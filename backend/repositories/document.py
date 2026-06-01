import uuid
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession
from models.document import Document
from repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: Any):
        super().__init__(Document, session)

    async def get_by_knowledge_base(
        self, kb_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.knowledge_base_id == kb_id)
            .offset(skip)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self, doc_id: uuid.UUID, status: str, chunk_count: int = 0, error_message: str | None = None
    ) -> Document | None:
        doc = await self.get_by_id(doc_id)
        if doc is None:
            return None
        doc.status = status
        doc.chunk_count = chunk_count
        if error_message:
            doc.error_message = error_message
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    def get_by_id_sync(self, doc_id: uuid.UUID) -> Document | None:
        return self.session.get(Document, doc_id)

    def update_status_sync(
        self, doc_id: uuid.UUID, status: str, chunk_count: int = 0, error_message: str | None = None
    ) -> Document | None:
        doc = self.get_by_id_sync(doc_id)
        if doc is None:
            return None
        doc.status = status
        doc.chunk_count = chunk_count
        if error_message:
            doc.error_message = error_message
        self.session.flush()
        self.session.refresh(doc)
        return doc

    async def count_by_knowledge_base(self, kb_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(Document.id)).where(Document.knowledge_base_id == kb_id)
        )
        return result.scalar_one()
