# BookIQ — Document Intelligence Platform

A full-stack web application that scrapes books, generates AI insights using **Groq (free LLM)**, and supports intelligent Q&A using a RAG pipeline.

> Built with Django REST Framework · React · Tailwind CSS · ChromaDB · Groq API (Free)

---

## Screenshots

> Add 4 screenshots here after running the app:
> 1. Dashboard — book grid with search
> 2. Book detail — AI insights panel
> 3. Q&A interface — answer with source citations
> 4. Recommendations section

---

## Architecture

```
Frontend  (React + Tailwind CSS)
     ↓  REST API
Backend   (Django REST Framework)
  ├── Scraper      → books.toscrape.com (BeautifulSoup)
  ├── AI Insights  → Groq llama-3.1-8b  (summary, genre, sentiment)
  └── RAG Pipeline → sentence-transformers + ChromaDB + Groq llama-3.3-70b
     ↓
SQLite (metadata)  +  ChromaDB (vectors)
```

---

## Tech Stack

| Layer      | Technology                              | Cost  |
|------------|-----------------------------------------|-------|
| Frontend   | React 18, React Router, Tailwind CSS    | Free  |
| Backend    | Django 4.2, Django REST Framework       | Free  |
| Database   | SQLite (dev) / MySQL (prod)             | Free  |
| Vector DB  | ChromaDB                                | Free  |
| Embeddings | sentence-transformers all-MiniLM-L6-v2  | Free  |
| LLM        | Groq API (Llama 3.1 8b + 3.3 70b)      | Free  |
| Scraping   | requests + BeautifulSoup4               | Free  |

**Everything is free. No credit card needed.**

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free Groq API key → https://console.groq.com (sign up with Google/GitHub, no card)

### Quick setup (recommended)

```bash
git clone https://github.com/YOUR_USERNAME/book-intelligence
cd book-intelligence
bash setup.sh
```

Then open `backend/.env` and set `GROQ_API_KEY=gsk_...`

### Manual setup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env → add your GROQ_API_KEY
python manage.py migrate
python manage.py createcachetable
python manage.py runserver      # → http://localhost:8000
```

#### Frontend (new terminal)
```bash
cd frontend
npm install
npm start                       # → http://localhost:3000
```

#### Scrape books
Option A — click **🕷️ Scrape Books** on the Dashboard UI

Option B — terminal (more control):
```bash
cd backend && source venv/bin/activate
python manage.py scrape_books --pages 5   # 5 pages × 20 books = 100 books
```

---

## API Documentation

Base URL: `http://localhost:8000/api`

### GET `/books/`
List all books. Supports `?search=`, `?genre=`, `?page=`.

### GET `/books/<id>/`
Full book detail including AI insights.

### GET `/books/<id>/recommend/`
Returns 5 similar books via embedding similarity.

### POST `/books/upload/`
Trigger scraping + AI processing.
```json
{ "pages": 3 }
```

### POST `/books/ask/`
RAG Q&A endpoint.
```json
{ "question": "What are some good mystery books?", "book_id": null }
```
Response includes `answer` and `sources` with relevance scores.

### GET `/books/history/`
Returns recent Q&A chat history.

---

## Sample Questions & Answers

**Q: What are some highly-rated books in the library?**
> Based on the available books, I found several 5-star rated titles. "The Secret Garden" stands out as a classic with exceptional ratings. "Tipping the Velvet" is also highly rated and belongs to the Fiction genre...

**Q: Recommend a dark or suspenseful book**
> Based on the library, I recommend books from the Mystery and Thriller genres. "Sharp Objects" has a consistently dark tone according to its description, dealing with themes of psychological tension and suspense...

**Q: What self-help books are available?**
> The library contains several Self-Help titles. Based on the descriptions, these books focus on themes of personal growth, mindfulness, and productivity...

---

## AI Features

| Feature              | Model Used             | Description                            |
|----------------------|------------------------|----------------------------------------|
| Summary              | Groq llama-3.1-8b      | 2-3 sentence book summary              |
| Genre Classification | Groq llama-3.1-8b      | Predicted genre from description       |
| Sentiment Analysis   | Groq llama-3.1-8b      | Tone + 0–1 positivity score            |
| Key Themes           | Groq llama-3.1-8b      | 3-5 extracted themes                   |
| RAG Q&A              | Groq llama-3.3-70b     | Answers with ChromaDB source citations |
| Recommendations      | sentence-transformers  | Embedding cosine similarity            |

---

## Bonus Features

- ✅ AI response caching (24h TTL — no repeated API calls)
- ✅ Embedding-based similarity recommendations (ChromaDB cosine)
- ✅ Overlapping chunk strategy (80-char overlap for better RAG recall)
- ✅ Chat history saved and viewable in Q&A page
- ✅ Search + genre filter on Dashboard
- ✅ Pagination (20 books/page)

---

## Project Structure

```
book-intelligence/
├── backend/
│   ├── config/          settings.py, urls.py
│   ├── books/           models, serializers, views (all 5 API endpoints)
│   ├── scraper/         BeautifulSoup scraper + management command
│   ├── ai_engine/       groq_client.py, insights.py, rag.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/         client.js (all axios calls)
│   │   ├── components/  BookCard, AnswerDisplay, Navbar
│   │   └── pages/       Dashboard, BookDetail, QAInterface
│   └── package.json
├── setup.sh             one-click setup script
└── README.md
```
