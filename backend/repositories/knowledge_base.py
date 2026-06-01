from sqlalchemy.ext.asyncio import AsyncSession
from models.knowledge_base import KnowledgeBase
from repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeBase, session)
