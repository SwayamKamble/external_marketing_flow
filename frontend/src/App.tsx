import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import CreativeManager from "./pages/CreativeManager";
import CreativeCalendar from "./pages/CreativeCalendar";
import { Sparkles, CalendarCheck, Sun, Moon, LogOut } from "lucide-react";
import LoginSignup from "./components/LoginSignup";

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
  const weekId = localStorage.getItem("contentforge_weekId") || "2026-W37";
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("contentforge_theme") || "dark";
  });

  const [token, setToken] = useState<string | null>(() => localStorage.getItem("auth_token"));
  const [username, setUsername] = useState<string | null>(() => localStorage.getItem("auth_username"));

  useEffect(() => {
    if (theme === "light") {
      document.body.classList.add("light-mode");
    } else {
      document.body.classList.remove("light-mode");
    }
    localStorage.setItem("contentforge_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const handleLoginSuccess = (user: string, userId: string, sessionToken: string) => {
    localStorage.setItem("auth_token", sessionToken);
    localStorage.setItem("auth_username", user);
    localStorage.setItem("auth_user_id", userId);
    setToken(sessionToken);
    setUsername(user);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_username");
    localStorage.removeItem("auth_user_id");
    setToken(null);
    setUsername(null);
  };

  // Auth route guard overlay
  if (!token) {
    return <LoginSignup onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-50 text-slate-800">
        {/* Sidebar */}
        <div className="w-64 bg-slate-900 text-slate-300 flex flex-col items-center py-8 gap-4 shadow-xl shrink-0">
          <h1 className="text-2xl font-bold text-white mb-2">SocialHQ</h1>
          <span className="text-xs font-mono bg-slate-700 text-slate-300 px-3 py-1 rounded-full mb-6">{weekId}</span>
          <nav className="w-full">
            <NavLink to="/">
              <Sparkles size={20} />
              SocialHQ
            </NavLink>
            <NavLink to="/creative-calendar">
              <CalendarCheck size={20} />
              HQBoard
            </NavLink>
          </nav>

          {/* User Profile Info & Logout */}
          <div className="w-full px-6 flex flex-col gap-2 mt-auto">
            <div className="flex flex-col border-t border-slate-800 pt-4 mb-2">
              <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Logged in as</span>
              <span className="text-white text-sm font-semibold truncate">{username}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-red-950/40 hover:bg-red-900/40 border border-red-500/20 hover:border-red-500/40 text-xs font-semibold text-red-300 transition cursor-pointer"
            >
              <LogOut size={14} />
              <span>Log Out</span>
            </button>
          </div>

          {/* Theme Toggle Button */}
          <div className="px-6 w-full mt-4">
            <button
              onClick={toggleTheme}
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl border border-slate-700 hover:border-slate-500 text-xs font-semibold text-slate-300 hover:text-white transition cursor-pointer"
            >
              {theme === "dark" ? (
                <>
                  <Sun size={14} className="text-amber-400" />
                  <span>Light Mode</span>
                </>
              ) : (
                <>
                  <Moon size={14} className="text-indigo-400" />
                  <span>Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<CreativeManager weekId={weekId} />} />
            <Route path="/creative" element={<CreativeManager weekId={weekId} />} />
            <Route path="/creative-calendar" element={<CreativeCalendar />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
