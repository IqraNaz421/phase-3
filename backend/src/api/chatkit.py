"""
ChatKit API Router

Implements the ChatKit SDK API specification for thread management and messaging.
This endpoint is used by @openai/chatkit-react frontend components.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services.agent_service import get_agent_service
from src.services import conversation_service, message_service
from src.auth import get_current_user

router = APIRouter(prefix="/api/chatkit", tags=["ChatKit"])
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


class ChatKitSendMessageRequest(BaseModel):
    thread_id: Optional[str] = None
    text: str
    attachments: Optional[List[Dict[str, Any]]] = None
    new_thread: Optional[bool] = False


class ChatKitCreateThreadRequest(BaseModel):
    title: Optional[str] = None


@router.get("/health")
async def chatkit_health():
    return {"status": "ok", "service": "chatkit"}


@router.post("")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    body: ChatKitSendMessageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError) as e:
        logger.error(f"Auth error: {e}, current_user: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if not body.text or len(body.text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )

    conversation_id: Optional[UUID] = None
    if body.new_thread or not body.thread_id:
        title = body.text[:50] + "..." if len(body.text) > 50 else body.text
        conversation = await conversation_service.create_conversation(
            session, user_uuid, title
        )
        conversation_id = conversation.id
    else:
        conversation_id = UUID(body.thread_id)

    try:
        agent_service = get_agent_service()
    except ValueError as e:
        logger.error(f"Agent service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System configuration error. Please check backend settings."
        )

    async def generate():
        try:
            async for chunk in agent_service.invoke_agent(
                session, user_uuid, conversation_id, body.text.strip()
            ):
                yield f"0:{json.dumps({'role': 'assistant', 'content': chunk})}\n\n"
            yield f"2:{json.dumps({'done': True, 'thread_id': str(conversation_id)})}\n\n"
        except Exception as e:
            logger.error(f"ChatKit streaming error: {e}", exc_info=True)
            yield f"2:{json.dumps({'error': {'code': 'STREAMING_ERROR', 'message': str(e)}})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/threads")
async def list_threads(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError):
        return {"threads": [], "total": 0}

    conversations, total = await conversation_service.get_conversations_by_user(
        session, user_uuid, limit=100, offset=0
    )

    return {
        "threads": [
            {
                "id": str(conv.id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            }
            for conv in conversations
        ],
        "total": total,
    }


@router.get("/threads/{thread_id}")
async def get_thread(
    request: Request,
    thread_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        thread_uuid = UUID(thread_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thread ID format"
        )

    conversation = await conversation_service.get_conversation_by_id(
        session, thread_uuid, user_uuid
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    messages = await message_service.get_messages_by_conversation(
        session, thread_uuid, user_uuid, limit=limit, offset=offset
    )

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


@router.post("/threads")
async def create_thread(
    request: Request,
    body: Optional[ChatKitCreateThreadRequest] = None,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    title = body.title if body and body.title else "New Conversation"

    conversation = await conversation_service.create_conversation(
        session, user_uuid, title
    )

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
    }


@router.put("/threads/{thread_id}")
async def rename_thread(
    request: Request,
    thread_id: str,
    body: ChatKitCreateThreadRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        thread_uuid = UUID(thread_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thread ID format"
        )

    conversation = await conversation_service.update_conversation(
        session, thread_uuid, user_uuid, body.title
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
    }


@router.delete("/threads/{thread_id}")
async def delete_thread(
    request: Request,
    thread_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    try:
        token_user_id = str(current_user.get("sub") or current_user.get("id"))
        user_uuid = UUID(token_user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        thread_uuid = UUID(thread_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thread ID format"
        )

    deleted = await conversation_service.delete_conversation(
        session, thread_uuid, user_uuid
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    return {"success": True}
