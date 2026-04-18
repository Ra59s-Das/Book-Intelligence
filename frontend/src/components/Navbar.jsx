/**
 * Navbar.jsx — top navigation bar, present on all pages.
 */

import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();

  const links = [
    { to: "/",    label: "Dashboard" },
    { to: "/qa",  label: "Ask AI" },
  ];

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-gray-900">
          <span className="text-2xl">📚</span>
          <span className="text-brand-600">BookIQ</span>
        </Link>

        {/* Links */}
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pathname === link.to
                  ? "bg-brand-500 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
