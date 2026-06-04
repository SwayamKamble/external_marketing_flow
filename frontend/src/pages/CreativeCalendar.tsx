import { useState, useEffect } from "react";
import {
  Calendar,
  CalendarCheck,
  CheckCircle,
  Clock,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Loader,
  Sparkles,
  Smartphone,
  BookOpen,
  Target,
  FileText,
  AlertCircle
} from "lucide-react";
import { Link } from "react-router-dom";
import {
  listCreativeSessions,
  listQuickSessions,
  getCreativeStatus,
  getQuickStatus
} from "../services/creativeApi";
import { buildDayPrompt } from "./CreativeManager";
import type { SeriesDay, SeriesPlan } from "./CreativeManager";

// Platform Icon Components
const InstagramIcon = ({ className, size = 20 }: { className?: string; size?: number }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    width={size}
    height={size}
  >
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);

const LinkedinIcon = ({ className, size = 20 }: { className?: string; size?: number }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    width={size}
    height={size}
  >
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect width="4" height="12" x="2" y="9" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const TwitterIcon = ({ className, size = 20 }: { className?: string; size?: number }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    width={size}
    height={size}
  >
    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
  </svg>
);

const PLATFORM_ICONS: Record<string, any> = {
  instagram: InstagramIcon,
  linkedin: LinkedinIcon,
  x: TwitterIcon,
};

const PLATFORM_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  instagram: { border: "border-pink-200", bg: "bg-pink-50", text: "text-pink-700" },
  linkedin: { border: "border-blue-200", bg: "bg-blue-50", text: "text-blue-700" },
  x: { border: "border-slate-200", bg: "bg-slate-50", text: "text-slate-700" },
};

