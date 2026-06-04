import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CalendarView from "./pages/CalendarView";
import CreativeManager from "./pages/CreativeManager";
import CreativeCalendar from "./pages/CreativeCalendar";
import HumanInLoopChat from "./components/HumanInLoopChat";
import { LayoutDashboard, Calendar, FileEdit, Sparkles, CalendarCheck } from "lucide-react";

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 w-full px-6 py-4 transition ${
        isActive
          ? "bg-slate-800 text-white border-l-4 border-blue-400"
          : "hover:bg-slate-800 hover:text-white"
      }`}
    >
      {children}
    </Link>
  );
}

export default function App() {
  const [weekId, setWeekId] = useState(() => {
    return localStorage.getItem("contentforge_weekId") || "2026-W37";
  });

  // Persist weekId to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("contentforge_weekId", weekId);
  }, [weekId]);

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50 text-slate-800">
        {/* Sidebar */}
        <div className="w-64 bg-slate-900 text-slate-300 flex flex-col items-center py-8 gap-4 shadow-xl">
          <h1 className="text-2xl font-bold text-white mb-2">ContentForge</h1>
          <span className="text-xs font-mono bg-slate-700 text-slate-300 px-3 py-1 rounded-full mb-6">{weekId}</span>
          <nav className="w-full">
            <NavLink to="/">
              <LayoutDashboard size={20} />
              Engine Dashboard
            </NavLink>
            <NavLink to="/calendar">
              <Calendar size={20} />
              Weekly Calendar
            </NavLink>
            <NavLink to="/review">
              <FileEdit size={20} />
              Content Review
            </NavLink>
            <div className="my-3 mx-6 border-t border-slate-700" />
            <NavLink to="/creative">
              <Sparkles size={20} />
              Creative Manager
            </NavLink>
            <NavLink to="/creative-calendar">
              <CalendarCheck size={20} />
              Creative Calendar
            </NavLink>
          </nav>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard weekId={weekId} setWeekId={setWeekId} />} />
            <Route path="/calendar" element={<CalendarView weekId={weekId} />} />
            <Route path="/review" element={<HumanInLoopChat weekId={weekId} />} />
            <Route path="/creative" element={<CreativeManager weekId={weekId} />} />
            <Route path="/creative-calendar" element={<CreativeCalendar />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
