"""
Root URL configuration.
All API routes are prefixed with /api/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("books.urls")),
]
