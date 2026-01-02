"""
Message Model

Represents a single message within a conversation.
Enforces user isolation through user_id field.
"""

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from enum import Enum


class MessageRole(str, Enum):
    """Message role: user or assistant"""

    USER = "user"
    ASSISTANT = "assistant"


class Message(SQLModel, table=True):
    """
    Message entity for AI chatbot conversations.

    A message represents a single message in a conversation,
    sent either by the user or the AI assistant.
    """

    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        nullable=False, foreign_key="conversations.id", index=True
    )
    user_id: UUID = Field(nullable=False, index=True)  # User isolation
    role: str = Field(nullable=False, max_length=50)  # "user" or "assistant"
    content: str = Field(nullable=False)  # Message text
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": "987fcdeb-51a2-43d7-9012-345678901234",
                "user_id": "456e7890-abc1-23d4-5678-901234567890",
                "role": "user",
                "content": "Create a task to buy groceries",
                "created_at": "2025-12-31T00:00:00Z"
            }
        }
