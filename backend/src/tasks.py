

# from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
# from sqlmodel import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List
# from datetime import datetime, timezone
# from src.models import Task, TaskCreate, TaskUpdate, TaskRead
# from src.database import get_async_session
# import uuid

# # Router definition
# tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])

# # --- GET ALL TASKS ---
# @tasks_router.get("/", response_model=List[TaskRead])
# async def get_tasks(
#     user_id: str = Query(...), # Frontend se query param pakre ga (?user_id=...)
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Get all tasks for a specific user ID"""
#     try:
#         statement = select(Task).where(Task.user_id == user_id)
#         result = await session.execute(statement)
#         tasks = result.scalars().all()
#         return tasks
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

# # --- CREATE TASK ---
# @tasks_router.post("/", response_model=TaskRead)
# async def create_task(
#     task: TaskCreate, 
#     user_id: str = Query(...), # Frontend se user_id query param se lega
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Create a new task linked to the user_id"""
#     try:
#         db_task = Task(
#             title=task.title,
#             description=task.description,
#             user_id=user_id,
#             completed=False
#         )
#         session.add(db_task)
#         await session.commit()
#         await session.refresh(db_task)
#         return db_task
#     except Exception as e:
#         await session.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

# # --- GET SINGLE TASK ---
# @tasks_router.get("/{task_id}", response_model=TaskRead)
# async def get_task(
#     task_id: uuid.UUID, 
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Get a specific task by ID"""
#     task = await session.get(Task, task_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return task

# # --- UPDATE TASK ---
# @tasks_router.put("/{task_id}", response_model=TaskRead)
# async def update_task(
#     task_id: uuid.UUID, 
#     task_update: TaskUpdate, 
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Update task (title, description, or completed status)"""
#     db_task = await session.get(Task, task_id)
#     if not db_task:
#         raise HTTPException(status_code=404, detail="Task not found")

#     task_data = task_update.dict(exclude_unset=True)
#     for field, value in task_data.items():
#         setattr(db_task, field, value)

#     db_task.updated_at = datetime.now(timezone.utc)

#     session.add(db_task)
#     await session.commit()
#     await session.refresh(db_task)
#     return db_task

# # --- DELETE TASK ---
# @tasks_router.delete("/{task_id}")
# async def delete_task(
#     task_id: uuid.UUID, 
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Delete a specific task"""
#     task = await session.get(Task, task_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")

#     await session.delete(task)
#     await session.commit()
#     return {"message": "Task deleted successfully"}












from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import uuid
from src.models import Task, TaskCreate, TaskUpdate, TaskRead
from src.database import get_async_session

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])

@tasks_router.get("/", response_model=List[TaskRead])
async def get_tasks(
    user_id: str = Query(...),
    completed: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_async_session)
):
    print(f"🔍 [Backend] Fetching tasks for user_id: {user_id}, filter (completed): {completed}")

    statement = select(Task).where(Task.user_id == user_id)
    if completed is not None:
        statement = statement.where(Task.completed == completed)

    print(f"🚀 [Backend] Executing query: {statement}")
    result = await session.execute(statement)
    tasks = result.scalars().all()
    print(f"✅ [Backend] Found {len(tasks)} tasks")
    return tasks



@tasks_router.post("/", response_model=TaskRead)
async def create_task(task: TaskCreate, user_id: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    # FIX: .replace(tzinfo=None) added to prevent Postgres error
    db_task = Task(
        title=task.title,
        description=task.description,
        user_id=user_id,
        completed=False,
        created_at=datetime.now().replace(tzinfo=None),
        updated_at=datetime.now().replace(tzinfo=None)
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task


# Create task by user path
@tasks_router.post("/{user_id}/tasks", response_model=TaskRead)
async def create_task_by_user_path(task: TaskCreate, user_id: str, session: AsyncSession = Depends(get_async_session)):
    # FIX: .replace(tzinfo=None) added to prevent Postgres error
    db_task = Task(
        title=task.title,
        description=task.description,
        user_id=user_id,
        completed=False,
        created_at=datetime.now().replace(tzinfo=None),
        updated_at=datetime.now().replace(tzinfo=None)
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task

@tasks_router.put("/{task_id}", response_model=TaskRead)
async def update_task(task_id: uuid.UUID, task_update: TaskUpdate, user_id: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    db_task = await session.get(Task, task_id)
    if not db_task or str(db_task.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Unauthorized")

    task_data = task_update.dict(exclude_unset=True)
    for field, value in task_data.items():
        setattr(db_task, field, value)

    # FIX: .replace(tzinfo=None) added to prevent Postgres error
    db_task.updated_at = datetime.now().replace(tzinfo=None)

    await session.commit()
    await session.refresh(db_task)
    return db_task


# New endpoint to support the frontend's expected URL structure: /api/{user_id}/tasks/{task_id}
@tasks_router.put("/{user_id}/tasks/{task_id}", response_model=TaskRead)
async def update_task_by_user_path(task_id: uuid.UUID, user_id: str, task_update: TaskUpdate, session: AsyncSession = Depends(get_async_session)):
    db_task = await session.get(Task, task_id)
    if not db_task or str(db_task.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Unauthorized")

    task_data = task_update.dict(exclude_unset=True)
    for field, value in task_data.items():
        setattr(db_task, field, value)

    # FIX: .replace(tzinfo=None) added to prevent Postgres error
    db_task.updated_at = datetime.now().replace(tzinfo=None)

    await session.commit()
    await session.refresh(db_task)
    return db_task

@tasks_router.delete("/{task_id}")
async def delete_task(task_id: uuid.UUID, user_id: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    task = await session.get(Task, task_id)
    if not task or str(task.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Unauthorized")
    await session.delete(task)
    await session.commit()
    return {"message": "Deleted"}


# New endpoint to support the frontend's expected URL structure: /api/{user_id}/tasks/{task_id}
@tasks_router.delete("/{user_id}/tasks/{task_id}")
async def delete_task_by_user_path(task_id: uuid.UUID, user_id: str, session: AsyncSession = Depends(get_async_session)):
    task = await session.get(Task, task_id)
    if not task or str(task.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Unauthorized")
    await session.delete(task)
    await session.commit()
    return {"message": "Deleted"}


# Get single task by user path
@tasks_router.get("/{user_id}/tasks/{task_id}", response_model=TaskRead)
async def get_task_by_user_path(task_id: uuid.UUID, user_id: str, session: AsyncSession = Depends(get_async_session)):
    task = await session.get(Task, task_id)
    if not task or str(task.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Unauthorized")
    return task


