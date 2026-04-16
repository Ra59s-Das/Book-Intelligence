"""
Django management command to run the scraper from the terminal.

Usage:
    python manage.py scrape_books            # scrape 3 pages (default)
    python manage.py scrape_books --pages 10 # scrape 10 pages
"""

import logging
from django.core.management.base import BaseCommand
from scraper.scraper import BookScraper
from books.models import Book
from ai_engine.insights import generate_insights_for_book
from ai_engine.rag import index_book_in_chroma

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrapes books from books.toscrape.com and processes them with AI"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=3,
            help="Number of pages to scrape (each page has 20 books)",
        )

    def handle(self, *args, **options):
        pages = options["pages"]
        self.stdout.write(f"Starting scrape for {pages} pages...")

        scraper = BookScraper()
        scraped_books = scraper.scrape(max_pages=pages)

        saved = 0
        skipped = 0

        for book_data in scraped_books:
            if Book.objects.filter(book_url=book_data["book_url"]).exists():
                skipped += 1
                continue

            book = Book.objects.create(**book_data)
            saved += 1
            self.stdout.write(f"  Saved: {book.title}")

            # Generate AI insights
            try:
                generate_insights_for_book(book)
                self.stdout.write(f"    ✓ AI insights generated")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    ✗ AI failed: {e}"))

            # Index in ChromaDB
            try:
                index_book_in_chroma(book)
                self.stdout.write(f"    ✓ Indexed in ChromaDB")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    ✗ ChromaDB failed: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Saved: {saved} new books. Skipped: {skipped} duplicates."
        ))
