from fastapi import Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.exceptions import AppError
from core.security import decode_access_token
from integrations.llm.factory import create_llm_provider
from integrations.embedding import EmbeddingService
from integrations.vector_store import VectorStore
from integrations.reranker import Reranker
from models.user import User
from repositories.user import UserRepository

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


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Authorization: Bearer <token> 解析当前登录用户；未登录/失效则 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("未登录，请先登录", status_code=401)
    user_id = decode_access_token(authorization[7:])
    if user_id is None:
        raise AppError("登录已过期，请重新登录", status_code=401)
    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError("用户不存在", status_code=401)
    return user
