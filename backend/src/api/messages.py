"""
Messages API Router

Endpoints for sending messages and receiving streaming AI responses.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.services.agent_service import get_agent_service
from src.auth import get_current_user
from src.utils import sanitize_user_input

router = APIRouter(prefix="/api/{user_id}/conversations/{conversation_id}/messages", tags=["Messages"])
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


# Request Model
class SendMessageRequest(BaseModel):
    content: str


@router.post("")
@limiter.limit("20/minute")  # Rate limit: 20 messages per minute per IP
async def send_message(
    request: Request,
    user_id: UUID,
    conversation_id: UUID,
    message_request: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message to the AI agent and receive streaming response via SSE.

    This endpoint uses Server-Sent Events to stream the AI's response in real-time.
    """
    # Verify user owns this resource
    token_user_id = str(current_user.get("sub") or current_user.get("id"))
    if token_user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - user ID mismatch"
        )

    # Validate message content
    if not message_request.content or len(message_request.content.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )

    # Sanitize input to prevent prompt injection
    sanitized_content = sanitize_user_input(message_request.content)

    # Get agent service
    agent_service = get_agent_service()

    # Stream AI response
    async def stream_response():
        """Generate SSE stream from AI agent"""
        try:
            async for chunk in agent_service.invoke_agent(
                session, user_id, conversation_id, sanitized_content
            ):
                # SSE format: data: {json}\n\n
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            # Send error event
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        }
    )


