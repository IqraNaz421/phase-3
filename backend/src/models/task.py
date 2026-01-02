"""
Task Models

Todo task database model and schemas.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel
from sqlalchemy import Column, String


def get_utc_now_naive():
    """Helper function: Returns UTC time without timezone (Naive)"""
    return datetime.utcnow()


class Task(SQLModel, table=True):
    """Task model representing a user's todo item"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    user_id: str = Field(sa_column=Column(String, index=True))
    created_at: datetime = Field(default_factory=get_utc_now_naive)
    updated_at: datetime = Field(default_factory=get_utc_now_naive)


# Pydantic Schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TaskRead(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    completed: bool
    user_id: str
