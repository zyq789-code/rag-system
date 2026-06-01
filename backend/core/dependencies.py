from core.config import get_settings
from integrations.llm.factory import create_llm_provider
from integrations.embedding import EmbeddingService
from integrations.vector_store import VectorStore
from integrations.reranker import Reranker

_settings = get_settings()
_llm_provider = None
_embedding_service = None
_vector_store = None
_reranker = None


def get_llm_provider():
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = create_llm_provider(_settings)
    return _llm_provider


def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(_settings.embedding_model)
    return _embedding_service


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(_settings.chroma_host, _settings.chroma_port)
    return _vector_store


def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = Reranker(_settings.reranker_model)
    return _reranker
