import pytest
import pytest_asyncio
import uuid
from sqlalchemy import types
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from models.document import Document
from models.knowledge_base import KnowledgeBase
from models.conversation import Conversation, Message
from models.resume import ResumeAnalysis
from core.database import Base


# Override PostgreSQL-specific types for SQLite testing
@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_knowledge_base(db_session):
    kb = KnowledgeBase(name="Test KB", description="A test knowledge base")
    db_session.add(kb)
    await db_session.commit()
    await db_session.refresh(kb)
    assert kb.id is not None
    assert kb.name == "Test KB"
    assert kb.created_at is not None


@pytest.mark.asyncio
async def test_create_document_with_kb(db_session):
    kb = KnowledgeBase(name="Test KB")
    db_session.add(kb)
    await db_session.commit()
    await db_session.refresh(kb)

    doc = Document(
        knowledge_base_id=kb.id,
        filename="abc123.pdf",
        original_name="report.pdf",
        file_type="pdf",
        file_size=1024,
        file_path="/uploads/abc123.pdf",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    assert doc.id is not None
    assert doc.status == "pending"
    assert doc.knowledge_base_id == kb.id


@pytest.mark.asyncio
async def test_create_conversation_with_messages(db_session):
    conv = Conversation(title="Test Chat")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    msg = Message(
        conversation_id=conv.id,
        role="user",
        content="Hello",
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    assert msg.id is not None
    assert msg.role == "user"


@pytest.mark.asyncio
async def test_create_resume_analysis(db_session):
    resume = ResumeAnalysis(
        filename="resume.pdf",
        file_path="/uploads/resume.pdf",
        status="pending",
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    assert resume.id is not None
    assert resume.status == "pending"
