"""
rag.py — complete RAG pipeline using Groq (free) + sentence-transformers (local/free).

Steps:
  1. INDEXING  : book text → overlapping chunks → embed (local model) → ChromaDB
  2. RETRIEVAL : embed question → cosine similarity search → top-5 chunks
  3. GENERATION: chunks as context → Groq LLM (70b) → answer + source citations
"""

import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from django.conf import settings

from books.models import Book, BookChunk
from .groq_client import call_llm

logger = logging.getLogger(__name__)

# ── Singletons ────────────────────────────────────────────────────────────────
_embedding_model = None
_chroma_client   = None
_collection      = None

COLLECTION_NAME = "books"
CHUNK_SIZE      = 400   # characters per chunk
CHUNK_OVERLAP   = 80    # overlap between consecutive chunks


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model (first time only, ~30 seconds)...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Splits text into overlapping chunks.
    Overlap helps avoid losing context at chunk boundaries.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start  = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ── Indexing ──────────────────────────────────────────────────────────────────

def index_book_in_chroma(book: Book) -> None:
    """
    Chunks book text, embeds it, and stores in ChromaDB.
    Also saves BookChunk records to the relational DB for traceability.
    """
    if book.is_indexed:
        logger.info(f"Already indexed: {book.title}")
        return

    full_text = f"{book.title}. Genre: {book.genre}. {book.description}".strip()
    if not full_text:
        return

    chunks     = chunk_text(full_text)
    model      = _get_embedding_model()
    collection = _get_collection()

    documents  = []
    embeddings = []
    metadatas  = []
    ids        = []

    for i, chunk in enumerate(chunks):
        chroma_id = f"book_{book.id}_chunk_{i}"
        embedding = model.encode(chunk).tolist()

        documents.append(chunk)
        embeddings.append(embedding)
        metadatas.append({
            "book_id":    book.id,
            "book_title": book.title,
            "author":     book.author,
            "genre":      book.genre,
            "chunk_index": i,
        })
        ids.append(chroma_id)

        BookChunk.objects.get_or_create(
            book=book,
            chunk_index=i,
            defaults={"text": chunk, "chroma_id": chroma_id},
        )

    collection.upsert(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)

    book.is_indexed = True
    book.save(update_fields=["is_indexed"])
    logger.info(f"Indexed '{book.title}' → {len(chunks)} chunks")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_chunks(question: str, n_results: int = 5, book_id: int = None) -> list:
    """
    Embeds the question and returns the most similar chunks from ChromaDB.
    Optionally filters to a single book.
    """
    model      = _get_embedding_model()
    collection = _get_collection()

    q_embedding  = model.encode(question).tolist()
    where_filter = {"book_id": book_id} if book_id else None

    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=min(n_results, collection.count() or 1),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text":       results["documents"][0][i],
            "book_id":    results["metadatas"][0][i]["book_id"],
            "book_title": results["metadatas"][0][i]["book_title"],
            "author":     results["metadatas"][0][i].get("author", "Unknown"),
            "genre":      results["metadatas"][0][i].get("genre", ""),
            "score":      round(1 - results["distances"][0][i], 3),
        })
    return chunks


# ── Generation ────────────────────────────────────────────────────────────────

def answer_question(question: str, book_id: int = None) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve relevant chunks via embedding similarity
      2. Build a context string from those chunks
      3. Ask Groq 70b to answer using that context
      4. Return answer + deduplicated source citations
    """
    chunks = retrieve_chunks(question, n_results=5, book_id=book_id)

    if not chunks:
        return {
            "answer":  "No books in the library yet. Please scrape some books first using the Dashboard.",
            "sources": [],
        }

    # Build context from retrieved chunks
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}] \"{c['book_title']}\" by {c['author']} (Genre: {c['genre']})\n{c['text']}"
        )
    context = "\n\n".join(context_parts)

    system = (
        "You are a knowledgeable book assistant. Answer questions using ONLY the provided book excerpts. "
        "Always mention which book(s) your answer is based on by title. "
        "Be helpful, accurate, and concise. If you cannot answer from the context, say so."
    )

    prompt = f"""Use these book excerpts to answer the question below.

{context}

Question: {question}

Answer based on the excerpts above. Cite book titles in your answer."""

    answer_text = call_llm(prompt, system=system, use_smart_model=True, max_tokens=800)

    # Build deduplicated source list
    seen    = set()
    sources = []
    for c in chunks:
        if c["book_id"] not in seen:
            seen.add(c["book_id"])
            sources.append({
                "book_id":         c["book_id"],
                "book_title":      c["book_title"],
                "author":          c["author"],
                "excerpt":         c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                "relevance_score": c["score"],
            })

    return {"answer": answer_text, "sources": sources}


# ── Similarity for recommendations ───────────────────────────────────────────

def get_similar_books(book_id: int, n_results: int = 5) -> list:
    """
    Finds books similar to book_id via embedding cosine similarity.
    Returns list of similar book IDs.
    """
    try:
        chunk = BookChunk.objects.filter(book_id=book_id).first()
        if not chunk:
            return []

        results = retrieve_chunks(chunk.text, n_results=n_results + 5)

        seen       = set()
        similar_ids = []
        for r in results:
            bid = r["book_id"]
            if bid != book_id and bid not in seen:
                seen.add(bid)
                similar_ids.append(bid)
            if len(similar_ids) >= n_results:
                break

        return similar_ids
    except Exception as e:
        logger.error(f"get_similar_books error: {e}")
        return []
