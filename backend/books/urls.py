from django.urls import path
from . import views

urlpatterns = [
    path("books/",                      views.list_books,      name="list-books"),
    path("books/upload/",               views.upload_books,    name="upload-books"),
    path("books/ask/",                  views.ask_question,    name="ask-question"),
    path("books/history/",              views.chat_history,    name="chat-history"),
    path("books/<int:book_id>/",        views.book_detail,     name="book-detail"),
    path("books/<int:book_id>/recommend/", views.recommend_books, name="recommend-books"),
]
