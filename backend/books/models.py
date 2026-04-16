"""
Database models for the Book Intelligence Platform.

Tables:
  - Book          : scraped book metadata
  - AIInsight     : AI-generated analysis for each book (cached)
  - BookChunk     : text chunks used for RAG
  - ChatHistory   : saved Q&A sessions
"""

from django.db import models


class Book(models.Model):
    """Stores metadata for each scraped book."""

    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True, default="Unknown")
    rating = models.FloatField(null=True, blank=True)          # 1.0–5.0
    num_reviews = models.IntegerField(default=0)
    description = models.TextField(blank=True, default="")
    genre = models.CharField(max_length=200, blank=True, default="")
    price = models.CharField(max_length=50, blank=True, default="")
    availability = models.CharField(max_length=100, blank=True, default="")
    book_url = models.URLField(max_length=1000, unique=True)
    cover_image_url = models.URLField(max_length=1000, blank=True, default="")
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Flags to track processing state
    is_processed = models.BooleanField(default=False)   # AI insights generated
    is_indexed = models.BooleanField(default=False)     # Added to ChromaDB

    class Meta:
        ordering = ["-scraped_at"]

    def __str__(self):
        return f"{self.title} ({self.author})"


class AIInsight(models.Model):
    """AI-generated insights for a book. One-to-one with Book."""

    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="ai_insight")

    # Generated fields
    summary = models.TextField(blank=True, default="")
    genre_prediction = models.CharField(max_length=200, blank=True, default="")
    sentiment = models.CharField(max_length=100, blank=True, default="")   # positive/negative/neutral/mixed
    sentiment_score = models.FloatField(null=True, blank=True)             # 0.0–1.0
    key_themes = models.JSONField(default=list)                            # list of theme strings

    generated_at = models.DateTimeField(auto_now_add=True)
    model_used = models.CharField(max_length=100, default="claude-haiku-4-5-20251001")

    def __str__(self):
        return f"Insights for: {self.book.title}"


class BookChunk(models.Model):
    """
    Text chunks of book descriptions used for RAG.
    Each book description is split into overlapping chunks for better retrieval.
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()          # order within the book
    text = models.TextField()                    # the actual chunk text
    chroma_id = models.CharField(max_length=200, unique=True)  # ChromaDB document ID

    class Meta:
        ordering = ["book", "chunk_index"]
        unique_together = ["book", "chunk_index"]

    def __str__(self):
        return f"{self.book.title} — chunk {self.chunk_index}"


class ChatHistory(models.Model):
    """Saves every Q&A interaction for the bonus chat history feature."""

    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list)     # list of {book_id, title, chunk} dicts
    asked_at = models.DateTimeField(auto_now_add=True)

    # Optional: link to a specific book if the question was book-specific
    book = models.ForeignKey(
        Book, on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_history"
    )

    class Meta:
        ordering = ["-asked_at"]

    def __str__(self):
        return f"Q: {self.question[:60]}..."
