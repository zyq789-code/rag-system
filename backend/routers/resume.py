import uuid
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_llm_provider
from schemas.resume import ResumeResponse
from services.resume_service import ResumeService

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    service = ResumeService(session=db, llm=get_llm_provider())
    resume = await service.upload(file)
    return ResumeResponse.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = ResumeService(session=db, llm=get_llm_provider())
    resume = await service.get(resume_id)
    return ResumeResponse.model_validate(resume)


@router.post("/{resume_id}/interview")
async def generate_interview(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = ResumeService(session=db, llm=get_llm_provider())
    questions = await service.generate_interview_questions(resume_id)
    return {"questions": questions}
