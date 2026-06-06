import React, { useState, useEffect } from "react";
import { User, Lock, Sparkles, LogIn, UserPlus, Sun, Moon } from "lucide-react";
import { loginUser, signupUser } from "../services/creativeApi";

interface LoginSignupProps {
  onLoginSuccess: (username: string, userId: string, token: string) => void;
}

export default function LoginSignup({ onLoginSuccess }: LoginSignupProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("contentforge_theme") || "dark";
  });

  useEffect(() => {
    if (theme === "light") {
      document.body.classList.add("light-mode");
    } else {
      document.body.classList.remove("light-mode");
    }
    localStorage.setItem("contentforge_theme", theme);
  }, [theme]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    const cleanUsername = username.trim();
    if (cleanUsername.length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        const response = await loginUser(cleanUsername, password);
        onLoginSuccess(response.username, response.user_id, response.token);
      } else {
        const response = await signupUser(cleanUsername, password);
        onLoginSuccess(response.username, response.user_id, response.token);
      }
    } catch (err: any) {
      console.error("Authentication failed:", err);
      const detail = err.response?.data?.detail;
      setError(
        detail || "Authentication failed. Check your credentials or network."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen w-full flex items-center justify-center relative overflow-hidden font-sans transition-colors duration-500 ${
      theme === "dark" ? "bg-slate-950" : "bg-slate-50"
    }`}>
      {/* Theme Toggle Button */}
      <div className="absolute top-6 right-6 z-20">
        <button
          type="button"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className={`p-3 rounded-full border transition-all duration-300 cursor-pointer ${
            theme === "dark"
              ? "bg-slate-900/50 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              : "bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:border-slate-300 shadow-sm"
          }`}
        >
          {theme === "dark" ? (
            <Sun size={18} className="text-amber-400" />
          ) : (
            <Moon size={18} className="text-indigo-600" />
          )}
        </button>
      </div>

      {/* Dynamic Animated Gradient Mesh Backgrounds */}
      {theme === "dark" ? (
        <>
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black z-0" />
          <div className="absolute top-1/6 left-1/6 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] animate-float-1 z-0" />
          <div className="absolute bottom-1/6 right-1/6 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] animate-float-2 z-0" />
        </>
      ) : (
        <>
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-50/20 via-slate-100/30 to-sky-50/20 z-0" />
          <div className="absolute top-1/6 left-1/6 w-[500px] h-[500px] bg-indigo-300/10 rounded-full blur-[100px] animate-float-1 z-0" />
          <div className="absolute bottom-1/6 right-1/6 w-[500px] h-[500px] bg-sky-200/15 rounded-full blur-[100px] animate-float-2 z-0" />
        </>
      )}

      {/* Floating Glassmorphic Authentication Card */}
      <div className={`w-full max-w-md p-8 backdrop-blur-2xl border rounded-3xl z-10 mx-4 transition-all duration-500 ${
        theme === "dark"
          ? "bg-slate-900/40 border-slate-800/80 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.7)] hover:shadow-[0_25px_70px_-10px_rgba(99,102,241,0.15)] hover:border-indigo-500/20"
          : "bg-white/60 border-slate-200/80 shadow-[0_25px_60px_-15px_rgba(15,23,42,0.06)] hover:shadow-[0_25px_70px_-10px_rgba(99,102,241,0.04)] hover:border-indigo-500/10"
      }`}>
        
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 mb-4 transform hover:rotate-12 transition-transform duration-300">
            <Sparkles size={28} className="text-white animate-pulse" />
          </div>
          <h2 className={`text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r ${
            theme === "dark"
              ? "from-white via-slate-100 to-slate-300"
              : "from-slate-900 via-slate-850 to-slate-950"
          }`}>
            {isLogin ? "Sign In to SocialHQ" : "Join SocialHQ"}
          </h2>
          <p className={`text-sm mt-2 text-center max-w-[280px] leading-relaxed ${
            theme === "dark" ? "text-slate-400" : "text-slate-500"
          }`}>
            {isLogin
              ? "Access your campaigns, analytics & creative studios."
              : "Isolate and secure your campaign content sessions."}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className={`p-4 border rounded-2xl text-xs leading-relaxed animate-fade-in ${
              theme === "dark"
                ? "bg-red-950/40 border-red-500/20 text-red-300"
                : "bg-red-50 border-red-200 text-red-700"
            }`}>
              {error}
            </div>
          )}

          {/* Username Input */}
          <div className="space-y-1.5">
            <label className={`block text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-slate-400" : "text-slate-500"
            }`}>
              Username
            </label>
            <div className="relative group">
              <User
                size={18}
                className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${
                  theme === "dark"
                    ? "text-slate-500 group-focus-within:text-indigo-400"
                    : "text-slate-400 group-focus-within:text-indigo-500"
                }`}
              />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                disabled={loading}
                className={`w-full pl-12 pr-4 py-3.5 border rounded-2xl text-sm transition-all duration-300 disabled:opacity-50 ${
                  theme === "dark"
                    ? "bg-slate-950/40 border-slate-800/80 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                    : "bg-white border-slate-200 text-slate-900 placeholder-slate-450 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                }`}
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-1.5">
            <label className={`block text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-slate-400" : "text-slate-500"
            }`}>
              Password
            </label>
            <div className="relative group">
              <Lock
                size={18}
                className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${
                  theme === "dark"
                    ? "text-slate-500 group-focus-within:text-indigo-400"
                    : "text-slate-400 group-focus-within:text-indigo-500"
                }`}
              />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                className={`w-full pl-12 pr-4 py-3.5 border rounded-2xl text-sm transition-all duration-300 disabled:opacity-50 ${
                  theme === "dark"
                    ? "bg-slate-950/40 border-slate-800/80 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                    : "bg-white border-slate-200 text-slate-900 placeholder-slate-450 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                }`}
              />
            </div>
          </div>

          {/* Confirm Password Input (Signup only) */}
          {!isLogin && (
            <div className="space-y-1.5 animate-slide-down">
              <label className={`block text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-slate-400" : "text-slate-500"
              }`}>
                Confirm Password
              </label>
              <div className="relative group">
                <Lock
                  size={18}
                  className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors ${
                    theme === "dark"
                      ? "text-slate-500 group-focus-within:text-indigo-400"
                      : "text-slate-400 group-focus-within:text-indigo-500"
                  }`}
                />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className={`w-full pl-12 pr-4 py-3.5 border rounded-2xl text-sm transition-all duration-300 disabled:opacity-50 ${
                    theme === "dark"
                      ? "bg-slate-950/40 border-slate-800/80 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                      : "bg-white border-slate-200 text-slate-900 placeholder-slate-450 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  }`}
                />
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:via-indigo-500 hover:to-violet-500 text-white font-semibold text-sm rounded-2xl shadow-[0_4px_20px_rgba(99,102,241,0.25)] hover:shadow-[0_4px_25px_rgba(99,102,241,0.45)] active:scale-[0.98] transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : isLogin ? (
              <>
                <LogIn size={16} />
                <span>Log In</span>
              </>
            ) : (
              <>
                <UserPlus size={16} />
                <span>Sign Up</span>
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className={`w-full border-t ${
              theme === "dark" ? "border-slate-800/60" : "border-slate-200"
            }`} />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className={`px-2 ${
              theme === "dark" ? "bg-slate-900/0 text-slate-500" : "bg-white/0 text-slate-400"
            }`}>Or continue with</span>
          </div>
        </div>

        {/* Toggle Mode */}
        <button
          type="button"
          onClick={() => {
            setIsLogin(!isLogin);
            setError("");
          }}
          disabled={loading}
          className={`w-full text-center text-sm font-semibold transition-colors cursor-pointer disabled:opacity-50 ${
            theme === "dark"
              ? "text-indigo-400 hover:text-indigo-300"
              : "text-indigo-600 hover:text-indigo-500"
          }`}
        >
          {isLogin
            ? "New to SocialHQ? Register a profile"
            : "Already have an account? Sign in here"}
        </button>
      </div>
    </div>
  );
}
