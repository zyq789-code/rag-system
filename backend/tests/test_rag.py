import pytest
from unittest.mock import AsyncMock, MagicMock
from services.rag_service import RAGService


@pytest.fixture
def rag_service():
    return RAGService(
        llm=AsyncMock(),
        embedding=AsyncMock(),
        vector_store=AsyncMock(),
        reranker=AsyncMock(),
        settings=MagicMock(top_k_vector=20, top_k_bm25=20, top_k_rerank=5, chunk_size=512),
    )


def test_build_prompt(rag_service):
    prompt = rag_service._build_prompt(
        question="What is RAG?",
        contexts=[
            {"text": "RAG stands for Retrieval-Augmented Generation.", "metadata": {"filename": "intro.pdf"}, "score": 0.9},
        ],
    )
    assert "What is RAG?" in prompt
    assert "Retrieval-Augmented Generation" in prompt


def test_build_prompt_empty_context(rag_service):
    prompt = rag_service._build_prompt(question="Hello", contexts=[])
    assert "Hello" in prompt
    assert "没有找到相关文档" in prompt


@pytest.mark.asyncio
async def test_search(rag_service):
    rag_service.embedding.embed_query.return_value = [0.1] * 512
    rag_service.vector_store.query.return_value = {
        "ids": ["chunk1"],
        "documents": ["Test document content"],
        "metadatas": [{"filename": "test.pdf", "document_id": "doc1"}],
        "distances": [0.1],
    }
    rag_service.reranker.rerank.return_value = [{"text": "Test", "metadata": {"filename": "test.pdf"}, "rerank_score": 0.9}]
    results = await rag_service.search("test query")
    assert len(results) > 0
