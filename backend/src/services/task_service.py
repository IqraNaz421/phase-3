"""
Task Service

Service for managing tasks - provides direct access to task CRUD operations.
Used by the AI agent to create/manipulate tasks through the MCP client.
"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.models import Task, TaskCreate, TaskUpdate
from src.database import get_session

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for task management operations.

    This service provides methods to create, read, update, and delete tasks
    directly without going through HTTP endpoints. It's used by the AI agent
    to perform task operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        completed: bool = False
    ) -> Task:
        """
        Create a new task.

        Args:
            user_id: User ID who owns the task
            title: Task title
            description: Optional task description
            completed: Task completion status (default False)

        Returns:
            Created task object
        """
        try:
            task = Task(
                title=title,
                description=description,
                user_id=user_id,
                completed=completed,
                created_at=datetime.now().replace(tzinfo=None),
                updated_at=datetime.now().replace(tzinfo=None)
            )
            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Created task: {task.id} for user: {user_id}")
            return task

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise

    async def list_tasks(
        self,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[Task]:
        """
        List tasks for a user.

        Args:
            user_id: User ID
            status_filter: Optional filter ('all', 'completed', 'incomplete')

        Returns:
            List of tasks
        """
        try:
            statement = select(Task).where(Task.user_id == user_id)

            if status_filter == 'completed':
                statement = statement.where(Task.completed == True)
            elif status_filter == 'incomplete':
                statement = statement.where(Task.completed == False)

            result = await self.session.execute(statement)
            tasks = result.scalars().all()

            logger.info(f"Listed {len(tasks)} tasks for user: {user_id} (filter: {status_filter})")
            return tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}", exc_info=True)
            raise

    async def get_task(self, user_id: str, task_id: UUID) -> Optional[Task]:
        """
        Get a specific task by ID.

        Args:
            user_id: User ID for authorization
            task_id: Task ID

        Returns:
            Task object or None if not found
        """
        try:
            task = await self.session.get(Task, task_id)

            # Verify user ownership
            if task and str(task.user_id) != user_id:
                logger.warning(f"Unauthorized access to task {task_id} by user {user_id}")
                return None

            return task

        except Exception as e:
            logger.error(f"Failed to get task: {e}", exc_info=True)
            raise

    async def update_task(
        self,
        user_id: str,
        task_id: UUID,
        updates: TaskUpdate
    ) -> Optional[Task]:
        """
        Update an existing task.

        Args:
            user_id: User ID for authorization
            task_id: Task ID
            updates: Fields to update

        Returns:
            Updated task or None if not found/unauthorized
        """
        try:
            task = await self.get_task(user_id, task_id)

            if not task:
                logger.warning(f"Task {task_id} not found for user {user_id}")
                return None

            # Update fields
            task_data = updates.dict(exclude_unset=True)
            for field, value in task_data.items():
                setattr(task, field, value)

            task.updated_at = datetime.now().replace(tzinfo=None)

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Updated task: {task_id} for user: {user_id}")
            return task

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update task: {e}", exc_info=True)
            raise

    async def delete_task(self, user_id: str, task_id: UUID) -> bool:
        """
        Delete a task.

        Args:
            user_id: User ID for authorization
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        try:
            task = await self.get_task(user_id, task_id)

            if not task:
                logger.warning(f"Task {task_id} not found for user {user_id}")
                return False

            await self.session.delete(task)
            await self.session.commit()

            logger.info(f"Deleted task: {task_id} for user: {user_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete task: {e}", exc_info=True)
            raise

    async def toggle_task_completion(self, user_id: str, task_id: UUID) -> Optional[Task]:
        """
        Toggle task completion status.

        Args:
            user_id: User ID for authorization
            task_id: Task ID

        Returns:
            Updated task or None if not found
        """
        try:
            task = await self.get_task(user_id, task_id)

            if not task:
                return None

            task.completed = not task.completed
            task.updated_at = datetime.now().replace(tzinfo=None)

            self.session.add(task)
            await self.session.commit()
            await self.session.refresh(task)

            logger.info(f"Toggled task {task_id} to {'completed' if task.completed else 'incomplete'}")
            return task

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to toggle task: {e}", exc_info=True)
            raise
