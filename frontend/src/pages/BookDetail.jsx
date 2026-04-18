/**
 * BookDetail.jsx — full book detail page.
 * Shows: cover, metadata, AI-generated insights, and similar book recommendations.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchBookDetail, fetchRecommendations } from "../api/client";

function InsightCard({ icon, label, value }) {
  if (!value) return null;
  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <div className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        <span>{icon}</span>{label}
      </div>
      <p className="text-gray-800 text-sm leading-relaxed">{value}</p>
    </div>
  );
}

function SentimentBar({ sentiment, score }) {
  const colours = {
    positive: "bg-green-400",
    hopeful:  "bg-teal-400",
    neutral:  "bg-gray-300",
    mixed:    "bg-amber-400",
    dark:     "bg-red-400",
    negative: "bg-red-500",
  };
  const colour = colours[sentiment] || "bg-gray-300";
  const pct    = Math.round((score || 0.5) * 100);

  return (
    <div className="bg-gray-50 rounded-xl p-4">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        🎭 Sentiment
      </div>
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className={`${colour} h-2 rounded-full transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-sm font-medium text-gray-700 capitalize">{sentiment}</span>
      </div>
    </div>
  );
}

function StarRating({ rating }) {
  return (
    <div className="flex gap-0.5 text-lg">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= Math.round(rating || 0) ? "text-amber-400" : "text-gray-200"}>
          ★
        </span>
      ))}
    </div>
  );
}

export default function BookDetail() {
  const { id }       = useParams();
  const navigate     = useNavigate();
  const [book, setBook]                 = useState(null);
  const [recs, setRecs]                 = useState([]);
  const [loading, setLoading]           = useState(true);
  const [recsLoading, setRecsLoading]   = useState(true);
  const [error, setError]               = useState("");

  useEffect(() => {
    setLoading(true);
    fetchBookDetail(id)
      .then((data) => { setBook(data); setLoading(false); })
      .catch(() => { setError("Book not found."); setLoading(false); });

    fetchRecommendations(id)
      .then((data) => { setRecs(data.results || []); setRecsLoading(false); })
      .catch(() => setRecsLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 animate-pulse">
        <div className="h-8 bg-gray-100 rounded w-1/2 mb-4" />
        <div className="h-4 bg-gray-100 rounded w-1/3" />
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-red-500">{error || "Book not found."}</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-brand-500 text-sm underline">
          ← Go back
        </button>
      </div>
    );
  }

  const ai = book.ai_insight;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-gray-400 hover:text-gray-700 mb-6 flex items-center gap-1 transition-colors"
      >
        ← Back
      </button>

      {/* Top section: cover + core metadata */}
      <div className="flex flex-col sm:flex-row gap-8 mb-8">
        {/* Cover */}
        <div className="w-full sm:w-44 flex-shrink-0">
          {book.cover_image_url ? (
            <img
              src={book.cover_image_url}
              alt={book.title}
              className="w-full rounded-xl shadow-md object-contain bg-gray-50 p-2"
            />
          ) : (
            <div className="w-full h-56 bg-gray-100 rounded-xl flex items-center justify-center text-5xl">
              📚
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="flex-1 space-y-3">
          <h1 className="text-2xl font-bold text-gray-900 leading-snug">{book.title}</h1>
          <p className="text-gray-500">{book.author}</p>

          <StarRating rating={book.rating} />

          <div className="flex flex-wrap gap-2 text-sm">
            {book.genre && (
              <span className="bg-brand-100 text-brand-700 px-3 py-1 rounded-full font-medium">
                {book.genre}
              </span>
            )}
            {book.price && (
              <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full font-medium">
                {book.price}
              </span>
            )}
            {book.availability && (
              <span className="bg-green-50 text-green-700 px-3 py-1 rounded-full font-medium">
                {book.availability}
              </span>
            )}
          </div>

          {book.description && (
            <p className="text-gray-600 text-sm leading-relaxed line-clamp-4">
              {book.description}
            </p>
          )}

          <a
            href={book.book_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-sm text-brand-500 hover:underline mt-1"
          >
            View on source site →
          </a>
        </div>
      </div>

      {/* AI Insights section */}
      {ai ? (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            🤖 AI Insights
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InsightCard icon="📝" label="Summary" value={ai.summary} />
            <InsightCard icon="🏷️" label="Genre Prediction" value={ai.genre_prediction} />
            <SentimentBar sentiment={ai.sentiment} score={ai.sentiment_score} />
            {ai.key_themes?.length > 0 && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  🔑 Key Themes
                </div>
                <div className="flex flex-wrap gap-2">
                  {ai.key_themes.map((theme, i) => (
                    <span key={i} className="bg-white border border-gray-200 text-gray-700 text-xs px-2 py-1 rounded-lg">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="mb-8 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-700">
          AI insights not yet generated for this book.
        </div>
      )}

      {/* Ask about this book */}
      <div className="mb-8">
        <button
          onClick={() => navigate(`/qa?book_id=${book.id}&title=${encodeURIComponent(book.title)}`)}
          className="bg-brand-500 hover:bg-brand-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          💬 Ask a question about this book
        </button>
      </div>

      {/* Recommendations */}
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          📖 You might also like
        </h2>
        {recsLoading ? (
          <div className="flex gap-4">
            {[1, 2, 3].map((i) => <div key={i} className="h-24 bg-gray-100 rounded-xl flex-1 animate-pulse" />)}
          </div>
        ) : recs.length === 0 ? (
          <p className="text-gray-400 text-sm">No recommendations yet.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {recs.map((rec) => (
              <div
                key={rec.id}
                onClick={() => navigate(`/books/${rec.id}`)}
                className="bg-white border border-gray-100 rounded-xl p-3 cursor-pointer
                           hover:border-brand-500 hover:shadow-sm transition-all"
              >
                {rec.cover_image_url && (
                  <img
                    src={rec.cover_image_url}
                    alt={rec.title}
                    className="h-24 w-full object-contain mb-2 bg-gray-50 rounded"
                  />
                )}
                <p className="text-xs font-semibold text-gray-800 line-clamp-2">{rec.title}</p>
                <p className="text-xs text-gray-400 mt-0.5">{rec.genre}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
