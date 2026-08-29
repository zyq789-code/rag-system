import pytest
from unittest.mock import AsyncMock, MagicMock
from services.rag_service import RAGService
from services import bm25


@pytest.fixture
def rag_service():
    bm25.clear()
    vector_store = AsyncMock()
    vector_store.texts_revision = 0
    vector_store.get_all_texts.return_value = []
    return RAGService(
        llm=AsyncMock(),
        embedding=AsyncMock(),
        vector_store=vector_store,
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
    rag_service.vector_store.get_all_texts.return_value = [
        {"id": "chunk1", "text": "RAG 是检索增强生成技术，用于知识库问答。", "metadata": {"filename": "a.pdf", "document_id": "doc1"}},
        {"id": "chunk2", "text": "向量数据库存储文档的语义向量。", "metadata": {"filename": "b.pdf", "document_id": "doc2"}},
    ]
    rag_service.reranker.rerank.return_value = [{"text": "Test", "metadata": {"filename": "a.pdf"}, "rerank_score": 0.9}]
    results = await rag_service.search("什么是检索增强生成")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_bm25_search_ranks_relevant_chunk_first(rag_service):
    """BM25（jieba 分词）应把命中间的关键词 chunk 排前面。"""
    rag_service.vector_store.get_all_texts.return_value = [
        {"id": "c1", "text": "RAG 是检索增强生成技术，用于知识库问答。", "metadata": {"filename": "a.pdf", "document_id": "doc1"}},
        {"id": "c2", "text": "向量数据库存储文档的语义向量。", "metadata": {"filename": "b.pdf", "document_id": "doc2"}},
        {"id": "c3", "text": "欢迎来到系统，这里是说明文档。", "metadata": {"filename": "c.pdf", "document_id": "doc3"}},
    ]
    results = await rag_service._bm25_search("什么是检索增强生成", None)
    assert results and results[0]["id"] == "c1"


@pytest.mark.asyncio
async def test_bm25_search_empty_corpus_returns_empty(rag_service):
    rag_service.vector_store.get_all_texts.return_value = []
    assert await rag_service._bm25_search("你好", None) == []
