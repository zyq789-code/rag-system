from sqlalchemy.ext.asyncio import AsyncSession
from models.resume import ResumeAnalysis
from repositories.base import BaseRepository


class ResumeRepository(BaseRepository[ResumeAnalysis]):
    def __init__(self, session: AsyncSession):
        super().__init__(ResumeAnalysis, session)
