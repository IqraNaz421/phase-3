"""
Input Sanitization Utilities

Protects against prompt injection and malicious inputs
"""

import re
from typing import Optional


def sanitize_user_input(content: str, max_length: int = 5000) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Args:
        content: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized content

    Raises:
        ValueError: If input is empty or exceeds max length
    """
    if not content or not content.strip():
        raise ValueError("Input cannot be empty")

    # Trim whitespace
    content = content.strip()

    # Check length
    if len(content) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")

    # Remove control characters except newlines and tabs
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

    # Detect potential prompt injection patterns
    suspicious_patterns = [
        r'(?i)(ignore|disregard|forget)\s+(previous|above|all)',
        r'(?i)(system|assistant|user):\s*',
        r'(?i)new\s+instruction[s]?:',
        r'(?i)you\s+are\s+(now|currently)',
        r'(?i)pretend\s+(to\s+be|you\s+are)',
        r'(?i)(bypass|override)\s+(security|rules|instructions)',
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, content):
            # Log suspicious activity
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Potential prompt injection detected: {pattern}")

            # Replace suspicious pattern with safe placeholder
            content = re.sub(pattern, '[FILTERED]', content, flags=re.IGNORECASE)

    return content


def sanitize_title(title: str, max_length: int = 255) -> str:
    """
    Sanitize task title.

    Args:
        title: Raw title input
        max_length: Maximum allowed length

    Returns:
        Sanitized title
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")

    title = title.strip()

    if len(title) > max_length:
        raise ValueError(f"Title exceeds maximum length of {max_length} characters")

    # Remove control characters and newlines
    title = re.sub(r'[\x00-\x1F\x7F\n\r\t]', '', title)

    return title


def sanitize_description(description: Optional[str], max_length: int = 2000) -> str:
    """
    Sanitize task description.

    Args:
        description: Raw description input
        max_length: Maximum allowed length

    Returns:
        Sanitized description
    """
    if not description:
        return ""

    description = description.strip()

    if len(description) > max_length:
        raise ValueError(f"Description exceeds maximum length of {max_length} characters")

    # Remove control characters except newlines
    description = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', description)

    return description
