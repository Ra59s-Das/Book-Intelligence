"""
Serializers: convert Django model instances → JSON for API responses.
"""

from rest_framework import serializers
from .models import Book, AIInsight, BookChunk, ChatHistory


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = ["summary", "genre_prediction", "sentiment", "sentiment_score", "key_themes", "generated_at"]


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used in the book listing page."""

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "rating", "num_reviews",
            "genre", "price", "availability", "book_url",
            "cover_image_url", "is_processed", "scraped_at",
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """Full serializer with AI insights, used in the book detail page."""

    ai_insight = AIInsightSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "rating", "num_reviews",
            "description", "genre", "price", "availability",
            "book_url", "cover_image_url", "is_processed",
            "is_indexed", "scraped_at", "updated_at", "ai_insight",
        ]


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ["id", "question", "answer", "sources", "asked_at", "book"]
