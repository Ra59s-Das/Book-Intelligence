/**
 * Dashboard.jsx — main page showing all books in a responsive grid.
 * Features: search, genre filter, pagination, scrape trigger.
 */

import { useState, useEffect, useCallback } from "react";
import { fetchBooks, triggerScrape } from "../api/client";
import BookCard from "../components/BookCard";

export default function Dashboard() {
  const [books, setBooks]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [scraping, setScraping]   = useState(false);
  const [search, setSearch]       = useState("");
  const [genre, setGenre]         = useState("");
  const [page, setPage]           = useState(1);
  const [meta, setMeta]           = useState({ count: 0, total_pages: 1 });
  const [scrapeMsg, setScrapeMsg] = useState("");
  const [error, setError]         = useState("");

  // Fetch books whenever search/genre/page changes
  const loadBooks = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchBooks({ search, genre, page });
      setBooks(data.results);
      setMeta({ count: data.count, total_pages: data.total_pages });
    } catch (e) {
      setError("Could not load books. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [search, genre, page]);

  useEffect(() => { loadBooks(); }, [loadBooks]);

  // Debounce search input
  const handleSearch = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg("");
    try {
      const result = await triggerScrape(3);
      setScrapeMsg(`✓ ${result.message}`);
      loadBooks();
    } catch (e) {
      setScrapeMsg("✗ Scrape failed. Check backend logs.");
    } finally {
      setScraping(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Book Library</h1>
          <p className="text-gray-500 text-sm mt-1">{meta.count} books indexed</p>
        </div>
        <button
          onClick={handleScrape}
          disabled={scraping}
          className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-60
                     text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {scraping ? (
            <>
              <span className="animate-spin">⏳</span> Scraping books…
            </>
          ) : (
            <>🕷️ Scrape Books</>
          )}
        </button>
      </div>

      {/* Scrape status message */}
      {scrapeMsg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
          scrapeMsg.startsWith("✓")
            ? "bg-green-50 text-green-700 border border-green-200"
            : "bg-red-50 text-red-700 border border-red-200"
        }`}>
          {scrapeMsg}
        </div>
      )}

      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <input
          type="text"
          placeholder="Search by title or author…"
          value={search}
          onChange={handleSearch}
          className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        <select
          value={genre}
          onChange={(e) => { setGenre(e.target.value); setPage(1); }}
          className="border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-white
                     focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All Genres</option>
          {["Fiction", "Mystery", "Romance", "Science Fiction", "Fantasy",
            "Thriller", "History", "Self-Help", "Biography", "Children's", "Poetry"].map((g) => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && books.length === 0 && (
        <div className="text-center py-20 text-gray-400">
          <div className="text-6xl mb-4">📭</div>
          <p className="text-lg font-medium">No books yet</p>
          <p className="text-sm mt-1">Click "Scrape Books" to get started</p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-64 animate-pulse" />
          ))}
        </div>
      )}

      {/* Book grid */}
      {!loading && books.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {meta.total_pages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded-lg border border-gray-200 text-sm
                       disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            ← Prev
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {meta.total_pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(meta.total_pages, p + 1))}
            disabled={page === meta.total_pages}
            className="px-4 py-2 rounded-lg border border-gray-200 text-sm
                       disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
