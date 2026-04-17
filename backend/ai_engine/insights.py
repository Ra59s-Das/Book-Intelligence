"""
insights.py — generates AI insights for a book using Groq (free LLM).

Generates:
  1. Summary        — 2-3 sentence summary
  2. Genre          — predicted genre label
  3. Sentiment      — tone analysis with score
  4. Key themes     — list of 3-5 themes

Results are stored in AIInsight model (one per book, never regenerated = cached).
"""

import json
import logging
from .groq_client import call_llm
from books.models import Book, AIInsight

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a literary analyst. Analyze book descriptions and return structured JSON insights. "
    "Always respond with valid JSON only — no markdown, no explanation, no extra text."
)


def generate_insights_for_book(book: Book) -> AIInsight:
    """
    Generates AI insights for a Book and saves to DB.
    Skips if insights already exist (acts as cache — no repeated API calls).
    """
    # Already generated — skip API call entirely
    if hasattr(book, "ai_insight"):
        logger.info(f"Insights already cached for: {book.title}")
        return book.ai_insight

    description = book.description or book.title
    prompt = _build_prompt(book.title, book.genre, description)

    try:
        raw  = call_llm(prompt, system=SYSTEM_PROMPT, use_smart_model=False, max_tokens=512)
        data = _parse_response(raw)
    except Exception as e:
        logger.error(f"Insight generation failed for '{book.title}': {e}")
        data = _fallback_insights()

    insight = AIInsight.objects.create(
        book=book,
        summary=data.get("summary", ""),
        genre_prediction=data.get("genre", book.genre or ""),
        sentiment=data.get("sentiment", "neutral"),
        sentiment_score=float(data.get("sentiment_score", 0.5)),
        key_themes=data.get("key_themes", []),
        model_used="groq/llama-3.1-8b-instant",
    )

    book.is_processed = True
    book.save(update_fields=["is_processed"])

    logger.info(f"Insights generated for: {book.title}")
    return insight


def _build_prompt(title: str, genre: str, description: str) -> str:
    return f"""Analyze this book and respond with JSON only. No extra text, no markdown.

Title: {title}
Genre hint: {genre or "unknown"}
Description: {description[:800]}

Return exactly this JSON:
{{
  "summary": "2-3 sentences describing what this book is about",
  "genre": "one of: Fiction, Mystery, Romance, Science Fiction, Fantasy, Thriller, History, Self-Help, Biography, Children's, Poetry, Other",
  "sentiment": "one of: positive, negative, dark, hopeful, neutral, mixed",
  "sentiment_score": 0.75,
  "key_themes": ["theme1", "theme2", "theme3"]
}}"""


def _parse_response(raw: str) -> dict:
    """Parses JSON from LLM response. Handles markdown fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    return json.loads(cleaned)


def _fallback_insights() -> dict:
    return {
        "summary": "Summary not available.",
        "genre": "Unknown",
        "sentiment": "neutral",
        "sentiment_score": 0.5,
        "key_themes": [],
    }
