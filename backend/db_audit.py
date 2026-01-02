
import asyncio
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, select, Session, SQLModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import ssl
from typing import Optional

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

class Task(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str
    title: str

async def audit_tasks():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"ssl": ctx}
    )

    async with AsyncSession(engine) as session:
        statement = select(Task)
        result = await session.execute(statement)
        tasks = result.scalars().all()

        print("\n--- DATABASE AUDIT ---")
        unique_user_ids = set()
        for task in tasks:
            print(f"Task: {task.title} | UserID: {task.user_id}")
            unique_user_ids.add(task.user_id)

        print("\nUnique User IDs in DB:")
        for uid in unique_user_ids:
            print(f"- {uid}")
        print("----------------------\n")

if __name__ == "__main__":
    asyncio.run(audit_tasks())
