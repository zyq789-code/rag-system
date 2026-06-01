import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from services.knowledge_service import KnowledgeService

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_kb(data: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.create(data)


@router.get("/", response_model=list[KnowledgeBaseResponse])
async def list_kbs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.list_all(skip, limit)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.get(kb_id)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(kb_id: uuid.UUID, data: KnowledgeBaseUpdate, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    return await service.update(kb_id, data)


@router.delete("/{kb_id}")
async def delete_kb(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = KnowledgeService(db)
    await service.delete(kb_id)
    return {"message": "Knowledge base deleted"}
