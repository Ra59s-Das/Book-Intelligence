"""
claude_client.py — thin wrapper around the Anthropic API.

All calls to Claude go through this file.
Model: claude-haiku-4-5-20251001 (fastest + cheapest, perfect for this use case)
"""

import logging
import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

# Single client instance shared across the app
_client = None


def get_client() -> anthropic.Anthropic:
    """Returns (or creates) the shared Anthropic client."""
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def call_claude(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """
    Makes a single call to Claude and returns the text response.

    Args:
        prompt:     The user message / question
        system:     Optional system prompt to set Claude's role
        max_tokens: Max response length (default 1024)

    Returns:
        The text content of Claude's response.
    """
    client = get_client()

    messages = [{"role": "user", "content": prompt}]

    kwargs = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    try:
        response = client.messages.create(**kwargs)
        return response.content[0].text.strip()
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise
