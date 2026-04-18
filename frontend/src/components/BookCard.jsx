/**
 * BookCard.jsx — displays a single book in the listing grid.
 * Clicking it navigates to the detail page.
 */

import { useNavigate } from "react-router-dom";

// Maps numeric rating to filled/empty stars
function StarRating({ rating }) {
  const stars = Math.round(rating || 0);
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= stars ? "text-amber-400" : "text-gray-200"}>
          ★
        </span>
      ))}
    </div>
  );
}

// Colour badge for genre
function GenreBadge({ genre }) {
  if (!genre) return null;
  return (
    <span className="inline-block bg-brand-100 text-brand-700 text-xs font-medium px-2 py-0.5 rounded-full">
      {genre}
    </span>
  );
}

export default function BookCard({ book }) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/books/${book.id}`)}
      className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md
                 hover:border-brand-500 cursor-pointer transition-all duration-200 overflow-hidden flex flex-col"
    >
      {/* Cover image */}
      <div className="h-48 bg-gray-50 flex items-center justify-center overflow-hidden">
        {book.cover_image_url ? (
          <img
            src={book.cover_image_url}
            alt={book.title}
            className="h-full w-full object-contain p-2"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        ) : (
          <div className="text-5xl select-none">📚</div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">
          {book.title}
        </h3>
        <p className="text-xs text-gray-500">{book.author || "Unknown author"}</p>

        <div className="flex items-center justify-between mt-auto pt-2">
          <StarRating rating={book.rating} />
          <span className="text-sm font-semibold text-gray-700">{book.price}</span>
        </div>

        <div className="flex items-center justify-between">
          <GenreBadge genre={book.genre} />
          {book.is_processed && (
            <span className="text-xs text-green-600 font-medium">✓ AI insights</span>
          )}
        </div>
      </div>
    </div>
  );
}
