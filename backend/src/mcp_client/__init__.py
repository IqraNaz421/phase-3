"""
MCP Client Package

Provides service token generation and MCP client functionality
for invoking MCP Server tools.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional


def generate_service_token(secret: Optional[str] = None) -> str:
    """
    Generate JWT token for MCP Server → Backend service-to-service communication.

    Args:
        secret: JWT secret (uses AUTH_SECRET env var if not provided)

    Returns:
        Encoded JWT token
    """
    if secret is None:
        secret = os.getenv("AUTH_SECRET")
        if not secret:
            raise ValueError("AUTH_SECRET environment variable is required")

    payload = {
        "sub": "mcp-server",
        "service": True,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }

    return jwt.encode(payload, secret, algorithm="HS256")


__all__ = ["generate_service_token"]
