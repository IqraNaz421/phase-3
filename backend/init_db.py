"""Script to initialize the database schema."""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from src.database import async_engine
from src.models import User, Task
from sqlmodel import SQLModel

# Load environment variables from .env file
load_dotenv()


async def init_db():
    """Initialize the database schema."""
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    print("Database schema initialized successfully!")
    print("Tables created:")
    print("- users")
    print("- tasks")


if __name__ == "__main__":
    asyncio.run(init_db())