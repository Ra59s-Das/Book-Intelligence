/**
 * QAInterface.jsx — the question-answering page.
 * Users type a question, Claude answers using the RAG pipeline.
 * Supports: general questions or book-specific questions (via ?book_id= URL param).
 * Also shows saved chat history.
 */

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { askQuestion, fetchHistory } from "../api/client";
import AnswerDisplay from "../components/AnswerDisplay";

// Sample questions to help users get started
const SAMPLE_QUESTIONS = [
  "What are some good mystery books?",
  "Recommend a book with a dark tone",
  "Which books are about adventure?",
  "What is the best-rated book available?",
  "Recommend something similar to a thriller",
];

export default function QAInterface() {
  const [searchParams]            = useSearchParams();
  const bookId                    = searchParams.get("book_id") || null;
  const bookTitle                 = searchParams.get("title") || null;

  const [question, setQuestion]   = useState("");
  const [result, setResult]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [history, setHistory]     = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const inputRef                  = useRef(null);

  // Focus input on mount
  useEffect(() => { inputRef.current?.focus(); }, []);

  // Load chat history
  useEffect(() => {
    fetchHistory().then(setHistory).catch(() => {});
  }, [result]);   // reload after each new answer

  const handleAsk = async (q = question) => {
    const trimmed = q.trim();
    if (!trimmed) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await askQuestion(trimmed, bookId ? parseInt(bookId) : null);
      setResult(data);
    } catch (e) {
      setError("Failed to get an answer. Make sure the backend is running and books are scraped.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Ask About Books</h1>
        {bookTitle ? (
          <p className="text-sm text-brand-600 mt-1 font-medium">
            📖 Asking about: {bookTitle}
          </p>
        ) : (
          <p className="text-sm text-gray-500 mt-1">
            Ask anything — recommendations, themes, summaries, comparisons.
          </p>
        )}
      </div>

      {/* Input area */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-6">
        <textarea
          ref={inputRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. What are some good mystery books? Or: Recommend something dark and suspenseful."
          rows={3}
          className="w-full resize-none text-sm text-gray-800 placeholder-gray-400
                     focus:outline-none leading-relaxed"
        />
        <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">Press Enter to send · Shift+Enter for new line</p>
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question.trim()}
            className="flex items-center gap-2 bg-brand-500 hover:bg-brand-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {loading ? (
              <><span className="animate-spin text-base">⏳</span> Thinking…</>
            ) : (
              <>✨ Ask</>
            )}
          </button>
        </div>
      </div>

      {/* Sample questions */}
      {!result && !loading && (
        <div className="mb-6">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-2">Try asking</p>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => { setQuestion(q); handleAsk(q); }}
                className="text-xs bg-gray-50 hover:bg-brand-50 border border-gray-200
                           hover:border-brand-500 text-gray-600 hover:text-brand-700
                           px-3 py-1.5 rounded-lg transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-4">
          <div className="flex items-center gap-3 text-gray-500 text-sm">
            <span className="animate-spin text-xl">🔍</span>
            <div>
              <p className="font-medium">Searching the library…</p>
              <p className="text-xs text-gray-400 mt-0.5">Finding relevant books · Building context · Generating answer</p>
            </div>
          </div>
        </div>
      )}

      {/* Answer */}
      {result && <AnswerDisplay result={result} />}

      {/* Chat history */}
      {history.length > 0 && (
        <div className="mt-8">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            <span>{showHistory ? "▼" : "▶"}</span>
            Recent Questions ({history.length})
          </button>

          {showHistory && (
            <div className="mt-3 space-y-2">
              {history.slice(0, 10).map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    setQuestion(item.question);
                    setResult({ answer: item.answer, sources: item.sources });
                  }}
                  className="bg-white border border-gray-100 rounded-xl px-4 py-3 cursor-pointer
                             hover:border-brand-500 transition-colors"
                >
                  <p className="text-sm font-medium text-gray-800 line-clamp-1">{item.question}</p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{item.answer}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
