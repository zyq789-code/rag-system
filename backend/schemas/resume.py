import uuid
from datetime import datetime
from pydantic import BaseModel


class SkillAssessment(BaseModel):
    name: str
    level: str
    years: int | None = None


class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str
    expected_points: list[str]


class ResumeAnalysisResult(BaseModel):
    overall_score: int
    summary: str
    skills: list[SkillAssessment]
    strengths: list[str]
    gaps: list[str]
    interview_questions: list[InterviewQuestion]


class ResumeResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    analysis_result: ResumeAnalysisResult | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
