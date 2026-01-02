"""
Agent Service

Handles OpenAI Agents SDK integration for conversational AI.
Implements stateless agent invocation pattern.
"""

import os
import logging
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from uuid import UUID
from openai import AsyncOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services import conversation_service, message_service
from src.models import MessageRole
from src.mcp_client.client import get_mcp_client

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for AI agent orchestration using OpenAI Agents SDK.

    This service is stateless - it loads conversation history from the database
    before each invocation and persists responses after completion.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Latest recommended conversational model
        self.mcp_client = get_mcp_client()

    def _get_system_instructions(self) -> str:
        """Get system instructions for task management assistant"""
        return """You are a helpful AI assistant for managing todo tasks. Your role is to help users:

1. Create tasks - Extract title and description from natural language
2. List tasks - Show tasks with optional filtering (all, completed, incomplete)
3. Update tasks - Modify task details based on user requests
4. Delete tasks - Remove tasks when requested
5. Toggle completion - Mark tasks as done or undone

TASK LIST DISPLAY (CRITICAL):
- When you successfully retrieve tasks using a tool, you MUST explicitly list them out for the user in your text response.
- Do not just confirm the tool was called.
- If the user asks for "all tasks", "sare tasks", or "everything", call list_tasks with status_filter="all". Do not restrict the search to just the current week unless specified.
- If there are no tasks, say: "You have no pending tasks for this week" or "Your task list is empty."
- Display tasks in a neat, organized format:
  ✓ Use checkmarks (✓) for completed tasks
  ✓ Use empty circles (○) for pending tasks
  ✓ Group tasks: "📋 Pending Tasks:" and "✅ Completed Tasks:"
  ✓ For each task, show: title, description (if any), and status
- Example format:
  📋 Pending Tasks:
  ○ Grocery shopping - Buy milk and eggs
  ○ Complete project report

  ✅ Completed Tasks:
  ✓ Buy shoes

TASK COMPLETION & CONFIRMATION:
- When user marks a task as complete, confirm with: "✓ Great! I've marked '[task title]' as completed."
- Always explicitly state the task title.

LANGUAGE SUPPORT (Hindi/Urdu Roman Script):
- Understand and respond in Roman Urdu/Hindi if the user uses it.
- Example: "Tasks dikhao" -> Show tasks. "Kaam ho gaya" -> Task completed.

IMPORTANT RULES:
- NEVER give a silent response like "Task operation completed: Success".
- ALWAYS be descriptive and list the results of the tool call.
- Provide a summary of what you did.
"""

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """
        Prepare OpenAI function calling tool definitions.

        Returns:
            List of tool definitions for OpenAI API
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Creates a new task for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title (required)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional task description including due dates or details"
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "Lists the user's tasks with optional filtering",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status_filter": {
                                "type": "string",
                                "enum": ["all", "completed", "incomplete"],
                                "description": "Filter tasks by completion status"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Updates an existing task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to update"
                            },
                            "updates": {
                                "type": "object",
                                "description": "Fields to update (title, description, completed)",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "completed": {"type": "boolean"}
                                }
                            }
                        },
                        "required": ["task_id", "updates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Deletes a task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to delete"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "toggle_task_completion",
                    "description": "Toggles task completion status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to toggle"
                            }
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

    async def _load_conversation_history(
        self, session: AsyncSession, conversation_id: UUID, user_id: UUID
    ) -> List[Dict[str, str]]:
        """
        Load conversation history from database (stateless requirement).

        Args:
            session: Database session
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            List of messages in OpenAI format
        """
        messages = await message_service.get_messages_by_conversation(
            session, conversation_id, user_id, limit=100
        )

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def invoke_agent(
        self,
        session: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Invoke AI agent with stateless pattern.
        """
        print(f"DEBUG: Agent is querying tasks for user: {user_id}")
        try:
            # Step 1: Load conversation history (stateless requirement)
            conversation_history = await self._load_conversation_history(
                session, conversation_id, user_id
            )

            # Step 2: Add user message to history
            conversation_history.append({"role": "user", "content": user_message})

            # Save user message to database
            await message_service.create_message(
                session, conversation_id, user_id, MessageRole.USER, user_message
            )

            # Step 3: Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self._get_system_instructions()}
            ] + conversation_history

            # Step 4: Invoke OpenAI with streaming and tools
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._prepare_tools(),
                stream=True,
                temperature=0.7
            )

            # Step 5: Stream response chunks
            full_response = ""
            tool_calls_accumulator = {}  # Accumulate tool call data across chunks

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta

                    # Handle content chunks
                    if delta.content:
                        content = delta.content
                        full_response += content
                        yield content

                    # Handle tool calls (streaming accumulation)
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            tool_call_id = tool_call.index

                            # Initialize accumulator for this tool call if needed
                            if tool_call_id not in tool_calls_accumulator:
                                tool_calls_accumulator[tool_call_id] = {
                                    "name": "",
                                    "arguments": ""
                                }

                            # Accumulate function name
                            if tool_call.function and tool_call.function.name:
                                tool_calls_accumulator[tool_call_id]["name"] = tool_call.function.name

                            # Accumulate function arguments (streamed in chunks)
                            if tool_call.function and tool_call.function.arguments:
                                tool_calls_accumulator[tool_call_id]["arguments"] += tool_call.function.arguments

            # Step 6: Process accumulated tool calls after streaming completes
            for tool_call_data in tool_calls_accumulator.values():
                tool_name = tool_call_data["name"]
                tool_args_str = tool_call_data["arguments"]

                try:
                    # Parse complete JSON arguments
                    tool_args = json.loads(tool_args_str) if tool_args_str else {}

                    # Add user_id to tool arguments
                    tool_args["user_id"] = str(user_id)

                    # Invoke MCP tool
                    logger.info(f"Invoking tool: {tool_name} with args: {tool_args}")
                    tool_result = await self.mcp_client.invoke_tool(tool_name, tool_args)

                    # Format tool result as a message to yield to user
                    if tool_name == "list_tasks":
                        # Format task list with proper display
                        # Handle both raw list (direct from API) or wrapped dict
                        tasks = []
                        if isinstance(tool_result, list):
                            tasks = tool_result
                        elif isinstance(tool_result, dict):
                            # Handle nested data structure: {"data": {"tasks": [...]}}
                            data = tool_result.get('data', {})
                            if isinstance(data, dict):
                                tasks = data.get('tasks', [])
                            else:
                                # Fallback for other dict structures
                                tasks = tool_result.get('tasks', tool_result.get('data', []))

                        if not isinstance(tasks, list):
                            tasks = []

                        print(f"DEBUG: Agent found {len(tasks)} tasks for user {user_id}")
                        if tasks:
                            pending_tasks = [task for task in tasks if not task.get('completed', False)]
                            completed_tasks = [task for task in tasks if task.get('completed', False)]

                            tool_response = "\n\n📋 Your Task List:\n"

                            if pending_tasks:
                                tool_response += "\n📋 Pending Tasks:\n"
                                for task in pending_tasks:
                                    title = task.get('title', 'Untitled')
                                    description = task.get('description', '')
                                    due_date = task.get('due_date', '')
                                    task_info = f"  ○ {title}"
                                    if description:
                                        task_info += f" - {description}"
                                    if due_date:
                                        # format due_date if it's longer
                                        try:
                                            d = str(due_date).split('T')[0]
                                            task_info += f" (Due: {d})"
                                        except:
                                            task_info += f" (Due: {due_date})"
                                    tool_response += task_info + "\n"

                            if completed_tasks:
                                tool_response += "\n✅ Completed Tasks:\n"
                                for task in completed_tasks:
                                    title = task.get('title', 'Untitled')
                                    description = task.get('description', '')
                                    task_info = f"  ✓ {title}"
                                    if description:
                                        task_info += f" - {description}"
                                    tool_response += task_info + "\n"

                            # Add Urdu/Hindi response closing
                            tool_response += "\nIs there anything else I can help you with? Kya main kisi aur cheez mein aapki madad kar sakta hoon?"
                        else:
                            tool_response = f"\n\nI found 0 tasks in the database for user: {user_id}. Aapka koi pending task nahi hai."
                    else:
                        # For other tools, find message in nested data
                        msg = "Success"
                        if isinstance(tool_result, dict):
                            data = tool_result.get('data', {})
                            if isinstance(data, dict):
                                msg = data.get('message', tool_result.get('message', 'Success'))
                            else:
                                msg = tool_result.get('message', 'Success')

                        if tool_name == "create_task":
                            title = tool_args.get('title', 'task')
                            tool_response = f"\n\n✓ Task created successfully: '{title}'. Naya task bana diya gaya hai."
                        elif tool_name == "toggle_task_completion":
                            tool_response = f"\n\n✓ {msg}! Task status update kar diya gaya hai."
                        elif tool_name == "delete_task":
                            tool_response = f"\n\n🗑️ {msg}! Task delete kar diya gaya hai."
                        else:
                            tool_response = f"\n\n✓ Operation completed: {msg}"

                    full_response += tool_response
                    yield tool_response

                    logger.info(f"Tool result: {tool_result}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments: {tool_args_str}, error: {e}")
                    error_msg = "\n\n⚠ Failed to process task operation due to malformed data."
                    full_response += error_msg
                    yield error_msg
                except Exception as e:
                    logger.error(f"Tool invocation failed: {e}", exc_info=True)
                    error_msg = f"\n\n⚠ Task operation failed: {str(e)}"
                    full_response += error_msg
                    yield error_msg

            # Step 7: Persist assistant response to database (stateless requirement)
            if full_response:
                await message_service.create_message(
                    session, conversation_id, user_id, MessageRole.ASSISTANT, full_response
                )

        except Exception as e:
            logger.error(f"Agent invocation failed: {e}", exc_info=True)
            error_message = f"I apologize, but I encountered an error: {str(e)}"
            yield error_message

            # Persist error message
            try:
                await message_service.create_message(
                    session, conversation_id, user_id, MessageRole.ASSISTANT, error_message
                )
            except Exception as persist_error:
                logger.error(f"Failed to persist error message: {persist_error}")


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create singleton agent service"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
