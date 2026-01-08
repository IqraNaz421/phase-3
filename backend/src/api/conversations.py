"""
Conversations API Router

Endpoints for conversation CRUD operations with user isolation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from src.database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services import conversation_service, message_service
from src.auth import get_current_user

router = APIRouter(prefix="/api/{user_id}/conversations", tags=["Conversations"])
logger = logging.getLogger(__name__)


# Request/Response Models
class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    initial_message: Optional[str] = None


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationsListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class UpdateConversationRequest(BaseModel):
    title: str


class StandardResponse(BaseModel):
    status: str
    data: Any
    meta: Dict[str, Any]


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    user_id: UUID,
    request: CreateConversationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Create a new conversation for the authenticated user"""
    # Verify user owns this resource
    # JWT token has 'sub' field, not 'id'
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    url_user_id = str(user_id)

    logger.info(f"Create conversation - Token user_id: {token_user_id}, URL user_id: {url_user_id}")

    if token_user_id != url_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied - user ID mismatch (token: {token_user_id}, url: {url_user_id})"
        )

    # Create conversation
    conversation = await conversation_service.create_conversation(
        session, user_id, request.title
    )

    return {
        "status": "success",
        "data": ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        ),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    }


@router.get("", response_model=StandardResponse)
async def list_conversations(
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """List all conversations for the authenticated user"""
    # Verify user owns this resource
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - user ID mismatch"
        )

    # Get conversations
    conversations, total = await conversation_service.get_conversations_by_user(
        session, user_id, limit, offset
    )

    return {
        "status": "success",
        "data": {
            "conversations": [
                ConversationResponse(
                    id=conv.id,
                    user_id=conv.user_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at
                )
                for conv in conversations
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    }


@router.get("/{conversation_id}", response_model=StandardResponse)
async def get_conversation(
    user_id: UUID,
    conversation_id: UUID,
    message_limit: int = 50,
    message_offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific conversation with its messages"""
    # Verify user owns this resource
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - user ID mismatch"
        )

    # Get conversation
    conversation = await conversation_service.get_conversation_by_id(
        session, conversation_id, user_id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get messages
    messages = await message_service.get_messages_by_conversation(
        session, conversation_id, user_id, message_limit, message_offset
    )

    return {
        "status": "success",
        "data": {
            "conversation": ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            ),
            "messages": [
                {
                    "id": str(msg.id),
                    "conversation_id": str(msg.conversation_id),
                    "user_id": str(msg.user_id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ],
            "message_count": len(messages)
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    }


@router.put("/{conversation_id}", response_model=StandardResponse)
async def update_conversation(
    user_id: UUID,
    conversation_id: UUID,
    request: UpdateConversationRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Update a conversation (rename title)"""
    # Verify user owns this resource
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - user ID mismatch"
        )

    # Update conversation
    conversation = await conversation_service.update_conversation(
        session, conversation_id, user_id, request.title
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return {
        "status": "success",
        "data": ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        ),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    }


@router.delete("/{conversation_id}", response_model=StandardResponse)
async def delete_conversation(
    user_id: UUID,
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation (cascade deletes messages)"""
    # Verify user owns this resource
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - user ID mismatch"
        )

    # Delete conversation
    deleted = await conversation_service.delete_conversation(
        session, conversation_id, user_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return {
        "status": "success",
        "data": {"message": "Conversation deleted successfully"},
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4())
        }
    }


# Need Any type for response data
from typing import Any
