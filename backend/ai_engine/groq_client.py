"""
groq_client.py — Groq API wrapper (FREE, no credit card needed).

Sign up at https://console.groq.com to get your free API key.

Models used:
  - llama-3.1-8b-instant   : fast, for AI insights (summary/genre/sentiment)
  - llama-3.3-70b-versatile: smarter, for RAG Q&A answers

Free tier limits (as of 2025):
  - 14,400 requests/day
  - 500,000 tokens/minute
  Plenty for this project.
"""

import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None

# Model choices — both are FREE on Groq
FAST_MODEL  = "llama-3.1-8b-instant"      # used for insights (speed matters)
SMART_MODEL = "llama-3.3-70b-versatile"   # used for Q&A (quality matters)


def get_client() -> Groq:
    """Returns (or creates) the shared Groq client."""
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set.\n"
                "1. Go to https://console.groq.com\n"
                "2. Sign up free → API Keys → Create Key\n"
                "3. Paste it in backend/.env as GROQ_API_KEY=gsk_..."
            )
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def call_llm(prompt: str, system: str = "", use_smart_model: bool = False, max_tokens: int = 1024) -> str:
    """
    Calls Groq LLM and returns the text response.

    Args:
        prompt          : The user message
        system          : System prompt (sets the AI's role/behaviour)
        use_smart_model : True = 70b model (Q&A), False = 8b model (insights)
        max_tokens      : Max response length

    Returns:
        Plain text response string.
    """
    client = get_client()
    model  = SMART_MODEL if use_smart_model else FAST_MODEL

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,   # low temperature = more consistent, factual answers
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error (model={model}): {e}")
        raise
