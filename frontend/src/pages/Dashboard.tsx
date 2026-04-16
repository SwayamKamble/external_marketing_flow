import { useEffect, useState } from "react";
import { connectWebSocket, startPipeline, getPipelineStatus } from "../services/api";
import { Play, Activity, CheckCircle, Loader } from "lucide-react";
import HumanInputPanel from "../components/HumanInputPanel";

export default function Dashboard() {
  const [events, setEvents] = useState<any[]>([]);
  const [pipelineState, setPipelineState] = useState<any>(null);
  const [weekId, setWeekId] = useState("2026-W16");
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // Check initial status
    getPipelineStatus(weekId).then((data) => {
      setPipelineState(data);
    }).catch(() => console.log("Pipeline not started yet"));

    const interval = setInterval(() => {
      getPipelineStatus(weekId).then((data) => setPipelineState(data)).catch(() => {});
    }, 3000);

    // Connect to WebSocket tail
    const ws = connectWebSocket((newMsg) => {
      setEvents((prev) => [...prev, newMsg].slice(-50)); // Keep last 50 events
    });

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [weekId]);

  const actionType = pipelineState?.human_action_type;
  const isResearchStage = ["research", "deep_research"].includes(pipelineState?.status);
  const isResearchInputAction = ["paste_research", "paste_deep_research"].includes(actionType) || isResearchStage;
  const selectedTopics = pipelineState?.state?.selected_topics || [];
  const topicQueue = pipelineState?.state?.topic_queue || [];
  const actionHints: Record<string, string> = {
    select_topics: "Select topics in Weekly Calendar, then continue.",
    paste_research: "Paste weekly research results in this panel.",
    paste_deep_research: "Paste deep research for the current pending topic in this panel.",
    review_content: "Review content in Content Review and approve or edit.",
  };
  const nextActionHint = actionType ? actionHints[actionType] : "";

  const formatTimestamp = (timestamp: any) => {
    const parsed = new Date(timestamp ?? "");
    if (Number.isNaN(parsed.getTime())) {
      return "--:--:--";
    }
    return parsed.toLocaleTimeString();
  };

  const normalizeLogEvent = (ev: any) => {
    const data = ev?.data ?? ev?.details ?? ev?.payload ?? {};
    return {
      timestamp: ev?.timestamp,
      level: ev?.level ?? ev?.type ?? "EVENT",
      event: ev?.event ?? ev?.node ?? ev?.name ?? "unknown",
      data,
    };
  };

  const handleStart = async () => {
    setIsRunning(true);
    try {
      await startPipeline(weekId);
      const state = await getPipelineStatus(weekId);
      setPipelineState(state);
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto flex flex-col gap-8 h-full">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Mission Control</h2>
          <p className="text-slate-500 mt-2">Autonomous LangGraph Engine Monitoring</p>
        </div>
        <div className="flex gap-4 items-center">
          <input 
            type="text" 
            value={weekId}
            onChange={(e) => setWeekId(e.target.value)}
            className="border border-slate-300 rounded px-4 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Week ID"
          />
          <button 
            onClick={handleStart}
            disabled={isRunning}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium flex gap-2 items-center transition disabled:opacity-50"
          >
            {isRunning ? <Loader size={18} className="animate-spin" /> : <Play size={18} />}
            Start Pipeline Run
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 items-start">
        {/* State Panel */}
        <div className="col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
          <h3 className="font-semibold text-lg flex gap-2 items-center border-b pb-4">
            <Activity size={20} className="text-blue-500"/> Current Phase
          </h3>
          {pipelineState ? (
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Status</span>
                <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-mono uppercase font-bold tracking-widest">{pipelineState.status}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Pending Topic</span>
                <span className="font-mono text-xs">{pipelineState.pending_topic_id || "None"}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Topic Progress</span>
                <span className="font-mono text-xs">
                  {pipelineState?.state?.topic_index || 0}/{pipelineState?.state?.topic_total || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Wait State</span>
                {pipelineState.human_action_required ? (
                  <span className="text-amber-600 font-bold text-sm bg-amber-50 px-2 rounded border border-amber-200">INTERRUPTED</span>
                ) : (
                  <span className="text-emerald-600 font-bold text-sm flex gap-1 items-center"><CheckCircle size={14}/> CLEAR</span>
                )}
              </div>
              {pipelineState.human_action_required && nextActionHint && (
                <div className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded p-2">
                  Next Step: {nextActionHint}
                </div>
              )}
            </div>
          ) : (
            <div className="text-slate-400 text-sm py-4 text-center">No active state for {weekId}</div>
          )}
          
        </div>

          {/* Live Tail Log + Research Input */}
          <div className="col-span-2 flex flex-col gap-6">
            <div className="bg-slate-900 rounded-xl p-6 shadow-sm flex flex-col gap-4 h-96">
           <h3 className="font-semibold text-lg flex gap-2 items-center border-b border-slate-700 text-slate-100 pb-4">
            <Activity size={20} className="text-emerald-400"/> Live WebSocket Log
          </h3>
          <div className="flex-1 overflow-y-auto font-mono text-xs text-slate-300 flex flex-col gap-2 p-2">
             {events.length === 0 ? (
               <div className="text-slate-500 text-center mt-20">Waiting for events...</div>
             ) : (
                 events.map((rawEvent, idx) => {
                   const ev = normalizeLogEvent(rawEvent);

                   return (
                 <div key={idx} className="flex gap-4 p-2 hover:bg-slate-800 rounded">
                    <span className="text-slate-500 shrink-0">
                        {formatTimestamp(ev.timestamp)}
                    </span>
                    <span className={`font-bold shrink-0 ${ev.level === 'INFO' ? 'text-blue-400' : 'text-amber-400'}`}>
                      [{ev.level}]
                    </span>
                    <span className="shrink-0 w-48 text-purple-400">
                      &lt;{ev.event}&gt;
                    </span>
                    <span className="text-slate-400 truncate">
                        {JSON.stringify(ev.data ?? {})}
                    </span>
                   </div>
                 );
                 })
             )}
          </div>
            </div>

            {pipelineState?.state && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg text-slate-800">Topic Queue</h3>
                  <span className="text-xs text-slate-500 font-mono">{selectedTopics.length} selected</span>
                </div>
                {selectedTopics.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedTopics.map((topicId: string, index: number) => (
                      <span
                        key={topicId}
                        className={`px-3 py-1 rounded-full text-xs font-mono border ${pipelineState.pending_topic_id === topicId ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}
                      >
                        {index + 1}. {topicId}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-slate-500">No topics selected yet.</div>
                )}
                {topicQueue.length > 0 && (
                  <div className="text-xs text-slate-500">
                    Queue order: {topicQueue.join(" → ")}
                  </div>
                )}
              </div>
            )}

            {isResearchInputAction && (
              <HumanInputPanel weekId={weekId} pipelineState={pipelineState} onSubmitted={() => getPipelineStatus(weekId).then(setPipelineState)} />
            )}
          </div>
      </div>
    </div>
  );
}
