"""
User and Auth Models

Better Auth database tables and schemas.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel
from sqlalchemy import Column, String, ForeignKey


def get_utc_now_naive():
    """Helper function: Returns UTC time without timezone (Naive)"""
    return datetime.utcnow()


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


# Pydantic Schemas
class UserRead(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    createdAt: datetime


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    password: str