export default function CreativeCalendar() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("");
  const [activeSession, setActiveSession] = useState<any>(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [expandedDay, setExpandedDay] = useState<string | number | null>(null);
  const [completedDays, setCompletedDays] = useState<Record<string, boolean>>({});
  const [copiedDay, setCopiedDay] = useState<string | number | null>(null);
  const [copiedType, setCopiedType] = useState<string>("");

  // Load all sessions and filter for approved/finalized ones
  useEffect(() => {
    async function loadSessions() {
      setLoadingList(true);
      try {
        const [standardRes, quickRes] = await Promise.all([
          listCreativeSessions().catch(() => ({ sessions: [] })),
          listQuickSessions().catch(() => ({ sessions: [] }))
        ]);

        const standardApproved = (standardRes.sessions || [])
          .filter((s: any) => s.status === "planned")
          .map((s: any) => ({
            id: s.id,
            title: `Weekly Plan: ${s.week_id} (${s.niche || "AI & Tech"})`,
            type: "standard",
            date: s.created_at,
          }));

        const quickApproved = (quickRes.sessions || [])
          .filter((s: any) => s.status === "finalized" || s.status === "plan_review")
          .map((s: any) => ({
            id: s.id,
            title: `Quick Series: ${s.user_prompt.length > 40 ? s.user_prompt.slice(0, 40) + "..." : s.user_prompt}`,
            type: "quick",
            date: s.created_at,
          }));

        const allApproved = [...standardApproved, ...quickApproved].sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );

        setSessions(allApproved);
        if (allApproved.length > 0) {
          setSelectedSessionId(allApproved[0].id);
        }
      } catch (err) {
        console.error("Failed to load approved sessions", err);
      } finally {
        setLoadingList(false);
      }
    }
    loadSessions();
  }, []);

  // Fetch full details of the selected session
  useEffect(() => {
    if (!selectedSessionId) {
      setActiveSession(null);
      return;
    }

    async function loadSessionDetails() {
      setLoadingSession(true);
      try {
        const isQuick = selectedSessionId.startsWith("qp_");
        let data: any = null;
        if (isQuick) {
          data = await getQuickStatus(selectedSessionId);
        } else {
          data = await getCreativeStatus(selectedSessionId);
        }
        setActiveSession(data);
        setExpandedDay(null);

        // Load completed states from localStorage
        const loadedCompleted: Record<string, boolean> = {};
        const daysList = isQuick ? (data.series_plan?.days || []) : (data.weekly_plan || []);
        daysList.forEach((dayItem: any) => {
          const dayId = isQuick ? dayItem.day_number : dayItem.day;
          const key = `creative_done_${selectedSessionId}_${dayId}`;
          loadedCompleted[dayId] = localStorage.getItem(key) === "true";
        });
        setCompletedDays(loadedCompleted);

      } catch (err) {
        console.error("Failed to fetch session details", err);
      } finally {
        setLoadingSession(false);
      }
    }

    loadSessionDetails();
  }, [selectedSessionId]);

  // Toggle checkbox state and save to localStorage
  const toggleCompleted = (dayId: string | number, e: React.MouseEvent) => {
    e.stopPropagation(); // Avoid expanding card when clicking checkbox
    const newCompleted = !completedDays[dayId];
    const key = `creative_done_${selectedSessionId}_${dayId}`;
    if (newCompleted) {
      localStorage.setItem(key, "true");
    } else {
      localStorage.removeItem(key);
    }
    setCompletedDays((prev) => ({ ...prev, [dayId]: newCompleted }));
  };

  const handleCopyText = (text: string, dayId: string | number, type: string) => {
    navigator.clipboard.writeText(text);
    setCopiedDay(dayId);
    setCopiedType(type);
    setTimeout(() => {
      setCopiedDay(null);
      setCopiedType("");
    }, 2000);
  };

  // Progress Calculations
  const daysArray = activeSession?.series_plan?.days || activeSession?.weekly_plan || [];
  const totalDays = daysArray.length;
  const completedCount = Object.values(completedDays).filter(Boolean).length;
  const progressPercent = totalDays > 0 ? Math.round((completedCount / totalDays) * 100) : 0;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Top Banner */}
      <div className="bg-slate-950 border-b border-slate-800 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-xl">
            <CalendarCheck size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Creative Calendar</h1>
            <p className="text-slate-400 text-sm mt-0.5">Manage and track your approved publishing schedule</p>
          </div>
        </div>

        {/* Dropdown Selector */}
        {sessions.length > 0 && (
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-xl w-full md:w-auto">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">Plan:</span>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="bg-transparent text-white font-bold text-sm focus:outline-none w-full md:w-64 cursor-pointer"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id} className="bg-slate-900 text-slate-200">
                  {s.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
        {loadingList ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
            <Loader className="animate-spin text-emerald-400" size={32} />
            <span className="text-sm font-semibold">Loading your calendars...</span>
          </div>
        ) : sessions.length === 0 ? (
          /* Empty State */
          <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-12 text-center max-w-lg mx-auto mt-12 flex flex-col items-center shadow-2xl">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-full text-slate-400 mb-6">
              <Calendar size={48} className="text-slate-500" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">No Approved Plans Found</h2>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              Once you finish planning and approve a series or weekly strategy in the Creative Manager, the schedule will appear here automatically.
            </p>
            <Link
              to="/creative"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold px-6 py-3 rounded-xl shadow-lg transition duration-200"
            >
              <Sparkles size={18} />
              Open Creative Manager
            </Link>
          </div>
        ) : loadingSession || !activeSession ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
            <Loader className="animate-spin text-emerald-400" size={32} />
            <span className="text-sm font-semibold">Loading schedule details...</span>
          </div>
        ) : (
          /* Loaded Calendar */
          <div className="flex flex-col gap-6">
            {/* Session Stats Header */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl relative overflow-hidden">
              <div className="flex flex-col gap-1 w-full md:w-2/3">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-widest">
                  {selectedSessionId.startsWith("qp_") ? "Quick Series Pipeline" : "Standard Weekly Planner"}
                </span>
                <h2 className="text-xl font-bold text-white tracking-tight mt-1">
                  {selectedSessionId.startsWith("qp_")
                    ? activeSession.user_prompt
                    : `Week Plan: ${activeSession.week_id} (${activeSession.niche})`}
                </h2>
                <div className="flex flex-wrap gap-2.5 mt-3">
                  <span className="bg-slate-900 border border-slate-800 text-slate-300 text-xs px-3 py-1 rounded-full font-semibold">
                    Platform: <span className="text-emerald-400 capitalize">{activeSession.structured_intent?.platform || "Multi"}</span>
                  </span>
                  <span className="bg-slate-900 border border-slate-800 text-slate-300 text-xs px-3 py-1 rounded-full font-semibold">
                    Filter: <span className="text-emerald-400 capitalize">{activeSession.content_filter || "Educational"}</span>
                  </span>
                  <span className="bg-slate-900 border border-slate-800 text-slate-300 text-xs px-3 py-1 rounded-full font-semibold">
                    Total: <span className="text-emerald-400">{totalDays} posts</span>
                  </span>
                </div>
              </div>

              {/* Progress Circle/Bar */}
              <div className="w-full md:w-72 bg-slate-900/60 border border-slate-800/80 rounded-xl p-4.5 flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-slate-400">Publishing Progress</span>
                  <span className="text-emerald-400">{completedCount} / {totalDays} Done ({progressPercent}%)</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-400 to-teal-500 h-full rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Calendar Layout */}
            {selectedSessionId.startsWith("qp_") ? (
              /* Quick Series Timeline Grid */
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(activeSession.series_plan?.days || []).map((day: SeriesDay) => {
                  const isDone = completedDays[day.day_number];
                  const isOpen = expandedDay === day.day_number;
                  const platform = day.platform.toLowerCase() || "instagram";
                  const PlatformIcon = PLATFORM_ICONS[platform] || Smartphone;
                  const colors = PLATFORM_COLORS[platform] || { border: "border-slate-800", bg: "bg-slate-850", text: "text-slate-300" };
                  const dayPrompt = buildDayPrompt(day, activeSession.series_plan as SeriesPlan, platform, selectedSessionId);

                  return (
                    <div
                      key={day.day_number}
                      className={`group border rounded-2xl transition-all duration-300 overflow-hidden cursor-pointer ${
                        isDone
                          ? "bg-slate-950/60 border-emerald-500/20 opacity-70"
                          : isOpen
                          ? "bg-slate-950 border-emerald-500/30 ring-1 ring-emerald-500/20 shadow-lg"
                          : "bg-slate-950/90 border-slate-800 hover:border-slate-700/80 hover:shadow-md"
                      }`}
                      onClick={() => setExpandedDay(isOpen ? null : day.day_number)}
                    >
                      {/* Header */}
                      <div className="p-4 border-b border-slate-900/60 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          {/* Checkbox */}
                          <button
                            onClick={(e) => toggleCompleted(day.day_number, e)}
                            className={`p-1 border rounded-lg transition-all ${
                              isDone
                                ? "bg-emerald-500 border-emerald-500 text-slate-950"
                                : "border-slate-700 hover:border-slate-500 hover:bg-slate-850 text-transparent"
                            }`}
                          >
                            <CheckCircle size={16} className={isDone ? "opacity-100" : "opacity-0"} />
                          </button>

                          <span className="text-sm font-mono font-bold text-slate-400">Day {day.day_number}</span>
                        </div>

                        {/* Platform Badge */}
                        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-bold uppercase tracking-wider ${colors.bg} ${colors.border} ${colors.text}`}>
                          <PlatformIcon size={12} />
                          <span>{platform}</span>
                        </div>
                      </div>

                      {/* Content Overview */}
                      <div className="p-4">
                        <h3 className={`font-bold text-base leading-snug tracking-tight text-white ${isDone ? "line-through text-slate-400" : ""}`}>
                          {day.title}
                        </h3>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="bg-slate-900 text-slate-400 text-[10px] font-mono px-2 py-0.5 rounded border border-slate-850">
                            {day.content_type || "Carousel"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-3 line-clamp-2 leading-relaxed">
                          {day.hook}
                        </p>
                      </div>

                      {/* Expanded Details Drawer */}
                      {isOpen && (
                        <div
                          className="px-4 pb-5 pt-2 border-t border-slate-900/80 bg-slate-950/90 flex flex-col gap-4"
                          onClick={(e) => e.stopPropagation()} // Stop propagation to avoid closing on detail click
                        >
                          <div className="border-t border-slate-900 my-1" />

                          {/* Hook & Goal */}
                          <div className="flex flex-col gap-1">
                            <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1.5"><BookOpen size={12} className="text-emerald-400" /> Hook / Angle</span>
                            <p className="text-xs text-slate-200 bg-slate-900/80 border border-slate-800 p-2.5 rounded-xl font-medium leading-relaxed">{day.hook}</p>
                          </div>

                          <div className="flex flex-col gap-1">
                            <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1.5"><Target size={12} className="text-emerald-400" /> Teaching Goal</span>
                            <p className="text-xs text-slate-200 bg-slate-900/80 border border-slate-800 p-2.5 rounded-xl font-medium leading-relaxed">{day.teaching_goal}</p>
                          </div>

                          {/* Key Points */}
                          {day.key_points && day.key_points.length > 0 && (
                            <div className="flex flex-col gap-2">
                              <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1.5"><AlertCircle size={12} className="text-emerald-400" /> Key Teaching Points</span>
                              <ul className="text-xs text-slate-300 list-disc pl-4.5 flex flex-col gap-1">
                                {day.key_points.map((pt: string, idx: number) => (
                                  <li key={idx}>{pt}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Copy Caption Area */}
                          {day.caption && (
                            <div className="flex flex-col gap-1.5">
                              <div className="flex justify-between items-center">
                                <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1.5"><FileText size={12} className="text-emerald-400" /> Post Caption</span>
                                <button
                                  onClick={() => handleCopyText(day.caption || "", day.day_number, "caption")}
                                  className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-bold"
                                >
                                  {copiedDay === day.day_number && copiedType === "caption" ? (
                                    <>
                                      <Check size={10} /> Copied!
                                    </>
                                  ) : (
                                    <>
                                      <Copy size={10} /> Copy Caption
                                    </>
                                  )}
                                </button>
                              </div>
                              <pre className="text-[11px] font-sans text-slate-300 bg-slate-900 border border-slate-800/80 p-3 rounded-xl max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                                {day.caption}
                              </pre>
                            </div>
                          )}

                          {/* Slide Outline Area */}
                          {day.slide_outline && day.slide_outline.length > 0 && (
                            <div className="flex flex-col gap-1.5">
                              <span className="text-[10px] font-bold uppercase text-slate-400">Carousel Slide Outline</span>
                              <div className="bg-slate-900 border border-slate-850 p-2.5 rounded-xl flex flex-col gap-1.5 max-h-40 overflow-y-auto">
                                {day.slide_outline.map((slide: any, sIdx: number) => (
                                  <div key={sIdx} className="text-[11px] border-b border-slate-800/60 pb-1.5 last:border-0 last:pb-0">
                                    <span className="font-bold text-slate-400">Slide {sIdx + 1}:</span>{" "}
                                    <span className="text-slate-200">{slide.headline || slide.title || "Outline"}</span>
                                    <p className="text-[10px] text-slate-500 mt-0.5">{slide.body_content || slide.text}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Reel Script Area */}
                          {day.script && (
                            <div className="flex flex-col gap-1.5">
                              <div className="flex justify-between items-center">
                                <span className="text-[10px] font-bold uppercase text-slate-400">Video Script</span>
                                <button
                                  onClick={() => handleCopyText(day.script || "", day.day_number, "script")}
                                  className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-bold"
                                >
                                  {copiedDay === day.day_number && copiedType === "script" ? (
                                    <>
                                      <Check size={10} /> Copied!
                                    </>
                                  ) : (
                                    <>
                                      <Copy size={10} /> Copy Script
                                    </>
                                  )}
                                </button>
                              </div>
                              <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 border border-slate-800/80 p-3 rounded-xl max-h-32 overflow-y-auto whitespace-pre-wrap leading-normal">
                                {day.script}
                              </pre>
                            </div>
                          )}

                          {/* Production Prompt Area */}
                          <div className="flex flex-col gap-1.5">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1.5">
                                <Sparkles size={12} className="text-emerald-400" /> Production Prompt
                              </span>
                              <button
                                onClick={() => handleCopyText(dayPrompt, day.day_number, "prompt")}
                                className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-bold"
                              >
                                {copiedDay === day.day_number && copiedType === "prompt" ? (
                                  <>
                                    <Check size={10} /> Copied!
                                  </>
                                ) : (
                                  <>
                                    <Copy size={10} /> Copy Prompt
                                  </>
                                )}
                              </button>
                            </div>
                            <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 border border-slate-800/80 p-3 rounded-xl max-h-36 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                              {dayPrompt}
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* Bottom Toggle Area */}
                      <div className="bg-slate-900/20 py-2.5 px-4 border-t border-slate-900/40 flex items-center justify-center text-xs font-semibold text-slate-400 group-hover:text-slate-300 transition-colors">
                        {isOpen ? (
                          <span className="flex items-center gap-1">Collapse Details <ChevronUp size={14} /></span>
                        ) : (
                          <span className="flex items-center gap-1">View Full Day Details <ChevronDown size={14} /></span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* Standard Weekly Calendar (Monday -> Sunday) */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
                {["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].map((dayName) => {
                  const planItem = (activeSession.weekly_plan || []).find(
                    (p: any) => p.day.toLowerCase() === dayName
                  );

                  if (!planItem) {
                    return (
                      <div key={dayName} className="flex flex-col gap-2 opacity-40">
                        <h4 className="text-center font-bold text-slate-500 uppercase text-xs tracking-wider border-b border-slate-800 pb-2">
                          {dayName}
                        </h4>
                        <div className="bg-slate-950 border border-slate-800 border-dashed rounded-2xl min-h-[160px] flex flex-col items-center justify-center p-4">
                          <Clock size={20} className="text-slate-600 mb-1" />
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Rest Day</span>
                        </div>
                      </div>
                    );
                  }

                  const isDone = completedDays[planItem.day];
                  const isOpen = expandedDay === planItem.day;
                  const platform = planItem.platform.toLowerCase() || "instagram";
                  const PlatformIcon = PLATFORM_ICONS[platform] || Smartphone;
                  const colors = PLATFORM_COLORS[platform] || { border: "border-slate-850", bg: "bg-slate-900", text: "text-slate-300" };

                  return (
                    <div key={dayName} className="flex flex-col gap-2">
                      <h4 className="text-center font-bold text-slate-400 uppercase text-xs tracking-wider border-b border-slate-800 pb-2 flex items-center justify-center gap-1">
                        {isDone && <CheckCircle size={12} className="text-emerald-400" />}
                        <span>{dayName}</span>
                      </h4>

                      <div
                        className={`group border rounded-2xl transition-all duration-300 overflow-hidden cursor-pointer flex flex-col ${
                          isDone
                            ? "bg-slate-950/60 border-emerald-500/20 opacity-70"
                            : isOpen
                            ? "bg-slate-950 border-emerald-500/30 ring-1 ring-emerald-500/20 shadow-lg"
                            : "bg-slate-950/90 border-slate-800 hover:border-slate-700/80 hover:shadow-md"
                        }`}
                        onClick={() => setExpandedDay(isOpen ? null : planItem.day)}
                      >
                        {/* Checkbox + Icon Header */}
                        <div className="p-3.5 border-b border-slate-900/60 flex items-center justify-between gap-2">
                          <button
                            onClick={(e) => toggleCompleted(planItem.day, e)}
                            className={`p-1 border rounded-lg transition-all ${
                              isDone
                                ? "bg-emerald-500 border-emerald-500 text-slate-950"
                                : "border-slate-700 hover:border-slate-500 hover:bg-slate-850 text-transparent"
                            }`}
                          >
                            <CheckCircle size={14} className={isDone ? "opacity-100" : "opacity-0"} />
                          </button>

                          <div className={`flex items-center gap-1 px-2 py-0.5 rounded-lg border text-[10px] font-bold uppercase tracking-wider ${colors.bg} ${colors.border} ${colors.text}`}>
                            <PlatformIcon size={10} />
                            <span>{platform}</span>
                          </div>
                        </div>

                        {/* Title Overview */}
                        <div className="p-3.5 flex-1">
                          <h3 className={`font-bold text-sm leading-tight text-white ${isDone ? "line-through text-slate-400" : ""}`}>
                            {planItem.topic_title}
                          </h3>
                          <div className="flex items-center gap-1.5 mt-1.5">
                            <span className="bg-slate-900 text-slate-400 text-[9px] font-mono px-1.5 py-0.5 rounded border border-slate-850">
                              {planItem.content_format || "Post"}
                            </span>
                            {planItem.date && (
                              <span className="text-[10px] text-slate-500 font-mono">{planItem.date}</span>
                            )}
                          </div>
                        </div>

                        {/* Expandable details drawer */}
                        {isOpen && (
                          <div
                            className="px-3.5 pb-4 pt-1 border-t border-slate-900/80 bg-slate-950/90 flex flex-col gap-3"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="border-t border-slate-900 my-1" />

                            <div className="flex flex-col gap-0.5">
                              <span className="text-[9px] font-bold uppercase text-slate-400 flex items-center gap-1"><BookOpen size={10} className="text-emerald-400" /> Hook / Angle</span>
                              <p className="text-[11px] text-slate-200 bg-slate-900/85 border border-slate-800/80 p-2 rounded-xl leading-normal">{planItem.hook}</p>
                            </div>

                            <div className="flex flex-col gap-0.5">
                              <span className="text-[9px] font-bold uppercase text-slate-400 flex items-center gap-1"><Target size={10} className="text-emerald-400" /> Goal</span>
                              <p className="text-[11px] text-slate-200 bg-slate-900/85 border border-slate-800/80 p-2 rounded-xl leading-normal">{planItem.teaching_goal}</p>
                            </div>

                            {planItem.writing_prompt && (
                              <div className="flex flex-col gap-1">
                                <div className="flex justify-between items-center">
                                  <span className="text-[9px] font-bold uppercase text-slate-400 flex items-center gap-1"><FileText size={10} className="text-emerald-400" /> Writing Prompt</span>
                                  <button
                                    onClick={() => handleCopyText(planItem.writing_prompt, planItem.day, "prompt")}
                                    className="text-[9px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-bold"
                                  >
                                    {copiedDay === planItem.day && copiedType === "prompt" ? (
                                      <>
                                        <Check size={8} /> Copied!
                                      </>
                                    ) : (
                                      <>
                                        <Copy size={8} /> Copy
                                      </>
                                    )}
                                  </button>
                                </div>
                                <pre className="text-[10px] font-sans text-slate-300 bg-slate-900 border border-slate-800/80 p-2 rounded-xl max-h-28 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                                  {planItem.writing_prompt}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Card Toggle Indicator */}
                        <div className="bg-slate-900/10 py-1.5 px-3 border-t border-slate-900/40 flex items-center justify-center text-[10px] font-semibold text-slate-400 group-hover:text-slate-300 transition-colors mt-auto">
                          {isOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
