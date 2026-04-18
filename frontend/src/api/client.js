/**
 * api/client.js — centralises all API calls.
 * Every component imports from here, not from axios directly.
 * baseURL points to Django backend (proxied in dev via package.json "proxy").
 */

import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ── Books ────────────────────────────────────────────────────────────────────

/** Fetch paginated book list. Supports ?search= and ?genre= */
export const fetchBooks = (params = {}) =>
  api.get("/books/", { params }).then((r) => r.data);

/** Fetch full detail for one book including AI insights */
export const fetchBookDetail = (id) =>
  api.get(`/books/${id}/`).then((r) => r.data);

/** Fetch book recommendations for a given book ID */
export const fetchRecommendations = (id) =>
  api.get(`/books/${id}/recommend/`).then((r) => r.data);

/** Trigger scraping. pages = number of pages to scrape (1 page = 20 books) */
export const triggerScrape = (pages = 3) =>
  api.post("/books/upload/", { pages }).then((r) => r.data);

/** Ask a question via RAG. book_id is optional. */
export const askQuestion = (question, book_id = null) =>
  api.post("/books/ask/", { question, book_id }).then((r) => r.data);

/** Fetch recent Q&A history */
export const fetchHistory = () =>
  api.get("/books/history/").then((r) => r.data);

export default api;
