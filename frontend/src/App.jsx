/**
 * App.jsx — root component, sets up React Router.
 *
 * Routes:
 *   /            → Dashboard (book listing)
 *   /books/:id   → BookDetail
 *   /qa          → QA Interface
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import BookDetail from "./pages/BookDetail";
import QAInterface from "./pages/QAInterface";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main>
          <Routes>
            <Route path="/"           element={<Dashboard />} />
            <Route path="/books/:id"  element={<BookDetail />} />
            <Route path="/qa"         element={<QAInterface />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
