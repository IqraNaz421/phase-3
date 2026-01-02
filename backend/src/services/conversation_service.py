"""
Conversation Service

Handles CRUD operations for conversations with user isolation enforcement.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import Conversation


async def create_conversation(
    session: AsyncSession, user_id: UUID, title: Optional[str] = None
) -> Conversation:
    """
    Create a new conversation for a user.

    Args:
        session: Database session
        user_id: User ID (for isolation)
        title: Optional conversation title

    Returns:
        Created conversation

    Raises:
        ValueError: If title is empty
    """
    if title and len(title.strip()) == 0:
        raise ValueError("Conversation title cannot be empty")

    conversation = Conversation(
        user_id=user_id,
        title=title or "New Conversation"
    )

    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return conversation


async def get_conversation_by_id(
    session: AsyncSession, conversation_id: UUID, user_id: UUID
) -> Optional[Conversation]:
    """
    Get a conversation by ID with user isolation.

    Args:
        session: Database session
        conversation_id: Conversation ID
        user_id: User ID (for isolation)

    Returns:
        Conversation if found and belongs to user, None otherwise
    """
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)  # CRITICAL: User isolation
    )
    return result.scalar_one_or_none()


async def get_conversations_by_user(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Conversation], int]:
    """
    Get all conversations for a user with pagination.

    Args:
        session: Database session
        user_id: User ID (for isolation)
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip

    Returns:
        Tuple of (conversations list, total count)
    """
    # Get conversations
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)  # CRITICAL: User isolation
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()

    # Get total count
    count_result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
    )
    total = len(count_result.scalars().all())

    return list(conversations), total


async def update_conversation(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    title: Optional[str] = None
) -> Optional[Conversation]:
    """
    Update a conversation.

    Args:
        session: Database session
        conversation_id: Conversation ID
        user_id: User ID (for isolation)
        title: Optional new title

    Returns:
        Updated conversation if found and belongs to user, None otherwise
    """
    # Get conversation with user isolation
    conversation = await get_conversation_by_id(session, conversation_id, user_id)

    if not conversation:
        return None

    # Update fields
    if title:
        conversation.title = title
    conversation.updated_at = datetime.utcnow()

    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return conversation


async def delete_conversation(
    session: AsyncSession, conversation_id: UUID, user_id: UUID
) -> bool:
    """
    Delete a conversation (cascade deletes messages).

    Args:
        session: Database session
        conversation_id: Conversation ID
        user_id: User ID (for isolation)

    Returns:
        True if deleted, False if not found or access denied
    """
    # Get conversation with user isolation
    conversation = await get_conversation_by_id(session, conversation_id, user_id)

    if not conversation:
        return False

    await session.delete(conversation)
    await session.commit()

    return True
