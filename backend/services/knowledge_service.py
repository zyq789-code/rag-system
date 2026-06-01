import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_base import KnowledgeBase
from models.document import Document
from repositories.knowledge_base import KnowledgeBaseRepository
from repositories.document import DocumentRepository
from schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from core.exceptions import KnowledgeBaseNotFoundError
from core.dependencies import get_vector_store


class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.kb_repo = KnowledgeBaseRepository(session)
        self.doc_repo = DocumentRepository(session)

    async def create(self, data: KnowledgeBaseCreate) -> KnowledgeBaseResponse:
        kb = KnowledgeBase(name=data.name, description=data.description)
        created = await self.kb_repo.create(kb)
        return KnowledgeBaseResponse(
            id=created.id, name=created.name, description=created.description,
            document_count=0, created_at=created.created_at, updated_at=created.updated_at,
        )

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[KnowledgeBaseResponse]:
        kbs = await self.kb_repo.get_all(skip, limit)
        result = []
        for kb in kbs:
            count = await self.doc_repo.count_by_knowledge_base(kb.id)
            result.append(KnowledgeBaseResponse(
                id=kb.id, name=kb.name, description=kb.description,
                document_count=count, created_at=kb.created_at, updated_at=kb.updated_at,
            ))
        return result

    async def get(self, kb_id: uuid.UUID) -> KnowledgeBaseResponse:
        kb = await self.kb_repo.get_by_id(kb_id)
        if kb is None:
            raise KnowledgeBaseNotFoundError(str(kb_id))
        count = await self.doc_repo.count_by_knowledge_base(kb.id)
        return KnowledgeBaseResponse(
            id=kb.id, name=kb.name, description=kb.description,
            document_count=count, created_at=kb.created_at, updated_at=kb.updated_at,
        )

    async def update(self, kb_id: uuid.UUID, data: KnowledgeBaseUpdate) -> KnowledgeBaseResponse:
        kb = await self.kb_repo.get_by_id(kb_id)
        if kb is None:
            raise KnowledgeBaseNotFoundError(str(kb_id))
        if data.name is not None:
            kb.name = data.name
        if data.description is not None:
            kb.description = data.description
        await self.session.flush()
        await self.session.refresh(kb)
        count = await self.doc_repo.count_by_knowledge_base(kb.id)
        return KnowledgeBaseResponse(
            id=kb.id, name=kb.name, description=kb.description,
            document_count=count, created_at=kb.created_at, updated_at=kb.updated_at,
        )

    async def delete(self, kb_id: uuid.UUID) -> None:
        kb = await self.kb_repo.get_by_id(kb_id)
        if kb is None:
            raise KnowledgeBaseNotFoundError(str(kb_id))
        # 删除关联文档：从磁盘、ChromaDB、数据库
        docs = await self.doc_repo.get_by_knowledge_base(kb_id, 0, 10000)
        vector_store = get_vector_store()
        for doc in docs:
            try:
                await vector_store.delete_by_document(str(doc.id))
            except Exception:
                pass
            if doc.file_path and Path(doc.file_path).exists():
                Path(doc.file_path).unlink()
            await self.doc_repo.delete(doc)
        await self.kb_repo.delete(kb)
