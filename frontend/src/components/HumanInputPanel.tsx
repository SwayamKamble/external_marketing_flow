import { useState, useRef, useEffect } from "react";
import { provideFeedback, getArtifact, submitDeepResearchForTopic } from "../services/api";
import { FileUp, FileText, Send, Loader } from "lucide-react";

export default function HumanInputPanel({ weekId, pipelineState, onSubmitted }: { weekId: string, pipelineState: any, onSubmitted: () => void }) {
  const [textInput, setTextInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [promptContent, setPromptContent] = useState<string>("");
  const [copyLabel, setCopyLabel] = useState("Copy Prompt");
  const [submitNote, setSubmitNote] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const actionType = pipelineState?.human_action_type;
  const pipelineStatus = pipelineState?.status;

  const isDeepResearchInterrupt = actionType === "paste_deep_research" || pipelineStatus === "deep_research";
  const isRawResearchInterrupt = actionType === "paste_research" || (!actionType && pipelineStatus === "research");
  const isResearchInterrupt = isRawResearchInterrupt || isDeepResearchInterrupt;
  const pendingTopicId = pipelineState?.pending_topic_id;

  useEffect(() => {
     if (!isResearchInterrupt) return;

     // PRIMARY: Use prompt_content embedded directly in the status response
     const embeddedPrompt = pipelineState?.prompt_content;
     if (embeddedPrompt) {
       console.log("[HumanInputPanel] Using embedded prompt_content from status response");
       setPromptContent(embeddedPrompt);
       return;
     }

     // For deep research, we MUST wait for pendingTopicId before fetching
     if (isDeepResearchInterrupt && !pendingTopicId) {
       console.log("[HumanInputPanel] Waiting for pendingTopicId...");
       setPromptContent("Loading deep research prompt...");
       return;
     }

     // FALLBACK: Try artifact API
     const phase = isDeepResearchInterrupt ? "04_deep_research" : "01_research";
     const preferredName = isDeepResearchInterrupt
       ? `deep_research_prompt_${pendingTopicId}.md`
       : "research_prompts.md";

     console.log(`[HumanInputPanel] Fallback: fetching artifact ${phase}/${preferredName}`);

     getArtifact(weekId, phase, preferredName)
       .then(res => {
         console.log("[HumanInputPanel] Artifact loaded successfully via fallback");
         setPromptContent(res.content);
       })
       .catch(async (err) => {
         console.error(`[HumanInputPanel] Fallback failed for ${phase}/${preferredName}:`, err);
         setPromptContent("Prompt is being generated. Please wait a moment and refresh the page.");
       });
  }, [actionType, weekId, isResearchInterrupt, isDeepResearchInterrupt, pendingTopicId, pipelineState?.prompt_content]);

  const handleSubmit = async () => {
    if (!textInput.trim()) return;
    setIsSubmitting(true);
    setSubmitNote("Submitting... this may take 30-60 seconds for content generation.");
    
    try {
         if (isDeepResearchInterrupt) {
           const topicId = pendingTopicId;
           if (!topicId) {
          throw new Error("Missing pending topic id for deep research submission.");
           }
           await submitDeepResearchForTopic(weekId, topicId, textInput);
        } else {
             // Default to raw_research
             await provideFeedback(weekId, "supply_raw_research", "", { raw_research_data: textInput });
        }
        setTextInput("");
      setSubmitNote("✅ Submitted! AI is generating content in the background. Watch the Dashboard for progress.");
      window.setTimeout(() => setSubmitNote(""), 8000);
        onSubmitted();
    } catch (e: any) {
        console.error("Failed to submit feedback", e);
        const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      setSubmitNote(`Submit failed: ${detail}`);
    } finally {
        setIsSubmitting(false);
    }
  };

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      if (text) {
          setTextInput((prev) => prev + (prev ? "\n\n" : "") + text);
      }
    };
    reader.readAsText(file);
  };

  const onDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleCopyPrompt = async () => {
    if (!promptContent.trim()) return;

    try {
      await navigator.clipboard.writeText(promptContent);
      setCopyLabel("Copied");
      window.setTimeout(() => setCopyLabel("Copy Prompt"), 1500);
    } catch {
      setCopyLabel("Copy Failed");
      window.setTimeout(() => setCopyLabel("Copy Prompt"), 1500);
    }
  };

  if (!isResearchInterrupt && !pipelineState?.human_action_required) return null;

  return (
    <div className="bg-white border-2 border-indigo-200 rounded-xl shadow-lg flex flex-col mt-4 overflow-hidden">
        <div className="bg-indigo-50 border-b border-indigo-100 p-4 font-bold text-indigo-900 flex justify-between items-center">
            <span>Human-in-the-Loop Paused</span>
            <span className="bg-white text-indigo-600 px-3 py-1 rounded-full text-xs uppercase font-mono tracking-wider border border-indigo-200">
                {actionType || "Awaiting Input"}
            </span>
        </div>
        
        <div className="p-6 flex flex-col gap-6">
            {isResearchInterrupt && (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                         <FileText size={18} className="text-blue-500"/> Generated Prompt for External LLM
                      </h4>
                      <button
                        onClick={handleCopyPrompt}
                        disabled={!promptContent.trim()}
                        className="text-xs font-semibold px-3 py-2 rounded border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50"
                      >
                        {copyLabel}
                      </button>
                    </div>
                    <div className="bg-slate-900 text-slate-300 p-4 rounded-lg text-sm font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                        {promptContent || <span className="opacity-50 flex items-center gap-2"><Loader size={14} className="animate-spin"/> Loading...</span>}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Copy this prompt and paste it into ChatGPT or Perplexity, then bring the output down below.</p>
                </div>
            )}
            
            <div className="flex flex-col gap-2">
                 <h4 className="font-semibold text-slate-700">Paste or Upload Results</h4>
                 {submitNote && (
                   <div className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
                     {submitNote}
                   </div>
                 )}
                 <div 
                    className={`relative border-2 border-dashed rounded-lg p-2 transition ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50'}`}
                    onDragEnter={onDrag}
                    onDragLeave={onDrag}
                    onDragOver={onDrag}
                    onDrop={onDrop}
                 >
                     <textarea
                         value={textInput}
                         onChange={(e) => setTextInput(e.target.value)}
                         placeholder="Paste raw markdown output here..."
                         className="w-full h-40 bg-transparent resize-none focus:outline-none p-2 text-sm text-slate-700"
                     />
                     
                     <div className="absolute bottom-4 right-4 flex items-center gap-3">
                         <span className="text-xs text-slate-400 font-medium">or drop a .md file here</span>
                         <input 
                             type="file" 
                             accept=".txt,.md" 
                             ref={fileInputRef} 
                             className="hidden"
                           title="Upload research file"
                           aria-label="Upload research file"
                             onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                         />
                         <button 
                             onClick={() => fileInputRef.current?.click()}
                             className="bg-white border rounded shadow-sm text-slate-600 p-2 hover:bg-slate-50 transition tooltip"
                             title="Upload Markdown File"
                         >
                             <FileUp size={18} />
                         </button>
                         <button 
                             onClick={handleSubmit}
                             disabled={isSubmitting || !textInput.trim()}
                             className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded shadow flex items-center gap-2 transition disabled:opacity-50"
                         >
                             {isSubmitting ? <Loader size={16} className="animate-spin"/> : <Send size={16} />}
                           {isDeepResearchInterrupt ? "Submit Deep Research" : "Submit Research"}
                         </button>
                     </div>
                 </div>
            </div>
        </div>
    </div>
  );
}
