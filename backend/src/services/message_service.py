"""
Message Service

Handles operations for messages with user isolation enforcement.
"""

from typing import List
from uuid import UUID
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Message, MessageRole


async def create_message(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    role: str,
    content: str
) -> Message:
    """
    Create a new message in a conversation.

    Args:
        session: Database session
        conversation_id: Parent conversation ID
        user_id: User ID (for isolation)
        role: Message role ('user' or 'assistant')
        content: Message content

    Returns:
        Created message

    Raises:
        ValueError: If content is empty or role is invalid
    """
    if not content or len(content.strip()) == 0:
        raise ValueError("Message content cannot be empty")

    if role not in [MessageRole.USER, MessageRole.ASSISTANT]:
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

    message = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
        created_at=datetime.utcnow()
    )

    session.add(message)
    await session.commit()
    await session.refresh(message)

    return message


async def get_messages_by_conversation(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> List[Message]:
    """
    Get messages for a conversation with user isolation and pagination.

    Args:
        session: Database session
        conversation_id: Conversation ID
        user_id: User ID (for isolation)
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        List of messages in chronological order
    """
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.user_id == user_id)  # CRITICAL: User isolation
        .order_by(Message.created_at.asc())  # Chronological order
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_message_count(
    session: AsyncSession, conversation_id: UUID, user_id: UUID
) -> int:
    """
    Get total message count for a conversation.

    Args:
        session: Database session
        conversation_id: Conversation ID
        user_id: User ID (for isolation)

    Returns:
        Total number of messages
    """
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.user_id == user_id)  # CRITICAL: User isolation
    )
    return len(result.scalars().all())
