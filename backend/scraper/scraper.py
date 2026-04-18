"""
BookScraper — scrapes books.toscrape.com.

Uses requests + BeautifulSoup for fast bulk scraping.
Uses Selenium for JavaScript-heavy pages or when requests fails (fallback).

books.toscrape.com is a legal practice site made for scraping.
It has 1000 books across 50 pages.

Usage:
    scraper = BookScraper()
    books = scraper.scrape(max_pages=5)
"""

import logging
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com"

RATING_MAP = {
    "One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0,
}


class SeleniumScraper:
    """
    Selenium-based scraper used as fallback when requests fails.
    Handles JavaScript-rendered pages.
    Install: pip install selenium
    Requires ChromeDriver matching your Chrome version.
    """

    def __init__(self):
        self.driver = None

    def _init_driver(self):
        """Initializes headless Chrome via Selenium."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            options = Options()
            options.add_argument("--headless")           # run without opening browser
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium ChromeDriver initialized")
            return True
        except Exception as e:
            logger.warning(f"Selenium not available: {e}. Falling back to requests.")
            return False

    def get_page_source(self, url: str) -> str:
        """Gets fully rendered page source using Selenium."""
        if not self.driver and not self._init_driver():
            return None
        try:
            self.driver.get(url)
            time.sleep(1.5)   # wait for JS to render
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium failed for {url}: {e}")
            return None

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


class BookScraper:
    """
    Main scraper — uses requests+BeautifulSoup (fast).
    Falls back to Selenium if requests fails.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (educational scraper for book intelligence project)"
        })
        self.selenium = SeleniumScraper()   # available as fallback

    def scrape(self, max_pages: int = 3) -> list:
        """
        Scrapes up to max_pages of books (20 books per page).
        Returns list of book dicts ready to save to DB.
        """
        all_books = []
        page = 1

        while page <= max_pages:
            url = f"{BASE_URL}/catalogue/page-{page}.html"
            logger.info(f"Scraping page {page}/{max_pages}: {url}")

            soup = self._get_soup(url)
            if soup is None:
                logger.warning(f"Failed to get page {page}, stopping.")
                break

            articles = soup.select("article.product_pod")
            if not articles:
                break

            for article in articles:
                try:
                    book_data = self._parse_listing(article)
                    detail    = self._scrape_detail(book_data["book_url"])
                    book_data.update(detail)
                    all_books.append(book_data)
                    time.sleep(0.15)   # polite delay
                except Exception as e:
                    logger.warning(f"Failed to parse book: {e}")
                    continue

            logger.info(f"Page {page} done — {len(articles)} books")
            page += 1
            time.sleep(0.4)

        self.selenium.quit()
        logger.info(f"Total scraped: {len(all_books)} books")
        return all_books

    def _get_soup(self, url: str):
        """
        Tries requests first. Falls back to Selenium if it fails.
        Returns BeautifulSoup object or None.
        """
        # Try requests first (fast)
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.warning(f"requests failed for {url}: {e}. Trying Selenium...")

        # Fallback to Selenium
        source = self.selenium.get_page_source(url)
        if source:
            return BeautifulSoup(source, "html.parser")

        return None

    def _parse_listing(self, article) -> dict:
        """Parses a book card from the listing page."""
        title_tag    = article.select_one("h3 a")
        title        = title_tag["title"] if title_tag else "Unknown"
        rating_tag   = article.select_one("p.star-rating")
        rating_word  = rating_tag["class"][1] if rating_tag else "One"
        rating       = RATING_MAP.get(rating_word, 1.0)
        price_tag    = article.select_one("p.price_color")
        price        = price_tag.text.strip() if price_tag else ""
        avail_tag    = article.select_one("p.availability")
        availability = avail_tag.text.strip() if avail_tag else ""
        img_tag      = article.select_one("img")
        img_src      = img_tag["src"] if img_tag else ""
        cover_image_url = f"{BASE_URL}/{img_src.replace('../', '')}" if img_src else ""
        relative_url = title_tag["href"] if title_tag else ""
        book_url     = f"{BASE_URL}/catalogue/{relative_url.replace('../', '')}"

        return {
            "title": title, "rating": rating, "price": price,
            "availability": availability, "cover_image_url": cover_image_url,
            "book_url": book_url,
        }

    def _scrape_detail(self, book_url: str) -> dict:
        """Fetches the individual book page for description and genre."""
        soup = self._get_soup(book_url)
        if soup is None:
            return {"description": "", "genre": "", "author": "Unknown", "num_reviews": 0}

        description = ""
        desc_header = soup.find("div", id="product_description")
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            if desc_p:
                description = desc_p.text.strip()

        genre = ""
        breadcrumbs = soup.select("ul.breadcrumb li")
        if len(breadcrumbs) >= 3:
            genre = breadcrumbs[2].text.strip()

        num_reviews = 0
        for row in soup.select("table.table-striped tr"):
            header = row.find("th")
            value  = row.find("td")
            if header and value and "Number of reviews" in header.text:
                try:
                    num_reviews = int(value.text.strip())
                except ValueError:
                    pass

        return {
            "description": description, "genre": genre,
            "author": "Unknown", "num_reviews": num_reviews,
        }
