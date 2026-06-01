from schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseResponse
from schemas.document import DocumentResponse
from schemas.chat import ChatRequest
from schemas.resume import ResumeAnalysisResult


def test_knowledge_base_create_valid():
    kb = KnowledgeBaseCreate(name="My KB", description="Test")
    assert kb.name == "My KB"


def test_knowledge_base_create_empty_name_fails():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        KnowledgeBaseCreate(name="")


def test_chat_request_valid():
    req = ChatRequest(message="Hello")
    assert req.message == "Hello"
    assert req.conversation_id is None


def test_resume_analysis_result():
    result = ResumeAnalysisResult(
        overall_score=85,
        summary="Strong candidate",
        skills=[{"name": "Python", "level": "expert", "years": 5}],
        strengths=["Strong coding"],
        gaps=["Limited cloud experience"],
        interview_questions=[{
            "question": "Explain RAG",
            "category": "technical",
            "difficulty": "medium",
            "expected_points": ["retrieval", "generation"]
        }]
    )
    assert result.overall_score == 85
