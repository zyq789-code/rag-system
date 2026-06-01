import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_embedding_service, get_vector_store
from core.config import get_settings
from schemas.document import DocumentResponse, DocumentUploadResponse
from services.document_service import DocumentService
from services.chunking import Chunker
from integrations.document_parser import DocumentParser
from tasks.document_tasks import process_document

router = APIRouter()


def _get_doc_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    settings = get_settings()
    return DocumentService(
        session=db,
        parser=DocumentParser(),
        chunker=Chunker(settings.chunk_size, settings.chunk_overlap),
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        upload_dir=settings.upload_dir,
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    kb_id: uuid.UUID | None = Form(None),
    service: DocumentService = Depends(_get_doc_service),
):
    doc = await service.upload(file, kb_id)
    process_document.delay(str(doc.id))
    return DocumentUploadResponse(id=doc.id, filename=doc.filename, status=doc.status)


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: uuid.UUID | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    service: DocumentService = Depends(_get_doc_service),
):
    return await service.list_documents(kb_id, skip, limit)


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    service: DocumentService = Depends(_get_doc_service),
):
    return await service.get(doc_id)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    service: DocumentService = Depends(_get_doc_service),
):
    await service.delete(doc_id)
    return {"message": "Document deleted"}


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: uuid.UUID,
    service: DocumentService = Depends(_get_doc_service),
):
    """文档内容预览（DOCX/TXT/MD 提取文本，PDF 不支持）"""
    doc = await service.get(doc_id)
    if not doc.file_path or not Path(doc.file_path).exists():
        return {"content": "", "filename": doc.original_name, "file_type": doc.file_type}
    if doc.file_type == "pdf":
        return {"content": None, "filename": doc.original_name, "file_type": doc.file_type}
    from integrations.document_parser import DocumentParser
    parser = DocumentParser()
    text = parser.parse(doc.file_path, doc.file_type)
    return {"content": text[:10000], "filename": doc.original_name, "file_type": doc.file_type}


@router.get("/{doc_id}/file")
async def get_document_file(
    doc_id: uuid.UUID,
    service: DocumentService = Depends(_get_doc_service),
):
    """返回原始文件供浏览器预览或下载"""
    from fastapi.responses import FileResponse
    doc = await service.get(doc_id)
    if not doc.file_path or not Path(doc.file_path).exists():
        return {"error": "File not found"}
    media_types = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "txt": "text/plain", "md": "text/markdown", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    disposition = "inline" if doc.file_type == "pdf" else "attachment"
    return FileResponse(
        doc.file_path,
        media_type=media_types.get(doc.file_type, "application/octet-stream"),
        headers={"Content-Disposition": disposition},
    )


@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: uuid.UUID,
    service: DocumentService = Depends(_get_doc_service),
):
    doc = await service.get(doc_id)
    return {"id": doc.id, "status": doc.status, "chunk_count": doc.chunk_count}
