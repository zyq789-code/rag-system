from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging import setup_logging
from core.exceptions import AppError, app_error_handler
from routers import health, documents, chat, knowledge, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    from loguru import logger
    logger.info("Starting RAG Knowledge Base System...")
    # 同步加载所有模型（启动慢一次，但后续请求秒回）
    import time
    from core.dependencies import get_embedding_service, get_reranker
    t0 = time.time()
    get_embedding_service()
    get_reranker()
    logger.info(f"Models loaded in {time.time()-t0:.1f}s, application ready")
    yield
    logger.info("Shutting down...")


settings = get_settings()
app = FastAPI(
    title="RAG Knowledge Base API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/knowledge-bases", tags=["knowledge"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
