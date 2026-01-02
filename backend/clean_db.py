import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

# Aapki database URL jo .env mein hai
DATABASE_URL = os.getenv("DATABASE_URL")

async def clean():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Cleaning database tables...")
        await conn.execute(text('DROP TABLE IF EXISTS session CASCADE;'))
        await conn.execute(text('DROP TABLE IF EXISTS account CASCADE;'))
        await conn.execute(text('DROP TABLE IF EXISTS task CASCADE;'))
        await conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE;'))
        print("✅ Database cleaned successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean())