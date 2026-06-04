import { useState, useEffect } from "react";
import { getPipelineStatus, provideFeedback, renderCarouselPreview } from "../services/api";
import { Send, AlertCircle, Loader } from "lucide-react";
import ContentBoilerplate from "./ContentBoilerplate";
import ErrorBoundary from "./ErrorBoundary";

function normalizeSlidesFromDeepResearch(deepItem: any): any[] {
  const spec = deepItem?.content_spec || {};
  const rawSlides = Array.isArray(spec?.slides) ? spec.slides : [];
  return rawSlides
    .filter((s: any) => s && typeof s === "object")
    .map((s: any, idx: number) => ({
      slide_number: Number(s.slide_number) || idx + 1,
      heading: String(s.heading || "").trim(),
      body_text: String(s.body_text || "").trim(),
      visual_concept: String(s.visual_concept || s.image_description || "").trim(),
      image_description: String(s.image_description || "").trim(),
      image_placement: String(s.image_placement || "").trim(),
      heading_font: String(s.heading_font || "").trim(),
      heading_font_weight: String(s.heading_font_weight || "").trim(),
      body_font: String(s.body_font || "").trim(),
      body_font_weight: String(s.body_font_weight || "").trim(),
      slide_theme: s.theme || s.slide_theme || null,
    }))
    .filter((s: any) => {
      const markerBlob = `${s.heading}\n${s.body_text}`.toLowerCase();
      if (!s.heading || !s.body_text) return false;
      if (markerBlob.includes("content generation fallback")) return false;
      if (markerBlob.includes("re-run deep research")) return false;
      return true;
    });
}

export default function HumanInLoopChat({ weekId }: { weekId: string }) {
  const [state, setState] = useState<any>(null);
  const [feedback, setFeedback] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRenderingCarousel, setIsRenderingCarousel] = useState(false);
  const [carouselPreviewImages, setCarouselPreviewImages] = useState<any[]>([]);
  const [carouselError, setCarouselError] = useState("");
  const topicId = state?.pending_topic_id;

  // Find first topic with content if pending_topic_id is null
  const effectiveTopicId = topicId || (state?.state?.content ? Object.keys(state.state.content)[0] : null);

  const [viewingTopicId, setViewingTopicId] = useState<string | null>(null);
  const currentViewTopic = viewingTopicId || effectiveTopicId;

  useEffect(() => {
    // Poll status
    const interval = setInterval(() => {
      getPipelineStatus(weekId).then((data) => setState(data)).catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [weekId]);

  const [iframeHtml, setIframeHtml] = useState<string>("");

  useEffect(() => {
    setCarouselPreviewImages([]);
    setCarouselError("");
    setIframeHtml("");
  }, [currentViewTopic]);

  const handleSendFeedback = async () => {
    if (!feedback.trim()) return;
    setIsSending(true);
    try {
      await provideFeedback(weekId, "edit", feedback);
      setFeedback("");
    } catch (e) {
      console.error("Feedback error:", e);
    } finally {
      setIsSending(false);
    }
  };


  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await provideFeedback(weekId, "approve");
    } catch (e) {
      console.error(e);
    } finally {
      setIsApproving(false);
    }
  };

  const handleRenderCarousel = async () => {
    if (!effectiveTopicId) return;
    setIsRenderingCarousel(true);
    setCarouselError("");
    try {
      const response = await renderCarouselPreview(weekId, effectiveTopicId, iframeHtml);
      setCarouselPreviewImages(response.images || []);
    } catch (e: any) {
      setCarouselError(e?.response?.data?.detail || "Failed to render carousel preview.");
    } finally {
      setIsRenderingCarousel(false);
    }
  };

  const isEditingBlocked = state?.human_action_required && state?.human_action_type === "review_content";

  // All content topics for navigation
  const allContentTopics = state?.state?.content ? Object.keys(state.state.content) : [];
  const currentViewTc = state?.state?.content?.[currentViewTopic];
  const topicTitleById = new Map<string, string>(
    (state?.state?.topic_bank || [])
      .filter((t: any) => t?.id && t?.title)
      .map((t: any) => [t.id, t.title])
  );
  const topicLabel = (tid?: string | null) => (tid ? (topicTitleById.get(tid) || tid) : "None");
  const currentTopicMeta = state?.state?.topic_bank?.find((t: any) => t?.id === currentViewTopic);
  const deepForCurrentTopic = currentViewTopic ? state?.state?.deep_research?.[currentViewTopic] : null;
  const deepSlides = normalizeSlidesFromDeepResearch(deepForCurrentTopic);
  const stateSlides = Array.isArray(currentViewTc?.carousel_slides) ? currentViewTc.carousel_slides : [];
  const effectiveSlides = stateSlides.length > 0 ? stateSlides : deepSlides;

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col h-full">
      <div className="flex justify-between items-center mb-6 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold flex gap-2 items-center text-slate-800">
            <AlertCircle className="text-amber-500" />
            Content Review & Edit
          </h2>
          <p className="text-sm text-slate-500">
            Topic: <span className="bg-slate-100 px-2 rounded">{topicLabel(currentViewTopic)}</span>
          </p>
        </div>
        <div className="flex gap-3">
          {isEditingBlocked && (
            <button
              onClick={handleApprove}
              disabled={isApproving}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-6 rounded transition flex items-center gap-2"
            >
              {isApproving && <Loader size={18} className="animate-spin" />}
              {isApproving ? "Exporting..." : "Approve & Export Content"}
            </button>
          )}
        </div>
      </div>

      {/* Topic Navigation (if multiple topics have content) */}
      {allContentTopics.length > 1 && (
        <div className="flex gap-2 mb-4 flex-wrap">
          {allContentTopics.map((tid: string) => (
            <button
              key={tid}
              onClick={() => setViewingTopicId(tid)}
              className={`text-xs font-mono px-3 py-1.5 rounded-full border transition ${
                currentViewTopic === tid
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-slate-600 border-slate-300 hover:border-blue-400"
              }`}
            >
              {topicLabel(tid)}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 bg-white border rounded-xl overflow-hidden shadow-sm flex flex-col mb-6">
        <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-6 bg-slate-50">
          {/* Content Boilerplate View */}
          {currentViewTc ? (
            <ErrorBoundary>
              <ContentBoilerplate
                weekId={weekId}
                topicId={currentViewTopic || ""}
                topicTitle={currentTopicMeta?.title || ""}
                contentFormat={currentViewTc.content_format || "carousel"}
                theme={currentViewTc.theme || {}}
                slides={effectiveSlides}
                captions={currentViewTc.captions || {}}
                videoScript={currentViewTc.video_script || []}
                renderedCode={currentViewTc.rendered_code || ""}
                onHtmlChange={(html) => setIframeHtml(html)}
              />
            </ErrorBoundary>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <div className="text-center">
                <AlertCircle size={40} className="mx-auto mb-3 text-slate-300" />
                <p className="font-semibold">Waiting for pipeline to generate content...</p>
                <p className="text-sm mt-1">Content will appear here once the AI finishes creating it.</p>
              </div>
            </div>
          )}

          {/* Carousel Render Preview */}
          {currentViewTc?.content_format === "carousel" && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <strong className="text-slate-800">Rendered Carousel Preview</strong>
                <button
                  onClick={handleRenderCarousel}
                  disabled={isRenderingCarousel}
                  className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded text-xs disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isRenderingCarousel && <Loader size={12} className="animate-spin" />}
                  {isRenderingCarousel ? "Rendering..." : "Render Preview"}
                </button>
              </div>

              {carouselError && (
                <div className="text-xs text-red-600 mb-2">{carouselError}</div>
              )}

              {carouselPreviewImages.length > 0 && (
                <div className="grid md:grid-cols-2 gap-3">
                  {carouselPreviewImages.map((img: any) => (
                    <img
                      key={img.filename}
                      src={img.data_url}
                      alt={img.filename}
                      className="w-full rounded border border-slate-200"
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Chat Input */}
        <div className="flex flex-col w-full border-t bg-white">
          {isSending && (
            <div className="px-6 py-2 bg-blue-50 border-b border-blue-100 flex items-center gap-2 text-xs font-semibold text-blue-700 animate-pulse">
              <Loader size={14} className="animate-spin text-blue-600" />
              Applying slide modifications and regenerating previews...
            </div>
          )}
          <div className="p-4 flex gap-4 items-center">
            <input
              type="text"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              disabled={!isEditingBlocked || isSending}
              placeholder={isSending ? "Applying edits..." : (isEditingBlocked ? "E.g., Make the Instagram caption funnier and use #marketing..." : "Waiting for pipeline to reach editing phase...")}
              className="flex-1 bg-slate-100 border-none rounded-full px-6 py-3 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              onKeyDown={(e) => e.key === "Enter" && handleSendFeedback()}
            />
            <button
              onClick={handleSendFeedback}
              disabled={!isEditingBlocked || isSending || !feedback.trim()}
              title="Send feedback"
              aria-label="Send feedback"
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 disabled:opacity-50 transition flex items-center justify-center"
            >
              {isSending ? <Loader size={20} className="animate-spin" /> : <Send size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
