import { useState, useEffect } from "react";
import { getPipelineStatus, provideFeedback } from "../services/api";
import { CheckCircle, Clock } from "lucide-react";

export default function CalendarView() {
  const [state, setState] = useState<any>(null);
  const weekId = "2026-W16"; // Hardcoded for demo

  useEffect(() => {
    getPipelineStatus(weekId).then((data) => setState(data)).catch(() => {});
  }, []);

  const handleApprove = async () => {
    if (!state) return;
    const res = await provideFeedback(weekId, "approve");
    setState(res);
  };

  const isBlocked = state?.human_action_required && state?.human_action_type === "approve_plan";
  const plan = state?.state?.weekly_plan || [];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-slate-800">Weekly Calendar Plan</h2>
        {isBlocked && (
          <button 
            onClick={handleApprove}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-bold shadow-lg shadow-emerald-200 flex gap-2 items-center transition"
          >
            <CheckCircle size={20} />
            Approve Plan & Proceed
          </button>
        )}
      </div>

      <div className="grid grid-cols-7 gap-4">
        {["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].map(day => {
          const item = plan.find((p: any) => p.day === day);
          
          return (
            <div key={day} className="flex flex-col gap-2">
              <h4 className="text-center font-bold text-slate-500 uppercase text-xs tracking-wider border-b border-slate-200 pb-2">
                {day}
              </h4>
              <div className={`bg-white border rounded-lg p-4 min-h-[150px] shadow-sm ${item ? 'border-blue-200' : 'border-slate-100 bg-slate-50 border-dashed'}`}>
                {item ? (
                  <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-mono bg-blue-100 text-blue-800 px-2 py-1 rounded inline-block w-fit">
                      {item.content_format}
                    </span>
                    <h5 className="font-bold text-sm text-slate-800 leading-tight">
                      {item.topic_title}
                    </h5>
                    <p className="text-xs text-slate-500 mt-2 line-clamp-3">
                      {item.content_intent}
                    </p>
                  </div>
                ) : (
                  <div className="flex h-full items-center justify-center text-slate-300">
                    <Clock size={20} />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
