"""
Conversation Model

Represents a chat thread between a user and the AI assistant.
Enforces user isolation through user_id field.
"""

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .message import Message


class Conversation(SQLModel, table=True):
    """
    Conversation entity for AI chatbot.

    A conversation is a chat thread containing multiple messages
    between a user and the AI assistant.
    """

    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(nullable=False, index=True)  # User isolation
    title: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship to messages
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43d7-9012-345678901234",
                "title": "Task Planning Discussion",
                "created_at": "2025-12-31T00:00:00Z",
                "updated_at": "2025-12-31T01:00:00Z"
            }
        }
