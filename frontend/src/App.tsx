import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CalendarView from "./pages/CalendarView";
import HumanInLoopChat from "./components/HumanInLoopChat";
import { LayoutDashboard, Calendar, FileEdit } from "lucide-react";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50 text-slate-800">
        {/* Sidebar */}
        <div className="w-64 bg-slate-900 text-slate-300 flex flex-col items-center py-8 gap-4 shadow-xl">
          <h1 className="text-2xl font-bold text-white mb-8">ContentForge</h1>
          <nav className="w-full">
            <Link to="/" className="flex items-center gap-3 w-full px-6 py-4 hover:bg-slate-800 hover:text-white transition">
              <LayoutDashboard size={20} />
              Engine Dashboard
            </Link>
            <Link to="/calendar" className="flex items-center gap-3 w-full px-6 py-4 hover:bg-slate-800 hover:text-white transition">
              <Calendar size={20} />
              Weekly Calendar
            </Link>
            <Link to="/review" className="flex items-center gap-3 w-full px-6 py-4 hover:bg-slate-800 hover:text-white transition">
              <FileEdit size={20} />
              Content Review
            </Link>
          </nav>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calendar" element={<CalendarView />} />
            <Route path="/review" element={<HumanInLoopChat />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
