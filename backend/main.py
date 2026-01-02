

# from fastapi import FastAPI, Depends, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from sqlmodel import SQLModel, select, func
# from sqlmodel.ext.asyncio.session import AsyncSession
# import ssl
# import os
# from dotenv import load_dotenv
# from sqlalchemy.ext.asyncio import create_async_engine
# from typing import List

# # 1. Load env
# load_dotenv()

# # --- Imports (Ensure models.py has Task class) ---
# try:
#     from src.auth import auth_router
#     from src.tasks import tasks_router
#     from src.models import Task 
# except ImportError as e:
#     print(f"❌ Import Error: {e}")

# # 2. Database Config
# DATABASE_URL = os.getenv("DATABASE_URL")

# # Clean URL for asyncpg
# if DATABASE_URL and "sslmode=" in DATABASE_URL:
#     DATABASE_URL = DATABASE_URL.split("?")[0]

# # SSL for Neon
# ctx = ssl.create_default_context()
# ctx.check_hostname = False
# ctx.verify_mode = ssl.CERT_NONE

# # Optimized Engine to prevent hanging
# async_engine = create_async_engine(
#     DATABASE_URL, 
#     echo=True,
#     pool_pre_ping=True,
#     pool_recycle=300,
#     connect_args={
#         "ssl": ctx,
#         "server_settings": {
#             "jit": "off",
#             "statement_timeout": "20000" # 20 seconds timeout
#         }
#     }
# )

# async def get_session() -> AsyncSession:
#     async with AsyncSession(async_engine) as session:
#         yield session

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("🚀 Connecting to Neon DB...")
#     try:
#         async with async_engine.begin() as conn:
#             await conn.run_sync(SQLModel.metadata.create_all)
#         print("✅ Database Ready!")
#     except Exception as e:
#         print(f"❌ Connection Failed: {e}")
#     yield
#     await async_engine.dispose()

# app = FastAPI(lifespan=lifespan)
# allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
# # 3. CORS Fix
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000", 
#         "http://localhost:8000",
#         "http://127.0.0.1:3000",
#         # "https://phase-2-blush.vercel.app"  # <--- Ye lazmi add karein
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # 4. FIXED DASHBOARD ENDPOINT
# @app.get("/api/tasks/stats")
# async def get_task_stats(user_id: str, session: AsyncSession = Depends(get_session)):
#     try:
#         # User ke tasks fetch karo
#         statement = select(Task).where(Task.user_id == user_id)
#         result = await session.execute(statement)
#         tasks = result.scalars().all()
        
#         total = len(tasks)
#         completed = len([t for t in tasks if t.completed])
#         pending = total - completed
        
#         efficiency = f"{(completed / total * 100) if total > 0 else 0:.0f}%"

#         # Graph ke liye data
#         return {
#             "totalTasks": total,
#             "completed": completed,
#             "pending": pending,
#             "efficiency": efficiency,
#             "weeklyStats": [
#                 {"name": "Mon", "tasks": total},
#                 {"name": "Tue", "tasks": 0},
#                 {"name": "Wed", "tasks": 0},
#                 {"name": "Thu", "tasks": completed},
#                 {"name": "Fri", "tasks": total},
#             ]
#         }
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return {"totalTasks": 0, "completed": 0, "pending": 0, "efficiency": "0%", "weeklyStats": []}

# app.include_router(auth_router, prefix="/api")
# app.include_router(tasks_router, prefix="/api")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)









from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import ssl
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from typing import List

# 1. Load env
load_dotenv()

# --- Imports ---
try:
    from src.auth import auth_router, get_current_user
    from src.tasks import tasks_router
    from src.models import Task
    from src.api.conversations import router as conversations_router
    from src.api.messages import router as messages_router
except ImportError as e:
    print(f"❌ Import Error: {e}")
    import sys
    sys.exit(1)  # Exit if imports fail

# 2. Database Config
DATABASE_URL = os.getenv("DATABASE_URL")

# Clean URL for asyncpg
if DATABASE_URL and "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# SSL for Neon
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Engine Setup
async_engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": ctx,
        "server_settings": {
            "jit": "off",
            "statement_timeout": "20000"
        }
    }
)

async def get_session() -> AsyncSession:
    async with AsyncSession(async_engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Connecting to Neon DB...")
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database Ready!")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
    yield
    await async_engine.dispose()

app = FastAPI(lifespan=lifespan)

# --- Rate Limiting Setup ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- 3. UPDATED CORS (For both Local & Vercel) ---
# Environment variable se origins uthayein (Hugging Face Secrets se)
env_origins = os.getenv("CORS_ORIGINS", "").split(",")
env_origins = [o.strip() for o in env_origins if o.strip()]

# In sab ko allow karna hai
final_origins = [
    "http://localhost:3000", 
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://phase-2-blush.vercel.app"
]

# Merge both lists and remove duplicates
final_origins = list(set(final_origins + env_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=final_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# --- 4. DASHBOARD ENDPOINT ---
@app.get("/api/tasks/stats")
async def get_task_stats(user_id: str, session: AsyncSession = Depends(get_session)):
    try:
        statement = select(Task).where(Task.user_id == user_id)
        result = await session.execute(statement)
        tasks = result.scalars().all()
        
        total = len(tasks)
        completed = len([t for t in tasks if t.completed])
        pending = total - completed
        efficiency = f"{(completed / total * 100) if total > 0 else 0:.0f}%"

        return {
            "totalTasks": total,
            "completed": completed,
            "pending": pending,
            "efficiency": efficiency,
            "weeklyStats": [
                {"name": "Mon", "tasks": total},
                {"name": "Tue", "tasks": 0},
                {"name": "Wed", "tasks": 0},
                {"name": "Thu", "tasks": completed},
                {"name": "Fri", "tasks": total},
            ]
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"totalTasks": 0, "completed": 0, "pending": 0, "efficiency": "0%", "weeklyStats": []}

app.include_router(auth_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(conversations_router)  # Prefix already in router
app.include_router(messages_router)  # Prefix already in router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)