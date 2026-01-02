"""
Database Models

Exports all SQLModel entities for the application.
"""

# Phase 3: Conversation models
from .conversation import Conversation
from .message import Message, MessageRole

# Phase 2: Auth models
from .user import User, Session, Account, UserRead, UserCreate

# Phase 1: Task models
from .task import Task, TaskCreate, TaskUpdate, TaskRead

__all__ = [
    # Conversation models (Phase 3)
    "Conversation",
    "Message",
    "MessageRole",
    # Auth models (Phase 2)
    "User",
    "Session",
    "Account",
    "UserRead",
    "UserCreate",
    # Task models (Phase 1)
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskRead",
]
