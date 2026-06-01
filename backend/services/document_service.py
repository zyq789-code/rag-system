import uuid
import aiofiles
import aiofiles.os
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document
from repositories.document import DocumentRepository
from integrations.document_parser import DocumentParser
from services.chunking import Chunker
from integrations.embedding import EmbeddingService
from integrations.vector_store import VectorStore
from core.exceptions import DocumentNotFoundError, ProcessingError


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        parser: DocumentParser,
        chunker: Chunker,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        upload_dir: str = "./uploads",
    ):
        self.session = session
        self.repo = DocumentRepository(session)
        self.parser = parser
        self.chunker = chunker
        self.embedding = embedding_service
        self.vector_store = vector_store
        self.upload_dir = Path(upload_dir).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _is_allowed(self, filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def _get_file_type(self, filename: str) -> str:
        return filename.rsplit(".", 1)[1].lower()

    async def upload(self, file: UploadFile, kb_id: uuid.UUID | None = None) -> Document:
        if not file.filename or not self._is_allowed(file.filename):
            raise ProcessingError(f"File type not allowed: {file.filename}")

        file_type = self._get_file_type(file.filename)
        unique_name = f"{uuid.uuid4().hex}.{file_type}"
        file_path = self.upload_dir / unique_name

        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        doc = Document(
            knowledge_base_id=kb_id,
            filename=unique_name,
            original_name=file.filename,
            file_type=file_type,
            file_size=len(content),
            file_path=str(file_path.resolve()),
            status="pending",
        )
        await self.repo.create(doc)
        return doc

    async def get(self, doc_id: uuid.UUID) -> Document:
        doc = await self.repo.get_by_id(doc_id)
        if doc is None:
            raise DocumentNotFoundError(str(doc_id))
        return doc

    async def list_documents(
        self, kb_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[Document]:
        if kb_id:
            return await self.repo.get_by_knowledge_base(kb_id, skip, limit)
        return list(await self.repo.get_all(skip, limit))

    async def delete(self, doc_id: uuid.UUID) -> None:
        doc = await self.get(doc_id)
        await self.vector_store.delete_by_document(str(doc_id))
        if doc.file_path and Path(doc.file_path).exists():
            Path(doc.file_path).unlink()
        await self.repo.delete(doc)
