import { useState, useEffect } from "react";
import { getPipelineStatus, selectTopics } from "../services/api";
import { CheckCircle, Clock, Loader } from "lucide-react";
import { Link } from "react-router-dom";

export default function CalendarView({ weekId }: { weekId: string }) {
  const [state, setState] = useState<any>(null);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  // Poll status every 3s so the calendar updates in real-time
  useEffect(() => {
    setLoading(true);
    setState(null);

    const fetchStatus = () => {
      getPipelineStatus(weekId)
        .then((data) => {
          setState(data);
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
        });
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [weekId]);

  useEffect(() => {
    const plan = state?.state?.weekly_plan || [];
    const uniqueTopicIds = Array.from(new Set<string>(plan.map((p: any) => p.topic_id).filter(Boolean)));
    const currentSelected = state?.state?.selected_topics || [];
    // Important UX: do NOT auto-select all topics.
    // This allows users to intentionally select only 1 topic to save deep-research time.
    if (currentSelected.length > 0) {
      setSelectedTopics(currentSelected);
      return;
    }
    if (uniqueTopicIds.length > 0 && selectedTopics.length === 0) {
      setSelectedTopics([]);
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
  const isDeepResearchStep = state?.human_action_required && state?.human_action_type === "paste_deep_research";
  const isReviewStep = state?.human_action_required && state?.human_action_type === "review_content";
  const pendingTopicId = state?.pending_topic_id;
  const plan = state?.state?.weekly_plan || [];
  const hasPlan = plan.length > 0;
  const selectedTopicIds = state?.state?.selected_topics || [];
  const showTopicSelection = hasPlan && (isBlocked || selectedTopicIds.length === 0);
  const uniqueTopics = Array.from(
    new Map(
      plan
        .filter((p: any) => p.topic_id)
        .map((p: any) => [p.topic_id, { id: p.topic_id, title: p.topic_title, format: p.content_format }])
    ).values()
  );
  const topicById = new Map(uniqueTopics.map((t: any) => [t.id, t]));
  const pendingTopicTitle = pendingTopicId ? (topicById.get(pendingTopicId)?.title || pendingTopicId) : "(pending)";

  const pipelineStatus = state?.status;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Weekly Calendar Plan</h2>
          <p className="text-slate-500 text-sm mt-1">Week: <span className="font-mono font-bold">{weekId}</span>
            {pipelineStatus && (
              <span className="ml-3 bg-slate-100 text-slate-600 px-2 py-1 rounded text-xs font-mono uppercase">{pipelineStatus}</span>
            )}
          </p>
        </div>
        {showTopicSelection && (
          <button 
            onClick={handleContinue}
            disabled={isSubmitting || selectedTopics.length === 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-bold shadow-lg shadow-emerald-200 flex gap-2 items-center transition disabled:opacity-50"
          >
            {isSubmitting ? <Loader size={20} className="animate-spin" /> : <CheckCircle size={20} />}
            {isSubmitting ? "Submitting..." : "Use Selected Topics & Proceed"}
          </button>
        )}
      </div>

      {/* Loading state */}
      {loading && !state && (
        <div className="flex items-center justify-center h-64 text-slate-400">
          <Loader size={24} className="animate-spin mr-3" />
          <span>Loading pipeline state for {weekId}...</span>
        </div>
      )}

      {/* No pipeline found */}
      {!loading && !state && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
          <p className="text-amber-800 font-semibold">No pipeline found for {weekId}</p>
          <p className="text-sm text-amber-600 mt-2">Go to the Dashboard and click "Start Pipeline Run" first.</p>
          <Link to="/" className="inline-flex items-center bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded mt-4 text-sm font-semibold">
            Go to Dashboard
          </Link>
        </div>
      )}

      {/* Pipeline running but no plan yet */}
      {state && !hasPlan && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 flex items-center gap-4">
          <Loader size={24} className="animate-spin text-blue-600" />
          <div>
            <p className="text-blue-800 font-semibold">Pipeline is processing...</p>
            <p className="text-sm text-blue-600 mt-1">
              Status: <span className="font-mono font-bold">{pipelineStatus}</span>. 
              The weekly plan will appear here once the AI finishes scoring topics and creating the 7-day schedule.
              {pipelineStatus === "research" && " Go to Dashboard to submit the research data."}
            </p>
          </div>
        </div>
      )}

      {showTopicSelection && (
        <div className="mb-8 bg-white border border-slate-200 rounded-lg p-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h3 className="font-semibold text-slate-800">Select Topics To Create Content</h3>
            <span className="text-xs text-slate-500 font-mono">{selectedTopics.length} selected</span>
          </div>
          <p className="text-sm text-slate-500 mb-4">
            Pick only the topics you want the system to move into deep research and content generation.
            You can select just one topic to generate content faster.
          </p>
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

      {!showTopicSelection && (isDeepResearchStep || isReviewStep || (hasPlan && selectedTopicIds.length > 0)) && (
        <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-4 flex flex-col gap-3">
          <h3 className="font-semibold text-blue-900">Next Step</h3>
          {isDeepResearchStep && (
            <p className="text-sm text-blue-800">
              Topics are selected. Continue by opening Dashboard and submitting deep research for pending topic:
              <span className="ml-2 bg-white border border-blue-200 rounded px-2 py-1">{pendingTopicTitle}</span>
            </p>
          )}
          {isReviewStep && (
            <p className="text-sm text-blue-800">
              Content drafts are ready for review. Open Content Review to approve or request edits.
            </p>
          )}
          {!isDeepResearchStep && !isReviewStep && selectedTopicIds.length > 0 && (
            <p className="text-sm text-blue-800">
              Topics have been selected. Go to Dashboard to paste external research for the pending topic and continue the pipeline.
            </p>
          )}
          <div className="flex gap-3">
            <Link
              to="/"
              className="inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-semibold"
            >
              Go to Dashboard
            </Link>
            <Link
              to="/review"
              className="inline-flex items-center bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 px-4 py-2 rounded text-sm font-semibold"
            >
              Go to Content Review
            </Link>
          </div>
        </div>
      )}

      {hasPlan && (
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
      )}
    </div>
  );
}
