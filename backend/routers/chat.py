import uuid
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, async_session_factory
from core.dependencies import get_llm_provider, get_embedding_service, get_vector_store, get_reranker, get_current_user
from core.config import get_settings
from core.exceptions import AppError
from schemas.chat import ChatRequest, ConversationResponse, MessageResponse
from services.rag_service import RAGService
from models.conversation import Conversation, Message
from models.user import User
from repositories.conversation import ConversationRepository

router = APIRouter()


def _get_rag_service() -> RAGService:
    settings = get_settings()
    return RAGService(
        llm=get_llm_provider(),
        embedding=get_embedding_service(),
        vector_store=get_vector_store(),
        reranker=get_reranker(),
        settings=settings,
    )


@router.post("/completions")
async def chat_completions(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    rag: RAGService = Depends(_get_rag_service),
    user: User = Depends(get_current_user),
):
    conv_repo = ConversationRepository(db)
    if request.conversation_id:
        conversation = await conv_repo.get_by_id(request.conversation_id)
        if not conversation:
            conversation = Conversation(title=request.message[:50], kb_id=request.kb_id, user_id=user.id)
            await conv_repo.create(conversation)
        elif conversation.user_id != user.id:
            raise AppError("无权访问该对话", status_code=403)
    else:
        conversation = Conversation(title=request.message[:50], kb_id=request.kb_id, user_id=user.id)
        await conv_repo.create(conversation)

    # 获取历史消息（不含当前问题）
    history = []
    if request.conversation_id:
        msgs = await conv_repo.get_messages(request.conversation_id)
        history = [{"role": m.role, "content": m.content} for m in msgs if m.content]

    user_msg = Message(conversation_id=conversation.id, role="user", content=request.message)
    await conv_repo.add_message(user_msg)

    async def generate():
        full_response = ""
        sources = None
        try:
            async for token, source_list in rag.chat_stream(
                request.message,
                str(request.kb_id) if request.kb_id else None,
                history,
            ):
                if token == "__sources__":
                    sources = source_list
                    yield f"data: {json.dumps({'sources': [s.model_dump() for s in sources]})}\n\n"
                else:
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except GeneratorExit:
            pass
        except Exception as e:
            from loguru import logger
            logger.error(f"Stream error: {e}")
            full_response = f"[错误: {e}]"
        finally:
            if full_response or sources:
                try:
                    async with async_session_factory() as save_session:
                        save_repo = ConversationRepository(save_session)
                        assistant_msg = Message(
                            conversation_id=conversation.id,
                            role="assistant",
                            content=full_response or "(空回复)",
                            sources=[s.model_dump() for s in sources] if sources else None,
                        )
                        await save_repo.add_message(assistant_msg)
                        await save_session.commit()
                except Exception as e:
                    from loguru import logger
                    logger.error(f"Failed to save assistant message: {e}")
            yield f"data: {json.dumps({'done': True, 'conversation_id': str(conversation.id)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv_repo = ConversationRepository(db)
    conversations = await conv_repo.get_all_for_user(user.id, skip, limit)
    result = []
    for conv in conversations:
        count = await conv_repo.get_message_count(conv.id)
        result.append(ConversationResponse(
            id=conv.id, title=conv.title, kb_id=conv.kb_id,
            created_at=conv.created_at, message_count=count,
        ))
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv_repo = ConversationRepository(db)
    conversation = await conv_repo.get_by_id(conversation_id)
    if conversation is None:
        raise AppError("对话不存在", status_code=404)
    if conversation.user_id != user.id:
        raise AppError("无权访问该对话", status_code=403)
    messages = await conv_repo.get_messages(conversation_id)
    return [MessageResponse.model_validate(m) for m in messages]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_by_id(conversation_id)
    if conv is None:
        raise AppError("对话不存在", status_code=404)
    if conv.user_id != user.id:
        raise AppError("无权访问该对话", status_code=403)
    await conv_repo.delete(conv)
    return {"message": "Deleted"}
