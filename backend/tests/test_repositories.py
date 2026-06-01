import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.database import Base
from models.document import Document
from models.knowledge_base import KnowledgeBase
from models.conversation import Conversation, Message
from models.resume import ResumeAnalysis
from repositories.document import DocumentRepository
from repositories.knowledge_base import KnowledgeBaseRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    def _create_tables(sync_conn):
        KnowledgeBase.__table__.create(sync_conn, checkfirst=True)
        Document.__table__.create(sync_conn, checkfirst=True)

    async with engine.begin() as conn:
        await conn.run_sync(_create_tables)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.mark.asyncio
async def test_create_and_get_document(session):
    repo = DocumentRepository(session)
    doc = Document(
        filename="test.pdf",
        original_name="test.pdf",
        file_type="pdf",
        file_size=1024,
        file_path="/uploads/test.pdf",
    )
    created = await repo.create(doc)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.filename == "test.pdf"


@pytest.mark.asyncio
async def test_update_document_status(session):
    repo = DocumentRepository(session)
    doc = Document(
        filename="test.pdf",
        original_name="test.pdf",
        file_type="pdf",
        file_size=1024,
        file_path="/uploads/test.pdf",
    )
    created = await repo.create(doc)
    updated = await repo.update_status(created.id, "completed", chunk_count=10)
    assert updated.status == "completed"
    assert updated.chunk_count == 10


@pytest.mark.asyncio
async def test_document_filter_by_kb(session):
    kb_repo = KnowledgeBaseRepository(session)
    kb = await kb_repo.create(KnowledgeBase(name="Test KB"))

    doc_repo = DocumentRepository(session)
    await doc_repo.create(Document(
        filename="a.pdf", original_name="a.pdf", file_type="pdf",
        file_size=100, file_path="/a.pdf", knowledge_base_id=kb.id,
    ))
    await doc_repo.create(Document(
        filename="b.pdf", original_name="b.pdf", file_type="pdf",
        file_size=200, file_path="/b.pdf",
    ))

    docs = await doc_repo.get_by_knowledge_base(kb.id)
    assert len(docs) == 1
    assert docs[0].filename == "a.pdf"
