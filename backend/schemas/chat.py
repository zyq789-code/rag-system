import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: uuid.UUID | None = None
    kb_id: uuid.UUID | None = None


class SourceCitation(BaseModel):
    filename: str
    chunk_text: str
    score: float


class ChatResponse(BaseModel):
    message: str
    sources: list[SourceCitation] = []
    conversation_id: uuid.UUID


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    kb_id: uuid.UUID | None
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[dict] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
