/**
 * AnswerDisplay.jsx — renders the Claude answer + source citations.
 */

import { useNavigate } from "react-router-dom";

export default function AnswerDisplay({ result }) {
  const navigate = useNavigate();
  if (!result) return null;

  const { answer, sources, source: cacheSource } = result;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
      {/* Cache indicator */}
      {cacheSource === "cache" && (
        <div className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg w-fit">
          <span>⚡</span> Cached response
        </div>
      )}

      {/* Answer */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Answer</h3>
        <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{answer}</p>
      </div>

      {/* Sources */}
      {sources && sources.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Sources ({sources.length})
          </h3>
          <div className="space-y-2">
            {sources.map((src, i) => (
              <div
                key={i}
                onClick={() => navigate(`/books/${src.book_id}`)}
                className="flex gap-3 p-3 rounded-lg bg-gray-50 hover:bg-brand-50
                           border border-transparent hover:border-brand-500
                           cursor-pointer transition-colors"
              >
                <span className="text-brand-500 font-bold text-sm min-w-[20px]">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 text-sm">{src.book_title}</p>
                  <p className="text-xs text-gray-500 mb-1">{src.author}</p>
                  <p className="text-xs text-gray-400 italic line-clamp-2">{src.excerpt}</p>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap self-start mt-0.5">
                  {(src.relevance_score * 100).toFixed(0)}% match
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
