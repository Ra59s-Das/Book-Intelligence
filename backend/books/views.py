"""
API Views — all 5 required endpoints plus chat history.

GET  /api/books/                → list all books
GET  /api/books/<id>/           → book detail + AI insights
GET  /api/books/<id>/recommend/ → similar books
POST /api/books/upload/         → scrape + process books
POST /api/books/ask/            → RAG Q&A
GET  /api/books/history/        → saved chat history
"""

import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Book, AIInsight, ChatHistory
from .serializers import BookListSerializer, BookDetailSerializer, ChatHistorySerializer
from ai_engine.insights import generate_insights_for_book
from ai_engine.rag import answer_question, index_book_in_chroma
from scraper.scraper import BookScraper

logger = logging.getLogger(__name__)


# ─── GET /api/books/ ─────────────────────────────────────────────────────────

@api_view(["GET"])
def list_books(request):
    """
    Returns all books with optional search filtering.
    Query params:
      ?search=harry    — filter by title/author
      ?genre=fiction   — filter by genre
    """
    books = Book.objects.all()

    # Optional filters
    search = request.query_params.get("search", "").strip()
    genre = request.query_params.get("genre", "").strip()

    if search:
        books = books.filter(title__icontains=search) | books.filter(author__icontains=search)
    if genre:
        books = books.filter(genre__icontains=genre)

    # Manual pagination (simple)
    page = int(request.query_params.get("page", 1))
    page_size = 20
    total = books.count()
    start = (page - 1) * page_size
    end = start + page_size

    serializer = BookListSerializer(books[start:end], many=True)
    return Response({
        "count": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
        "results": serializer.data,
    })


# ─── GET /api/books/<id>/ ─────────────────────────────────────────────────────

@api_view(["GET"])
def book_detail(request, book_id):
    """Returns full book details including AI insights."""
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = BookDetailSerializer(book)
    return Response(serializer.data)


# ─── GET /api/books/<id>/recommend/ ──────────────────────────────────────────

@api_view(["GET"])
def recommend_books(request, book_id):
    """
    Returns up to 5 books similar to the given book.
    Uses ChromaDB embedding similarity if the book is indexed,
    otherwise falls back to same-genre matching.
    """
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

    # Cache key: recommendations are stable, cache for 24h
    cache_key = f"recommend_{book_id}"
    cached = cache.get(cache_key)
    if cached:
        return Response({"source": "cache", "results": cached})

    # Try embedding-based similarity first
    if book.is_indexed:
        try:
            from ai_engine.rag import get_similar_books
            similar_ids = get_similar_books(book_id, n_results=5)
            similar_books = Book.objects.filter(id__in=similar_ids).exclude(id=book_id)
            serializer = BookListSerializer(similar_books, many=True)
            cache.set(cache_key, serializer.data, settings.CACHE_TTL)
            return Response({"source": "embeddings", "results": serializer.data})
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}, falling back to genre match")

    # Fallback: same genre or random
    if book.genre:
        similar_books = Book.objects.filter(genre__icontains=book.genre).exclude(id=book_id)[:5]
    else:
        similar_books = Book.objects.exclude(id=book_id).order_by("?")[:5]

    serializer = BookListSerializer(similar_books, many=True)
    cache.set(cache_key, serializer.data, settings.CACHE_TTL)
    return Response({"source": "genre", "results": serializer.data})


# ─── POST /api/books/upload/ ─────────────────────────────────────────────────

@api_view(["POST"])
def upload_books(request):
    """
    Triggers scraping, stores books, generates AI insights, indexes in ChromaDB.
    Body (optional): { "pages": 5 }   — how many pages to scrape (default: 3)
    """
    pages = int(request.data.get("pages", 3))
    pages = min(pages, 10)  # safety cap

    try:
        # 1. Scrape books from books.toscrape.com
        scraper = BookScraper()
        scraped_books = scraper.scrape(max_pages=pages)
        logger.info(f"Scraped {len(scraped_books)} books")

        saved_count = 0
        for book_data in scraped_books:
            # Skip if already in DB (using URL as unique key)
            if Book.objects.filter(book_url=book_data["book_url"]).exists():
                continue

            book = Book.objects.create(**book_data)
            saved_count += 1

            # 2. Generate AI insights
            try:
                generate_insights_for_book(book)
            except Exception as e:
                logger.error(f"AI insight failed for {book.title}: {e}")

            # 3. Index in ChromaDB for RAG
            try:
                index_book_in_chroma(book)
            except Exception as e:
                logger.error(f"ChromaDB indexing failed for {book.title}: {e}")

        return Response({
            "message": f"Successfully processed {saved_count} new books.",
            "total_scraped": len(scraped_books),
            "new_books": saved_count,
        })

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── POST /api/books/ask/ ─────────────────────────────────────────────────────

@api_view(["POST"])
def ask_question(request):
    """
    RAG Q&A endpoint.
    Body: { "question": "What is a good mystery book?", "book_id": null }
    Returns answer with source citations.
    """
    question = request.data.get("question", "").strip()
    book_id = request.data.get("book_id", None)   # optional: restrict to one book

    if not question:
        return Response({"error": "question is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Cache key — cache same question for 1 hour
    cache_key = f"qa_{hash(question)}_{book_id}"
    cached = cache.get(cache_key)
    if cached:
        return Response({"source": "cache", **cached})

    try:
        result = answer_question(question, book_id=book_id)

        # Save to chat history
        ChatHistory.objects.create(
            question=question,
            answer=result["answer"],
            sources=result["sources"],
            book_id=book_id,
        )

        cache.set(cache_key, result, 3600)  # 1-hour cache for QA
        return Response(result)

    except Exception as e:
        logger.error(f"Q&A failed: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── GET /api/books/history/ ─────────────────────────────────────────────────

@api_view(["GET"])
def chat_history(request):
    """Returns recent Q&A history (bonus feature)."""
    history = ChatHistory.objects.all()[:50]
    serializer = ChatHistorySerializer(history, many=True)
    return Response(serializer.data)
