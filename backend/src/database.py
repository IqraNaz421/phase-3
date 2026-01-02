import ssl
from sqlmodel import create_engine, Session
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable - no default to ensure Neon DB is used
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create SSL context for Neon PostgreSQL
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Create async engine for Neon PostgreSQL with SSL context
# Remove any query parameters from the URL to avoid conflicts with asyncpg
async_engine = create_async_engine(
    DATABASE_URL.split('?')[0],  # This removes any ?sslmode from URL
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,  # Base number of connections
    max_overflow=10,  # Max additional connections beyond pool_size
    pool_recycle=300,  # Recycle connections after 5 minutes
    connect_args={'ssl': ctx}
)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get async session
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Alias for consistency across the codebase
get_session = get_async_session