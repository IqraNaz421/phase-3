"""
MCP Client

Client for invoking MCP Server tools from the backend.
Directly integrates with Task Service to perform actual database operations.
"""

import logging
from typing import Any, Dict, Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.task_service import TaskService
from src.models import TaskCreate, TaskUpdate
from src.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for invoking task management tools from the AI agent.

    This client directly integrates with the TaskService to perform
    actual database operations (create, list, update, delete, toggle tasks).
    """

    async def invoke_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke a task management tool.

        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments (must include user_id)

        Returns:
            Tool execution result with status, data, and metadata

        Raises:
            Exception: If tool invocation fails
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info(f"Invoking tool: {tool_name} with args: {arguments}")

                # Extract user_id (required for authorization)
                user_id = arguments.get("user_id")
                if not user_id:
                    raise ValueError("user_id is required for all tool operations")

                # Create task service with session
                task_service = TaskService(session)

                # Route to appropriate task service method
                if tool_name == "create_task":
                    return await self._create_task(task_service, user_id, arguments)

                elif tool_name == "list_tasks":
                    return await self._list_tasks(task_service, user_id, arguments)

                elif tool_name == "update_task":
                    return await self._update_task(task_service, user_id, arguments)

                elif tool_name == "delete_task":
                    return await self._delete_task(task_service, user_id, arguments)

                elif tool_name == "toggle_task_completion":
                    return await self._toggle_task_completion(task_service, user_id, arguments)

                else:
                    return {
                        "status": "error",
                        "error": {
                            "code": "UNKNOWN_TOOL",
                            "message": f"Unknown tool: {tool_name}",
                            "details": []
                        }
                    }

            except Exception as e:
                logger.error(f"Tool invocation failed: {e}", exc_info=True)
                return {
                    "status": "error",
                    "error": {
                        "code": "TOOL_INVOCATION_FAILED",
                        "message": str(e),
                        "details": []
                    }
                }

    async def _create_task(
        self,
        task_service: TaskService,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new task"""
        try:
            task = await task_service.create_task(
                user_id=user_id,
                title=arguments.get("title"),
                description=arguments.get("description")
            )

            return {
                "status": "success",
                "data": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "message": f"Task '{task.title}' created successfully"
                },
                "meta": {
                    "tool_name": "create_task",
                    "task_id": str(task.id)
                }
            }
        except Exception as e:
            logger.error(f"Create task failed: {e}", exc_info=True)
            raise

    async def _list_tasks(
        self,
        task_service: TaskService,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List tasks with optional filtering"""
        try:
            status_filter = arguments.get("status_filter", "all")
            tasks = await task_service.list_tasks(
                user_id=user_id,
                status_filter=status_filter
            )

            return {
                "status": "success",
                "data": {
                    "tasks": [
                        {
                            "id": str(task.id),
                            "title": task.title,
                            "description": task.description,
                            "completed": task.completed
                        }
                        for task in tasks
                    ],
                    "count": len(tasks),
                    "message": f"Found {len(tasks)} tasks"
                },
                "meta": {
                    "tool_name": "list_tasks",
                    "status_filter": status_filter
                }
            }
        except Exception as e:
            logger.error(f"List tasks failed: {e}", exc_info=True)
            raise

    async def _update_task(
        self,
        task_service: TaskService,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing task"""
        try:
            import uuid
            task_id = uuid.UUID(arguments.get("task_id"))
            updates_dict = arguments.get("updates", {})

            task_update = TaskUpdate(**updates_dict)
            task = await task_service.update_task(user_id, task_id, task_update)

            if not task:
                return {
                    "status": "error",
                    "error": {
                        "code": "TASK_NOT_FOUND",
                        "message": "Task not found or unauthorized",
                        "details": []
                    }
                }

            return {
                "status": "success",
                "data": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "message": f"Task '{task.title}' updated successfully"
                },
                "meta": {
                    "tool_name": "update_task",
                    "task_id": str(task.id)
                }
            }
        except Exception as e:
            logger.error(f"Update task failed: {e}", exc_info=True)
            raise

    async def _delete_task(
        self,
        task_service: TaskService,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete a task"""
        try:
            import uuid
            task_id = uuid.UUID(arguments.get("task_id"))
            deleted = await task_service.delete_task(user_id, task_id)

            if not deleted:
                return {
                    "status": "error",
                    "error": {
                        "code": "TASK_NOT_FOUND",
                        "message": "Task not found or unauthorized",
                        "details": []
                    }
                }

            return {
                "status": "success",
                "data": {
                    "message": "Task deleted successfully"
                },
                "meta": {
                    "tool_name": "delete_task",
                    "task_id": str(task_id)
                }
            }
        except Exception as e:
            logger.error(f"Delete task failed: {e}", exc_info=True)
            raise

    async def _toggle_task_completion(
        self,
        task_service: TaskService,
        user_id: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Toggle task completion status"""
        try:
            import uuid
            task_id = uuid.UUID(arguments.get("task_id"))
            task = await task_service.toggle_task_completion(user_id, task_id)

            if not task:
                return {
                    "status": "error",
                    "error": {
                        "code": "TASK_NOT_FOUND",
                        "message": "Task not found or unauthorized",
                        "details": []
                    }
                }

            status = "completed" if task.completed else "incomplete"
            return {
                "status": "success",
                "data": {
                    "id": str(task.id),
                    "title": task.title,
                    "completed": task.completed,
                    "message": f"Task '{task.title}' marked as {status}"
                },
                "meta": {
                    "tool_name": "toggle_task_completion",
                    "task_id": str(task.id),
                    "new_status": status
                }
            }
        except Exception as e:
            logger.error(f"Toggle task completion failed: {e}", exc_info=True)
            raise

    async def list_tools(self) -> list:
        """
        List available MCP tools.

        Returns:
            List of available tool names
        """
        return [
            "create_task_tool",
            "list_tasks_tool",
            "update_task_tool",
            "delete_task_tool",
            "toggle_task_completion_tool"
        ]


# Singleton instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create singleton MCP client"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
