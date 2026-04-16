import { useState, useEffect } from "react";
import { getPipelineStatus, selectTopics } from "../services/api";
import { CheckCircle, Clock } from "lucide-react";

export default function CalendarView() {
  const [state, setState] = useState<any>(null);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const weekId = "2026-W16"; // Hardcoded for demo

  useEffect(() => {
    getPipelineStatus(weekId).then((data) => setState(data)).catch(() => {});
  }, []);

  useEffect(() => {
    const plan = state?.state?.weekly_plan || [];
    const uniqueTopicIds = Array.from(new Set<string>(plan.map((p: any) => p.topic_id).filter(Boolean)));
    const currentSelected = state?.state?.selected_topics || [];
    if (currentSelected.length > 0) {
      setSelectedTopics(currentSelected);
    } else {
      setSelectedTopics(uniqueTopicIds);
    }
  }, [state]);

  const toggleTopic = (topicId: string) => {
    setSelectedTopics((prev) => (
      prev.includes(topicId) ? prev.filter((t) => t !== topicId) : [...prev, topicId]
    ));
  };

  const handleContinue = async () => {
    if (!state) return;
    setIsSubmitting(true);
    try {
      const res = await selectTopics(weekId, selectedTopics);
      setState(res);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isBlocked = state?.human_action_required && ["approve_plan", "select_topics"].includes(state?.human_action_type);
  const plan = state?.state?.weekly_plan || [];
  const uniqueTopics = Array.from(
    new Map(
      plan
        .filter((p: any) => p.topic_id)
        .map((p: any) => [p.topic_id, { id: p.topic_id, title: p.topic_title, format: p.content_format }])
    ).values()
  );

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-slate-800">Weekly Calendar Plan</h2>
        {isBlocked && (
          <button 
            onClick={handleContinue}
            disabled={isSubmitting || selectedTopics.length === 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-bold shadow-lg shadow-emerald-200 flex gap-2 items-center transition disabled:opacity-50"
          >
            <CheckCircle size={20} />
            {isSubmitting ? "Submitting..." : "Use Selected Topics & Proceed"}
          </button>
        )}
      </div>

      {isBlocked && (
        <div className="mb-8 bg-white border border-slate-200 rounded-lg p-4">
          <h3 className="font-semibold text-slate-800 mb-3">Select Topics To Continue</h3>
          <div className="grid md:grid-cols-2 gap-2">
            {uniqueTopics.map((topic: any) => (
              <label key={topic.id} className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 border border-slate-100">
                <input
                  type="checkbox"
                  checked={selectedTopics.includes(topic.id)}
                  onChange={() => toggleTopic(topic.id)}
                />
                <span className="text-sm text-slate-700">{topic.title}</span>
                <span className="ml-auto text-[10px] font-mono bg-blue-100 text-blue-700 px-2 py-1 rounded">{topic.format}</span>
              </label>
            ))}
          </div>
        </div>
      )}

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
