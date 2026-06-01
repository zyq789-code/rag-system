from tasks.celery_app import celery_app
from core.config import get_settings
from core.database import SyncSession
from repositories.document import DocumentRepository
from integrations.document_parser import DocumentParser
from services.chunking import Chunker
from integrations.embedding import EmbeddingService
from integrations.vector_store import VectorStore
from loguru import logger


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    import uuid
    settings = get_settings()
    parser = DocumentParser()
    chunker = Chunker(settings.chunk_size, settings.chunk_overlap)
    embedding_service = EmbeddingService(settings.embedding_model)
    vector_store = VectorStore(settings.chroma_host, settings.chroma_port)

    session = SyncSession()
    try:
        repo = DocumentRepository(session)
        doc = repo.get_by_id_sync(uuid.UUID(document_id))
        if not doc or not doc.file_path:
            session.close()
            return

        repo.update_status_sync(uuid.UUID(document_id), "processing")
        session.commit()

        text = parser.parse(doc.file_path, doc.file_type)
        meta = {
            "document_id": document_id,
            "filename": doc.original_name,
        }
        if doc.knowledge_base_id:
            meta["knowledge_base_id"] = str(doc.knowledge_base_id)
        chunks = chunker.chunk_with_metadata(text, meta)

        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts_sync(chunk_texts)

        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [c["metadata"] for c in chunks]

        vector_store._add_sync(
            ids=ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        repo.update_status_sync(uuid.UUID(document_id), "completed", chunk_count=len(chunks))
        session.commit()
        logger.info(f"Document {document_id} processed: {len(chunks)} chunks")
    except Exception as exc:
        session.rollback()
        logger.error(f"Document processing failed for {document_id}: {exc}")
        _mark_failed_sync(document_id, str(exc))
        session.close()
        raise self.retry(exc=exc, countdown=60)
    session.close()


def _mark_failed_sync(document_id: str, error: str):
    import uuid
    session = SyncSession()
    try:
        from repositories.document import DocumentRepository
        repo = DocumentRepository(session)
        repo.update_status_sync(uuid.UUID(document_id), "failed", error_message=error)
        session.commit()
    finally:
        session.close()
