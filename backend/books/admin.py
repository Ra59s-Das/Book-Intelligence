from django.contrib import admin
from .models import Book, AIInsight, BookChunk, ChatHistory

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "rating", "genre", "is_processed", "is_indexed", "scraped_at"]
    list_filter = ["is_processed", "is_indexed", "genre"]
    search_fields = ["title", "author"]

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ["book", "genre_prediction", "sentiment", "generated_at"]

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ["question", "asked_at"]
    readonly_fields = ["question", "answer", "sources", "asked_at"]

admin.site.register(BookChunk)
