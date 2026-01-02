from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel
from sqlalchemy import Column, String, ForeignKey

# Helper function: Ab ye baghair timezone (Naive) ke UTC time dega
def get_utc_now_naive():
    return datetime.utcnow()

# --- 1. BETTER AUTH DATABASE TABLES (SQLModel) ---

class User(SQLModel, table=True):
    """Better Auth User Table"""
    id: str = Field(
        sa_column=Column(
            String, 
            primary_key=True, 
            default=lambda: str(uuid.uuid4())
        )
    )
    email: str = Field(unique=True, index=True)
    password: str = Field() 
    name: Optional[str] = Field(default=None)
    emailVerified: bool = Field(default=False)
    image: Optional[str] = Field(default=None)
    # FIX: UTC Naive format (No offset-aware errors)
    createdAt: datetime = Field(default_factory=get_utc_now_naive)
    updatedAt: datetime = Field(default_factory=get_utc_now_naive)

class Session(SQLModel, table=True):
    """Better Auth Session Table"""
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    expiresAt: datetime
    token: str = Field(unique=True)
    createdAt: datetime = Field(default_factory=get_utc_now_naive)
    updatedAt: datetime = Field(default_factory=get_utc_now_naive)
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    userId: str = Field(sa_column=Column(String, ForeignKey("user.id"), nullable=False))

class Account(SQLModel, table=True):
    """Better Auth Account Table"""
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    accountId: str
    providerId: str
    userId: str = Field(sa_column=Column(String, ForeignKey("user.id"), nullable=False))
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None
    idToken: Optional[str] = None
    expiresAt: Optional[datetime] = None
    password: Optional[str] = None

# --- 2. TASK MODEL (Your Todo Logic) ---

class Task(SQLModel, table=True):
    """Task model representing a user's todo item"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    user_id: str = Field(sa_column=Column(String, index=True))
    # FIX: UTC Naive format
    created_at: datetime = Field(default_factory=get_utc_now_naive)
    updated_at: datetime = Field(default_factory=get_utc_now_naive)

# --- 3. PYDANTIC SCHEMAS ---

class UserRead(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    createdAt: datetime

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    password: str

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