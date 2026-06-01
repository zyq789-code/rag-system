from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class DocumentNotFoundError(AppError):
    def __init__(self, doc_id: str):
        super().__init__(f"Document {doc_id} not found", 404)


class ProcessingError(AppError):
    def __init__(self, detail: str):
        super().__init__(f"Processing error: {detail}", 500)


class KnowledgeBaseNotFoundError(AppError):
    def __init__(self, kb_id: str):
        super().__init__(f"Knowledge base {kb_id} not found", 404)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
