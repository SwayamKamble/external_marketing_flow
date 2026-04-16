import { useState, useEffect } from "react";
import { getPipelineStatus, provideFeedback } from "../services/api";
import { Send, AlertCircle } from "lucide-react";

export default function HumanInLoopChat() {
  const [state, setState] = useState<any>(null);
  const [feedback, setFeedback] = useState("");
  const [isSending, setIsSending] = useState(false);
  const weekId = "2026-W16"; // Hardcoded for demo

  useEffect(() => {
    // Poll or use websocket internally, for demo we just fetch
    const interval = setInterval(() => {
        getPipelineStatus(weekId).then((data) => setState(data)).catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSendFeedback = async () => {
    if (!feedback.trim()) return;
    setIsSending(true);
    await provideFeedback(weekId, "edit", feedback);
    setFeedback("");
    setIsSending(false);
  };
  
  const handleApprove = async () => {
      await provideFeedback(weekId, "approve");
  }

  const isEditingBlocked = state?.human_action_required && state?.human_action_type === "review_content";
  const topicId = state?.pending_topic_id;
  const tc = state?.state?.content?.[topicId];

  return (
    <div className="p-8 max-w-4xl mx-auto flex flex-col h-full">
      <div className="flex justify-between items-center mb-6 border-b pb-4">
        <div>
           <h2 className="text-2xl font-bold flex gap-2 items-center text-slate-800">
             <AlertCircle className="text-amber-500" />
             Content Review & Edit
           </h2>
           <p className="text-sm text-slate-500">
               Topic: <span className="font-mono bg-slate-100 px-2 rounded">{topicId || "None"}</span>
           </p>
        </div>
        {isEditingBlocked && (
            <button 
                onClick={handleApprove}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-6 rounded transition"
            >
                Approve & Export Content
            </button>
        )}
      </div>

      <div className="flex-1 bg-white border rounded-xl overflow-hidden shadow-sm flex flex-col mb-6">
         {/* Simple Chat View */}
         <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-6 bg-slate-50">
             {/* Render generated content preview here if available */}
             {tc && (
                 <div className="bg-white border rounded-lg p-6 shadow-sm">
                     <h3 className="font-bold text-slate-700 mb-4 border-b pb-2 tracking-wide uppercase text-sm">Generated Payload Prototype</h3>
                     <div className="grid grid-cols-2 gap-4">
                         {tc.captions?.instagram && (
                             <div className="bg-slate-50 p-4 border rounded text-sm text-slate-600">
                                 <strong className="text-slate-800 block mb-2">Instagram v1</strong>
                                 <p className="whitespace-pre-wrap">{tc.captions.instagram.v1.caption_text}</p>
                             </div>
                         )}
                         {tc.theme && (
                             <div className="bg-slate-50 p-4 border rounded text-sm text-slate-600">
                                 <strong className="text-slate-800 block mb-2">Theme Design</strong>
                                 <p>Font: {tc.theme.font_heading}</p>
                                 <p>Primary: {tc.theme.primary_color}</p>
                             </div>
                         )}
                     </div>
                 </div>
             )}
         </div>

         {/* Chat Input */}
         <div className="p-4 border-t bg-white flex gap-4 items-center">
             <input 
                 type="text" 
                 value={feedback}
                 onChange={(e) => setFeedback(e.target.value)}
                 disabled={!isEditingBlocked || isSending}
                 placeholder={isEditingBlocked ? "E.g., Make the Instagram caption funnier and use #marketing..." : "Waiting for pipeline to reach editing phase..."}
                 className="flex-1 bg-slate-100 border-none rounded-full px-6 py-3 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                 onKeyDown={(e) => e.key === 'Enter' && handleSendFeedback()}
             />
             <button 
                onClick={handleSendFeedback}
                disabled={!isEditingBlocked || isSending || !feedback.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 disabled:opacity-50 transition"
             >
                 <Send size={20} />
             </button>
         </div>
      </div>
    </div>
  );
}
