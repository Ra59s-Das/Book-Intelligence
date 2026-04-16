"""
BookScraper — scrapes books.toscrape.com using requests + BeautifulSoup.

books.toscrape.com is a legal practice site designed for scraping.
It has 1000 books across 50 pages.

Usage:
    scraper = BookScraper()
    books = scraper.scrape(max_pages=5)   # returns list of dicts
"""

import logging
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com"

# Maps word ratings to numbers
RATING_MAP = {
    "One": 1.0,
    "Two": 2.0,
    "Three": 3.0,
    "Four": 4.0,
    "Five": 5.0,
}


class BookScraper:
    """Scrapes book listings and detail pages from books.toscrape.com"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (educational scraper)"
        })

    def scrape(self, max_pages: int = 3) -> list[dict]:
        """
        Scrapes up to max_pages pages of books.
        Returns a list of book dicts ready to insert into the DB.
        """
        all_books = []
        page = 1

        while page <= max_pages:
            url = f"{BASE_URL}/catalogue/page-{page}.html"
            logger.info(f"Scraping page {page}: {url}")

            soup = self._get_soup(url)
            if soup is None:
                break

            books_on_page = soup.select("article.product_pod")
            if not books_on_page:
                break

            for article in books_on_page:
                try:
                    book_data = self._parse_listing(article)
                    # Fetch the detail page for description and more info
                    detailed = self._scrape_detail(book_data["book_url"])
                    book_data.update(detailed)
                    all_books.append(book_data)
                    time.sleep(0.2)   # polite delay
                except Exception as e:
                    logger.warning(f"Failed to parse book: {e}")
                    continue

            page += 1
            time.sleep(0.5)   # polite delay between pages

        logger.info(f"Total books scraped: {len(all_books)}")
        return all_books

    def _parse_listing(self, article) -> dict:
        """Parses a book card from the listing page."""
        # Title
        title_tag = article.select_one("h3 a")
        title = title_tag["title"] if title_tag else "Unknown"

        # Rating (stored as word class e.g. "Three")
        rating_tag = article.select_one("p.star-rating")
        rating_word = rating_tag["class"][1] if rating_tag else "One"
        rating = RATING_MAP.get(rating_word, 1.0)

        # Price
        price_tag = article.select_one("p.price_color")
        price = price_tag.text.strip() if price_tag else ""

        # Availability
        avail_tag = article.select_one("p.availability")
        availability = avail_tag.text.strip() if avail_tag else ""

        # Cover image
        img_tag = article.select_one("img")
        img_src = img_tag["src"] if img_tag else ""
        cover_image_url = f"{BASE_URL}/{img_src.replace('../', '')}" if img_src else ""

        # Book detail URL
        relative_url = title_tag["href"] if title_tag else ""
        book_url = f"{BASE_URL}/catalogue/{relative_url.replace('../', '')}"

        return {
            "title": title,
            "rating": rating,
            "price": price,
            "availability": availability,
            "cover_image_url": cover_image_url,
            "book_url": book_url,
        }

    def _scrape_detail(self, book_url: str) -> dict:
        """
        Fetches the individual book page for description, genre, and UPC.
        Returns a dict to merge into the listing data.
        """
        soup = self._get_soup(book_url)
        if soup is None:
            return {"description": "", "genre": "", "author": "Unknown", "num_reviews": 0}

        # Description — lives in <p> after <div id="product_description">
        description = ""
        desc_header = soup.find("div", id="product_description")
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            if desc_p:
                description = desc_p.text.strip()

        # Genre — second breadcrumb item
        genre = ""
        breadcrumbs = soup.select("ul.breadcrumb li")
        if len(breadcrumbs) >= 3:
            genre = breadcrumbs[2].text.strip()

        # Product table (UPC, reviews etc.)
        num_reviews = 0
        table = soup.select("table.table-striped tr")
        for row in table:
            header = row.find("th")
            value = row.find("td")
            if header and value:
                if "Number of reviews" in header.text:
                    try:
                        num_reviews = int(value.text.strip())
                    except ValueError:
                        pass

        return {
            "description": description,
            "genre": genre,
            "author": "Unknown",   # books.toscrape doesn't have authors
            "num_reviews": num_reviews,
        }

    def _get_soup(self, url: str):
        """Makes an HTTP GET request and returns a BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
