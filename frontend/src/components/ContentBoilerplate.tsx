import { useState, useRef, useEffect, useCallback } from "react";
import { Download, Upload, X, ChevronRight } from "lucide-react";
import JSZip from "jszip";
import { resolveTheme, themeVars, buildGoogleFontsUrl, normalizeFontName, type ThemeData, type ResolvedTheme } from "./themeUtils";
import { renderCarouselPreview } from "../services/api";


interface SlideData {
  slide_number: number;
  heading: string;
  body_text: string;
  visual_concept?: string;
  image_description?: string;
  image_placement?: string;
  heading_font?: string;
  heading_font_weight?: string;
  body_font?: string;
  body_font_weight?: string;
  slide_theme?: any;
}

interface ContentBoilerplateProps {
  weekId: string;
  topicId: string;
  topicTitle?: string;
  contentFormat: string;
  theme: ThemeData;
  slides: SlideData[];
  captions: any;
  videoScript: any[];
  renderedCode: string;
  onHtmlChange?: (html: string) => void;
}

const BRAND = "@tech_by_pravesh";

function hexToRgba(hex: string, alpha: number): string {
  let clean = (hex || "").trim();
  if (!clean) return `rgba(0,0,0,${alpha})`;
  if (clean.startsWith("#")) {
    clean = clean.slice(1);
  }
  if (clean.length === 3) {
    clean = clean.split("").map((char) => char + char).join("");
  }
  if (clean.length === 6) {
    const r = parseInt(clean.slice(0, 2), 16);
    const g = parseInt(clean.slice(2, 4), 16);
    const b = parseInt(clean.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  if (clean.startsWith("rgb")) {
    return clean;
  }
  return clean;
}

function ensureCompleteSentence(text: string): string {
  const t = (text || "").replace(/\s+/g, " ").trim();
  if (!t) return "";
  const cleaned = t
    .replace(/\b(and|or|but|so|because|as|that|which|with|for|to|of|in|on|at|by|from)\s*$/i, "")
    .trim();
  if (!cleaned) return "";
  return /[.!?]$/.test(cleaned) ? cleaned : `${cleaned}.`;
}

function summarizeByWordsComplete(input: string, maxWords: number): string {
  const t = (input || "").replace(/\s+/g, " ").trim();
  if (!t) return "";
  const words = t.split(" ").filter(Boolean);
  if (words.length <= maxWords) return ensureCompleteSentence(t);
  const trimmed = words.slice(0, maxWords).join(" ").trim();
  const lastStop = Math.max(trimmed.lastIndexOf("."), trimmed.lastIndexOf("!"), trimmed.lastIndexOf("?"));
  if (lastStop >= 18) return ensureCompleteSentence(trimmed.slice(0, lastStop + 1));
  return ensureCompleteSentence(trimmed);
}

function estimateLineCount(text: string, approxCharsPerLine: number): number {
  const t = (text || "").replace(/\s+/g, " ").trim();
  if (!t) return 0;
  return Math.ceil(t.length / Math.max(approxCharsPerLine, 1));
}

function fitToPlaceholderSpace(input: string, heading: string, isFullImage: boolean, isSingle: boolean = false): string {
  const normalized = (input || "").replace(/\s+/g, " ").trim();
  if (!normalized) return "";

  const headingLen = (heading || "").replace(/\s+/g, " ").trim().length;
  // Single posts: up to 6 lines. Carousel: up to 4 lines (3 if full-image).
  const maxLines = isSingle ? 6 : (isFullImage ? 3 : 4);
  const charsPerLine = isSingle ? 44 : (isFullImage ? 30 : 36);
  const headingPenaltyLines = headingLen > 64 ? 2 : headingLen > 40 ? 1 : 0;
  const allowedLines = Math.max(2, maxLines - headingPenaltyLines);

  let maxWords = isSingle ? 55 : (isFullImage ? 18 : 28);
  let candidate = summarizeByWordsComplete(normalized, maxWords);
  let guard = 0;

  while (estimateLineCount(candidate, charsPerLine) > allowedLines && maxWords > 8 && guard < 15) {
    maxWords -= isSingle ? 4 : (isFullImage ? 2 : 3);
    candidate = summarizeByWordsComplete(normalized, maxWords);
    guard += 1;
  }

  return ensureCompleteSentence(candidate);
}

function summarizeForPlaceholder(input: string, heading: string, isFullImage: boolean, isSingle: boolean = false): string {
  const text = (input || "").replace(/\s+/g, " ").trim();
  if (!text) return "";

  const headingPenalty = Math.max(0, ((heading || "").replace(/\s+/g, " ").trim().length - 36));
  const maxSentences = isSingle ? 4 : (isFullImage ? 2 : 3);
  const maxWordsBase = isSingle ? 60 : (isFullImage ? 24 : 36);
  const maxWords = Math.max(isSingle ? 40 : (isFullImage ? 16 : 22), maxWordsBase - Math.floor(headingPenalty / 7));
  const sentenceMatches = text.match(/[^.!?]+[.!?]+/g) || [];
  const picked: string[] = [];
  let usedWords = 0;
  for (const sRaw of sentenceMatches) {
    const s = sRaw.replace(/\s+/g, " ").trim();
    if (!s) continue;
    const sWords = s.split(" ").filter(Boolean).length;
    if (picked.length >= maxSentences || usedWords + sWords > maxWords) break;
    picked.push(s);
    usedWords += sWords;
  }
  if (picked.length > 0) return fitToPlaceholderSpace(picked.join(" "), heading, isFullImage, isSingle);
  return fitToPlaceholderSpace(summarizeByWordsComplete(text, maxWords), heading, isFullImage, isSingle);
}

function fitPlaceholderText(input: string, heading: string, isFullImage: boolean, isSingle: boolean = false): string {
  return fitToPlaceholderSpace(summarizeForPlaceholder(input, heading, isFullImage, isSingle), heading, isFullImage, isSingle);
}

function flattenJsonText(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map((v) => flattenJsonText(v)).filter(Boolean).join(" ");
  if (value && typeof value === "object") {
    return Object.values(value as Record<string, unknown>)
      .map((v) => flattenJsonText(v))
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

function sanitizeSlideText(input: string): string {
  const raw = (input || "").replace(/\s+/g, " ").trim();
  if (!raw) return "";

  if (/^[\[{]/.test(raw)) {
    try {
      const parsed = JSON.parse(raw);
      const flat = flattenJsonText(parsed).replace(/\s+/g, " ").trim();
      if (flat) return flat;
    } catch {
      // Fallback to plain cleanup below.
    }
  }

  const cleaned = raw
    .replace(/"([a-zA-Z0-9_]+)"\s*:\s*/g, "")
    .replace(/([a-zA-Z0-9_]+)\s*:\s*"/g, "")
    .replace(/([a-zA-Z0-9_]+)\s*:\s*(\{|\[)/g, " ")
    .replace(/\b(structured_research|deep_research|body_text|heading|image_description|image_placement|slide_number|visual_concept)\b\s*:?/gi, " ")
    .replace(/([{[\]}])/g, " ")
    .replace(/\\"/g, '"')
    .replace(/(^|[\s,])([a-zA-Z0-9_]+)\s*:\s*(?=[a-zA-Z])/g, " ")
    .replace(/^[\[{"]+/, "")
    .replace(/[\]}"]+$/, "")
    .replace(/\s+/g, " ")
    .trim();

  return cleaned;
}

/* ═══════════════════════════════════════════════════════
   SLIDE CARD — used for BOTH carousel AND single_image
   Theme is applied via CSS custom properties + data attributes
   ═══════════════════════════════════════════════════════ */
function SlideCard({
  slide, c, frameAspectRatio, isLast, showArrow, showSlideNumber, img, onUpload, onRemove, shouldSummarizeForPlaceholder = true, compactSingleLayout = false,
}: {
  slide: SlideData;
  c: ResolvedTheme;
  frameAspectRatio: string;
  isLast: boolean;
  showArrow: boolean;
  showSlideNumber?: boolean;
  img?: string;
  onUpload: (f: File) => void;
  onRemove: () => void;
  shouldSummarizeForPlaceholder?: boolean;
  compactSingleLayout?: boolean;
}) {
  const st = slide.slide_theme;
  const placement = (st?.layout?.image_position || st?.image?.placement || slide.image_placement || "").toLowerCase();
  const hasImageInstruction = Boolean((st?.image?.description || slide.image_description || "").trim());
  const mentionsPlacement = /(background|left|right|center|top|bottom|full)/.test(placement);
  const needsImagePlaceholder = hasImageInstruction && (mentionsPlacement || placement === "");
  const showPlaceholder = compactSingleLayout ? true : needsImagePlaceholder;
  const isFullImage = placement.includes("background") || placement.includes("full") || placement.includes("whole");
  const imageSlotMinHeight = isFullImage ? "160px" : "110px";
  const imageSlotHeight = isFullImage ? "34%" : "26%";
  const headingText = sanitizeSlideText(slide.heading || "");
  const cleanBodyText = sanitizeSlideText(slide.body_text || "");
  const bodyText = (showPlaceholder && shouldSummarizeForPlaceholder)
    ? fitPlaceholderText(cleanBodyText, headingText, isFullImage, compactSingleLayout)
    : cleanBodyText;

  // Per-slide font overrides (fallback to theme-level fonts)
  const slideHeadingFont = slide.heading_font?.trim()
    ? `'${normalizeFontName(slide.heading_font)}', sans-serif`
    : c.hFont;
  const slideBodyFont = slide.body_font?.trim()
    ? `'${normalizeFontName(slide.body_font)}', sans-serif`
    : c.bFont;
  const slideHeadingWeight = slide.heading_font_weight?.trim()
    ? parseInt(slide.heading_font_weight, 10) || 900
    : 900;
  const slideBodyWeight = slide.body_font_weight?.trim()
    ? parseInt(slide.body_font_weight, 10) || undefined
    : undefined;

  // Split layouts (left/right side-by-side)
  const isSplitLeft = placement.includes("left");
  const isSplitRight = placement.includes("right");
  const isSplit = isSplitLeft || isSplitRight;

  const elementPaddingX = isSplit ? "0" : "var(--slide-padding-x, 24px)";

  // Layout positioning orders
  let badgeOrder = 1;
  let headingOrder = 2;
  let dividerOrder = 3;
  let bodyOrder = 4;
  let imageOrder = 5;

  const headlinePos = st?.layout?.headline_position || st?.layout?.component_positions?.heading || "";
  if (headlinePos === "bottom") {
    headingOrder = 4;
    dividerOrder = 5;
    bodyOrder = 2;
  }
  if (placement.includes("top")) {
    imageOrder = 0;
  } else if (placement.includes("bottom")) {
    imageOrder = 6;
  }

  // Font Size Overrides from Slide Visual Hierarchy
  const customHeadingSize = st?.visual_hierarchy?.headline_size;
  let slideHeadingFontSize = "var(--slide-heading-font-size, clamp(22px, 4.2vw, 30px))";
  if (customHeadingSize === "large" || customHeadingSize === "h1") {
    slideHeadingFontSize = "clamp(26px, 4.8vw, 36px)";
  } else if (customHeadingSize === "medium" || customHeadingSize === "h2") {
    slideHeadingFontSize = "clamp(22px, 4.2vw, 30px)";
  } else if (customHeadingSize === "small" || customHeadingSize === "h3") {
    slideHeadingFontSize = "clamp(18px, 3.4vw, 24px)";
  }

  // Font Weight Overrides
  const customHeadingWeight = st?.visual_hierarchy?.headline_weight;
  let slideHeadingWeightOverride = slideHeadingWeight;
  if (customHeadingWeight === "bold" || customHeadingWeight === "900") {
    slideHeadingWeightOverride = 900;
  } else if (customHeadingWeight === "semibold" || customHeadingWeight === "600") {
    slideHeadingWeightOverride = 600;
  } else if (customHeadingWeight === "normal" || customHeadingWeight === "regular" || customHeadingWeight === "400") {
    slideHeadingWeightOverride = 400;
  } else if (customHeadingWeight === "light" || customHeadingWeight === "300") {
    slideHeadingWeightOverride = 300;
  }

  const defaultBodyFontSize = compactSingleLayout
    ? "clamp(13px, 2.2vw, 16px)"
    : (showPlaceholder
        ? "clamp(11px, 1.8vw, 13px)"
        : (showSlideNumber === false ? "clamp(14px, 2.4vw, 17px)" : "clamp(13px, 2.2vw, 15px)"));

  // Heading Highlight logic
  const highlightWords: string[] = Array.isArray(st?.visual_hierarchy?.highlight_words)
    ? st.visual_hierarchy.highlight_words
    : [];
  const highlightColor = st?.visual_hierarchy?.highlight_color || c.acc;

  const renderHeadingText = () => {
    if (!headingText) return "";
    if (highlightWords.length === 0) return headingText;

    const escapedWords = highlightWords
      .map((w: any) => String(w || "").trim())
      .filter(Boolean)
      .map((w: string) => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"));

    if (escapedWords.length === 0) return headingText;

    const pattern = escapedWords.join("|");
    const regex = new RegExp(`\\b(${pattern})\\b`, "gi");
    const parts = headingText.split(regex);

    return parts.map((part, idx) => {
      const isHighlighted = escapedWords.some(
        (w) => w.toLowerCase() === part.toLowerCase()
      );
      return isHighlighted ? (
        <span key={idx} style={{ color: highlightColor, fontWeight: 900 }}>
          {part}
        </span>
      ) : (
        part
      );
    });
  };

  const textColStyle: React.CSSProperties = {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    justifyContent: "center",
    padding: "16px var(--slide-padding-x, 24px)",
    zIndex: 2,
    boxSizing: "border-box",
  };

  const splitImageStyle: React.CSSProperties = {
    width: "45%",
    height: "100%",
    minHeight: "100%",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    boxSizing: "border-box",
    zIndex: 2,
    order: imageOrder,
  };

  const stackedImageStyle: React.CSSProperties = {
    padding: `8px ${elementPaddingX} 0`,
    height: "var(--slide-image-slot-height, " + imageSlotHeight + ")",
    minHeight: "var(--slide-image-slot-min-height, " + imageSlotMinHeight + ")",
    flex: "1 1 auto",
    zIndex: 2,
    order: imageOrder,
  };

  const renderImage = (isSplitImage: boolean) => {
    const imageContainerStyle = isSplitImage ? splitImageStyle : stackedImageStyle;
    const finalImgDesc = st?.image?.description || slide.image_description || "";
    return (
      <div style={imageContainerStyle}>
        {img ? (
          <div style={{
            position: "relative",
            height: "100%",
            minHeight: isSplitImage ? "100%" : "var(--slide-image-slot-min-height, " + imageSlotMinHeight + ")",
            borderRadius: "8px",
            overflow: "hidden"
          }}>
            <img src={img} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <button onClick={onRemove} style={{
              position: "absolute", top: "4px", right: "4px",
              background: "#ef4444", color: "#fff", border: "none",
              borderRadius: "50%", width: "20px", height: "20px",
              display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer",
            }}>
              <X size={10} />
            </button>
          </div>
        ) : (
          <label data-s-upload="" style={{
            height: "100%",
            minHeight: isSplitImage ? "150px" : "var(--slide-image-slot-min-height, " + imageSlotMinHeight + ")",
            borderRadius: "8px",
            borderWidth: "2px", borderStyle: "dashed",
            borderColor: hexToRgba(c.acc, 0.35),
            background: hexToRgba(c.acc, 0.05),
            display: "flex",
            flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            gap: "8px", cursor: "pointer", textAlign: "center", padding: "10px",
            boxSizing: "border-box",
          }}>
            <Upload size={isFullImage ? 18 : 14} style={{ opacity: 0.5 }} />
            <span style={{ fontSize: isFullImage ? "12px" : "11px", opacity: 0.6, lineHeight: 1.35 }}>
              {finalImgDesc}
            </span>
            <input type="file" accept="image/*" style={{ display: "none" }}
              onChange={(e) => { const f = e.target.files?.[0]; if (f) onUpload(f); }}
            />
          </label>
        )}
      </div>
    );
  };

  const badgeContainerStyle = {
    padding: `var(--slide-padding-top, 18px) ${elementPaddingX} 0`,
    flexShrink: 0,
    zIndex: 2,
    order: badgeOrder
  };

  const headingContainerStyle = {
    padding: `16px ${elementPaddingX} 0`,
    flexShrink: 0,
    zIndex: 2,
    order: headingOrder
  };

  const dividerContainerStyle = {
    padding: `12px ${elementPaddingX} 0`,
    flexShrink: 0,
    zIndex: 2,
    order: dividerOrder
  };

  const bodyContainerStyle = {
    padding: `12px ${elementPaddingX} 0`,
    flex: "0 0 auto",
    overflow: "hidden",
    zIndex: 2,
    order: bodyOrder
  };

  const renderBadge = () => showSlideNumber !== false && (
    <div style={badgeContainerStyle}>
      <span data-s-badge="" style={{
        fontSize: "var(--slide-badge-font-size, 10px)",
        fontWeight: 900,
        textTransform: "uppercase",
        letterSpacing: "2.5px",
        padding: "var(--slide-badge-padding, 5px 14px)",
        borderRadius: "4px",
        display: "inline-block",
        background: c.acc,
        color: c.bg,
      }}>
        SLIDE {slide.slide_number}
      </span>
    </div>
  );

  const renderHeading = () => (
    <div style={headingContainerStyle}>
      <div data-s-heading="" style={{
        fontFamily: slideHeadingFont,
        color: c.text,
        fontSize: slideHeadingFontSize,
        fontWeight: slideHeadingWeightOverride,
        lineHeight: 1.12,
        textShadow: "0 2px 8px rgba(0,0,0,0.3)",
        overflowWrap: "anywhere",
        whiteSpace: "normal",
      }}>
        {renderHeadingText()}
      </div>
    </div>
  );

  const renderDivider = () => (
    <div style={dividerContainerStyle}>
      <div data-s-divider="" style={{
        width: "var(--slide-divider-width, 60px)",
        height: "var(--slide-divider-height, 4px)",
        borderRadius: "2px",
        background: c.acc,
      }} />
    </div>
  );

  const renderBody = () => (
    <div style={bodyContainerStyle}>
      <div data-s-body="" style={{
        fontFamily: slideBodyFont,
        fontWeight: slideBodyWeight,
        fontSize: `var(--slide-body-font-size, ${defaultBodyFontSize})`,
        lineHeight: compactSingleLayout ? 1.45 : (showPlaceholder ? 1.35 : 1.55),
        opacity: 0.92,
        overflow: "hidden",
        whiteSpace: "normal",
        overflowWrap: "anywhere",
        display: (showPlaceholder || compactSingleLayout) ? "-webkit-box" : "block",
        WebkitBoxOrient: (showPlaceholder || compactSingleLayout) ? "vertical" as const : undefined,
        WebkitLineClamp: compactSingleLayout ? 6 : (showPlaceholder ? (isFullImage ? 3 : 4) : undefined),
      }}>
        {bodyText}
      </div>
    </div>
  );

  return (
    <div
      data-theme-slide=""
      data-exportable-slide=""
      data-heading-font={slideHeadingFont}
      data-body-font={slideBodyFont}
      data-is-full-image={isFullImage.toString()}
      style={{
        ...themeVars(c),
        background: c.bg,
        color: c.text,
        fontFamily: slideBodyFont,
        width: "100%",
        aspectRatio: frameAspectRatio,
        position: "relative",
        overflow: "hidden",
        borderRadius: "var(--slide-border-radius, 16px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.35)",
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
        paddingBottom: "var(--slide-padding-bottom, 10px)",
      }}
    >
      {/* TOP ACCENT BAR */}
      <div data-s-accent-bar="" style={{
        height: "var(--slide-accent-bar-height, 6px)",
        flexShrink: 0,
        background: `linear-gradient(90deg, ${c.acc}, ${c.pri}, ${c.acc})`,
      }} />

      {/* LEFT ACCENT STRIPE */}
      <div data-s-accent-stripe="" style={{
        position: "absolute", top: 0, left: 0, bottom: 0,
        width: "var(--slide-accent-stripe-width, 5px)",
        zIndex: 5,
        background: c.acc,
      }} />

      {isSplit ? (
        <div style={{ display: "flex", flexDirection: "row", flex: "1 1 auto", overflow: "hidden", width: "100%", height: "100%", boxSizing: "border-box" }}>
          {isSplitLeft && showPlaceholder && renderImage(true)}
          <div style={textColStyle}>
            {renderBadge()}
            {renderHeading()}
            {renderDivider()}
            {renderBody()}
          </div>
          {isSplitRight && showPlaceholder && renderImage(true)}
        </div>
      ) : (
        <>
          {renderBadge()}
          {renderHeading()}
          {renderDivider()}
          {renderBody()}
          {showPlaceholder && renderImage(false)}
        </>
      )}

      {/* DECORATIVE GLOWS */}
      <div data-s-glow-1="" style={{
        position: "absolute", top: "-40px", right: "-40px",
        width: "var(--slide-glow-1-size, 120px)", height: "var(--slide-glow-1-size, 120px)", borderRadius: "50%",
        zIndex: 1, pointerEvents: "none",
        background: `radial-gradient(circle, ${hexToRgba(c.acc, 0.2)} 0%, transparent 70%)`,
      }} />
      <div data-s-glow-2="" style={{
        position: "absolute", bottom: "-30px", left: "-30px",
        width: "var(--slide-glow-2-size, 100px)", height: "var(--slide-glow-2-size, 100px)", borderRadius: "50%",
        zIndex: 1, pointerEvents: "none",
        background: `radial-gradient(circle, ${hexToRgba(c.pri, 0.18)} 0%, transparent 70%)`,
      }} />

      {/* FOOTER CONTROLS */}
      <div style={{
        padding: "10px var(--slide-padding-x, 24px) 0",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "8px",
        flexShrink: 0,
        zIndex: 10,
      }}>
        {showArrow && !isLast ? (
          <div data-s-arrow="" style={{
            width: "var(--slide-arrow-size, 28px)", height: "var(--slide-arrow-size, 28px)", borderRadius: "50%",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 10px rgba(0,0,0,0.4)",
            background: c.acc,
          }}>
            <ChevronRight size={14} style={{ color: c.bg }} strokeWidth={3} />
          </div>
        ) : <div style={{ width: "var(--slide-arrow-size, 28px)" }} />}
        <div style={{ width: "var(--slide-arrow-size, 28px)" }} />
        <div data-s-brand="" style={{
          fontSize: "var(--slide-brand-font-size, 10px)", fontWeight: 700,
          letterSpacing: "0.8px", whiteSpace: "nowrap",
          opacity: 0.85,
          color: hexToRgba(c.text, 0.55),
        }}>
          {BRAND}
        </div>
      </div>
    </div>
  );
}

/* ═════════════════════════════════════════════════════
   MAIN COMPONENT
   ═════════════════════════════════════════════════════ */
export default function ContentBoilerplate({
  weekId,
  topicId,
  topicTitle,
  contentFormat,
  theme,
  slides,
  captions,
  videoScript,
  renderedCode,
  onHtmlChange,
}: ContentBoilerplateProps) {
  const [uploadedImages, setUploadedImages] = useState<Record<number, string>>({});
  const containerRef = useRef<HTMLDivElement | null>(null);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string>("");
  const [manualDownload, setManualDownload] = useState<{ url: string; name: string } | null>(null);

  const [prevTopicId, setPrevTopicId] = useState(topicId);
  if (prevTopicId !== topicId) {
    setPrevTopicId(topicId);
    setUploadedImages({});
    setExportMessage("");
    setManualDownload(null);
  }

  // Synchronize iframe document when renderedCode updates
  useEffect(() => {
    const iframe = iframeRef.current;
    if (iframe && iframe.contentDocument && renderedCode) {
      iframe.contentDocument.open();
      iframe.contentDocument.write(renderedCode);
      iframe.contentDocument.close();
    }
  }, [renderedCode]);

  // Setup message handler to listen for image upload notifications from within the iframe
  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data && e.data.type === 'SLIDE_IMAGE_UPLOADED') {
        const iframe = iframeRef.current;
        const doc = iframe?.contentDocument;
        if (doc?.documentElement && onHtmlChange) {
          const html = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
          onHtmlChange(html);
        }
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onHtmlChange]);

  const handleIframeLoad = () => {
    const iframe = iframeRef.current;
    const doc = iframe?.contentDocument;
    if (doc?.documentElement && onHtmlChange && renderedCode) {
      const html = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
      onHtmlChange(html);
    }
  };

  const c = resolveTheme(theme);

  const isCarousel = contentFormat === "carousel";
  const isReel     = contentFormat === "reel";
  const isSingle   = contentFormat === "single_image" || contentFormat === "news_post";
  const frameAspectRatio = isCarousel ? "1/1" : (isSingle ? "4/5" : "4/5");

  const handleUpload = (n: number, f: File) => setUploadedImages((p) => ({ ...p, [n]: URL.createObjectURL(f) }));
  const removeImg = (n: number) => setUploadedImages((p) => { const u = { ...p }; if (u[n]) { URL.revokeObjectURL(u[n]); delete u[n]; } return u; });

  // Google Fonts — collect from theme AND all per-slide overrides
  useEffect(() => {
    const allFontNames: string[] = [
      theme?.font_heading || "",
      theme?.font_body || "",
    ];
    // Collect per-slide font overrides
    for (const slide of slides) {
      if (slide.heading_font) allFontNames.push(slide.heading_font);
      if (slide.body_font) allFontNames.push(slide.body_font);
    }

    const url = buildGoogleFontsUrl(allFontNames);
    const linkId = "gfont-all-slides";
    let link = document.getElementById(linkId) as HTMLLinkElement | null;
    if (link) {
      link.href = url;
    } else {
      link = document.createElement("link");
      link.id = linkId;
      link.rel = "stylesheet";
      link.href = url;
      document.head.appendChild(link);
    }
  }, [theme?.font_heading, theme?.font_body, slides]);

  const exportAllJPG = useCallback(async () => {
    if (manualDownload?.url) {
      URL.revokeObjectURL(manualDownload.url);
      setManualDownload(null);
    }
    setExporting(true);
    setExportMessage("Requesting high-res server render...");
    try {
      const iframeEl = iframeRef.current;
      let currentHtml = renderedCode;
      const doc = iframeEl?.contentDocument;
      if (doc?.documentElement) {
        currentHtml = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
      }

      const res = await renderCarouselPreview(weekId, topicId, currentHtml);
      const images = res.images || [];
      if (images.length === 0) {
        throw new Error("No images returned by server");
      }

      const zip = new JSZip();
      for (const img of images) {
        const base64Data = img.data_url.split(",")[1];
        zip.file(img.filename.replace(".png", ".jpg"), base64Data, { base64: true });
      }

      const zipBlob = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${topicId}_slides_jpg.zip`;
      setManualDownload({ url, name: a.download });
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        a.remove();
      }, 100);

      setExportMessage(`Exported ${images.length} high-res slide(s) successfully.`);
    } catch (err) {
      console.error("Export all JPG failed:", err);
      setExportMessage("Export failed. Make sure the renderer server is running.");
    } finally {
      setExporting(false);
    }
  }, [manualDownload, topicId, weekId, renderedCode]);

  return (
    <div ref={containerRef} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: 800, fontSize: "18px" }}>
          {contentFormat.replace(/_/g, " ").toUpperCase()}
        </span>
        <button onClick={exportAllJPG} disabled={exporting} style={{
          display: "flex", alignItems: "center", gap: "8px",
          background: c.pri, color: "#fff", padding: "10px 22px",
          borderRadius: "8px", border: "none", fontWeight: 700,
          cursor: "pointer", fontSize: "13px", opacity: exporting ? 0.5 : 1,
        }}>
          <Download size={16} />
          {exporting ? "Preparing ZIP..." : "Export JPG ZIP"}
        </button>
      </div>
      {(exportMessage || manualDownload) && (
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {exportMessage && <span style={{ fontSize: "12px", opacity: 0.85 }}>{exportMessage}</span>}
          {manualDownload && (
            <a
              href={manualDownload.url}
              download={manualDownload.name}
              style={{
                fontSize: "12px",
                fontWeight: 700,
                color: c.pri,
                textDecoration: "underline",
              }}
            >
              Click here if download did not start
            </a>
          )}
        </div>
      )}

      {/* THEME PALETTE */}
      <div data-theme-slide="" style={{
        ...themeVars(c),
        display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap",
        borderRadius: "10px", padding: "10px 16px",
        border: `2px solid ${c.acc}44`,
      }}>
        <span style={{ fontSize: "9px", fontWeight: 900, textTransform: "uppercase", letterSpacing: "2px", color: c.acc }}>THEME</span>
        {[
          { clr: c.bg, l: "BG" }, { clr: c.text, l: "Text" }, { clr: c.pri, l: "Pri" },
          { clr: c.sec, l: "Sec" }, { clr: c.acc, l: "Acc" },
        ].map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <div style={{ width: "14px", height: "14px", borderRadius: "3px", background: s.clr, border: "1px solid rgba(255,255,255,0.2)" }} />
            <span style={{ fontSize: "9px", fontFamily: "monospace", opacity: 0.7 }}>{s.l}:{s.clr}</span>
          </div>
        ))}
      </div>

      {/* ═══════ CAROUSEL ═══════ */}
      {isCarousel && (slides || []).length > 0 && (
        renderedCode ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", alignItems: "center" }}>
            <div style={{
              fontSize: "13px",
              color: "#64748b",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              padding: "12px 18px",
              borderRadius: "8px",
              width: "100%",
              boxSizing: "border-box",
              lineHeight: "1.5"
            }}>
              💡 <strong>Interactive Slide Preview:</strong> Click inside the image placeholders in the preview below to upload images directly. You can also manually edit the <code>data/exports/{topicId}/slides.html</code> file on disk, then click <strong>Render Preview</strong> to update the final screenshots.
            </div>
            
            <div style={{
              width: "100%",
              maxWidth: "520px",
              aspectRatio: "4 / 5",
              position: "relative",
              overflow: "hidden",
              borderRadius: "24px",
              border: "12px solid #1e293b",
              boxShadow: "0 25px 50px -12px rgba(0,0,0,0.25)",
              background: "#f1f5f9",
            }}>
              <iframe
                ref={iframeRef}
                onLoad={handleIframeLoad}
                style={{
                  width: "1080px",
                  height: "1350px",
                  border: "none",
                  transform: "scale(0.463)", /* 500 / 1080 */
                  transformOrigin: "top left",
                  overflowY: "auto",
                  position: "absolute",
                  top: 0,
                  left: 0,
                }}
                title="Slides Live Preview"
              />
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "24px" }}>
            {(slides || []).filter(Boolean).map((slide, idx) => (
              <SlideCard
                key={slide.slide_number} slide={slide} c={c} frameAspectRatio={frameAspectRatio}
                isLast={idx === slides.length - 1} showArrow={true} showSlideNumber={true}
                shouldSummarizeForPlaceholder={true}
                img={uploadedImages[slide.slide_number]}
                onUpload={(f) => handleUpload(slide.slide_number, f)}
                onRemove={() => removeImg(slide.slide_number)}
              />
            ))}
          </div>
        )
      )}

      {/* ═══════ SINGLE IMAGE — same as carousel slide ═══════ */}
      {isSingle && (
        renderedCode ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", alignItems: "center" }}>
            <div style={{
              fontSize: "13px",
              color: "#64748b",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              padding: "12px 18px",
              borderRadius: "8px",
              width: "100%",
              boxSizing: "border-box",
              lineHeight: "1.5"
            }}>
              💡 <strong>Interactive Slide Preview:</strong> Click inside the image placeholders in the preview below to upload images directly. You can also manually edit the <code>data/exports/{topicId}/slides.html</code> file on disk, then click <strong>Render Preview</strong> to update the final screenshots.
            </div>
            
            <div style={{
              width: "100%",
              maxWidth: "520px",
              aspectRatio: "4 / 5",
              position: "relative",
              overflow: "hidden",
              borderRadius: "24px",
              border: "12px solid #1e293b",
              boxShadow: "0 25px 50px -12px rgba(0,0,0,0.25)",
              background: "#f1f5f9",
            }}>
              <iframe
                ref={iframeRef}
                onLoad={handleIframeLoad}
                style={{
                  width: "1080px",
                  height: "1350px",
                  border: "none",
                  transform: "scale(0.463)", /* 500 / 1080 */
                  transformOrigin: "top left",
                  overflowY: "auto",
                  position: "absolute",
                  top: 0,
                  left: 0,
                }}
                title="Slides Live Preview"
              />
            </div>
          </div>
        ) : (
          <div style={{ maxWidth: "380px" }}>
            <SlideCard
              slide={slides?.[0] || { slide_number: 1, heading: topicTitle || topicId.replace(/[_-]/g, " "), body_text: "Content will appear after generation." }}
              c={c} frameAspectRatio={frameAspectRatio} isLast={true} showArrow={false} showSlideNumber={false}
              shouldSummarizeForPlaceholder={true}
              compactSingleLayout={true}
              img={uploadedImages[1]}
              onUpload={(f) => handleUpload(1, f)}
              onRemove={() => removeImg(1)}
            />
          </div>
        )
      )}

      {/* ═══════ REEL SCRIPT ═══════ */}
      {isReel && (
        <div
          data-theme-slide=""
          data-exportable-slide=""
          style={{
            ...themeVars(c),
            background: c.bg,
            color: c.text,
            fontFamily: c.bFont,
            borderRadius: "16px", overflow: "hidden",
            boxShadow: "0 8px 32px rgba(0,0,0,0.35)",
            position: "relative",
          }}
        >
          <div data-s-accent-bar="" style={{ height: "6px", background: `linear-gradient(90deg, ${c.acc}, ${c.pri}, ${c.acc})` }} />
          <div data-s-accent-stripe="" style={{ position: "absolute", top: 0, left: 0, bottom: 0, width: "5px", background: c.acc }} />

          <div style={{ padding: "28px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
              <div data-s-heading="" style={{ fontFamily: c.hFont, color: c.text, fontSize: "24px", fontWeight: 900 }}>
                Reel Script
              </div>
              <span data-s-badge="" style={{
                fontSize: "10px", fontWeight: 900, textTransform: "uppercase",
                letterSpacing: "2.5px", padding: "5px 14px", borderRadius: "4px",
                background: c.acc,
                color: c.bg,
              }}>
                REEL
              </span>
            </div>

            {videoScript && videoScript.length > 0 ? (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "0 4px" }}>
                  <thead>
                    <tr>
                      {["Timestamp", "Visual / B-Roll", "What to Say (Script)"].map((h, i) => (
                        <th key={i} style={{
                          padding: "12px 16px", textAlign: "left",
                          fontSize: "11px", fontWeight: 900, color: c.acc,
                          textTransform: "uppercase", letterSpacing: "1.5px",
                          borderBottom: `3px solid ${c.acc}`,
                          background: hexToRgba(c.pri, 0.08),
                        }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {videoScript.map((scene: any, idx: number) => (
                      <tr key={idx}>
                        <td style={{
                          padding: "14px 16px", fontSize: "14px", fontWeight: 800,
                          color: c.acc, background: hexToRgba(c.acc, 0.07),
                          borderLeft: `3px solid ${c.acc}`,
                          whiteSpace: "nowrap", verticalAlign: "top",
                        }}>
                          {scene.time || scene.timestamp || `0:${String(idx * 5).padStart(2, "0")}`}
                        </td>
                        <td style={{
                          padding: "14px 16px", fontSize: "13px",
                          background: hexToRgba(c.pri, 0.03), lineHeight: 1.6, verticalAlign: "top",
                        }}>
                          {scene.visual || scene.visuals || scene.b_roll || "—"}
                        </td>
                        <td style={{
                          padding: "14px 16px", fontSize: "13px",
                          background: hexToRgba(c.pri, 0.03), lineHeight: 1.6,
                          verticalAlign: "top", fontStyle: "italic",
                        }}>
                          "{scene.audio || scene.spoken || scene.dialogue || scene.narration || "—"}"
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{
                padding: "48px 20px", textAlign: "center",
                background: hexToRgba(c.pri, 0.05), borderRadius: "12px",
                border: `2px dashed ${hexToRgba(c.acc, 0.2)}`,
              }}>
                <div style={{ color: c.acc, fontSize: "16px", fontWeight: 700, marginBottom: "8px" }}>
                  Reel Script Generating...
                </div>
                <div style={{ opacity: 0.5, fontSize: "13px" }}>
                  The AI is writing your video script.
                </div>
              </div>
            )}

            <div data-s-brand="" style={{
              textAlign: "center", marginTop: "20px",
              fontSize: "10px", fontWeight: 700, letterSpacing: "0.8px",
              color: hexToRgba(c.text, 0.55),
            }}>
              {BRAND}
            </div>
          </div>
        </div>
      )}

      {/* CAPTIONS */}
      {captions && typeof captions === "object" && Object.keys(captions).length > 0 && (
        <div data-theme-slide="" style={{
          ...themeVars(c),
          borderRadius: "14px", padding: "24px",
          border: `1px solid ${c.acc}22`,
        }}>
          <div style={{
            fontWeight: 800, color: c.acc,
            marginBottom: "16px", borderBottom: `2px solid ${c.acc}33`,
            paddingBottom: "10px", fontSize: "16px",
          }}>
            Captions
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "14px" }}>
            {Object.entries(captions).map(([platform, variants]: [string, any]) => (
              <div key={platform} style={{
                background: `${c.pri}12`, border: `1px solid ${c.pri}22`,
                borderRadius: "10px", padding: "16px",
              }}>
                <span style={{
                  fontSize: "10px", fontWeight: 900, textTransform: "uppercase",
                  letterSpacing: "2px", color: c.acc, display: "block", marginBottom: "10px",
                }}>
                  {platform}
                </span>
                {variants && typeof variants === "object" && Object.entries(variants).map(([variant, data]: [string, any]) => {
                  const isObj = data && typeof data === "object";
                  const captionText = isObj ? data.caption_text : (typeof data === "string" ? data : JSON.stringify(data));
                  const cta = isObj ? data.cta : null;
                  const hashtags = isObj ? data.hashtags : null;

                  return (
                    <div key={variant} style={{ marginTop: "12px", borderTop: `1px dashed ${c.pri}22`, paddingTop: "8px" }}>
                      <span style={{ fontSize: "9px", fontFamily: "monospace", opacity: 0.5, textTransform: "uppercase" }}>{variant}</span>
                      <div style={{ fontSize: "12px", whiteSpace: "pre-wrap", marginTop: "4px", lineHeight: 1.5, opacity: 0.85 }}>
                        {captionText}
                      </div>
                      {cta && (
                        <div style={{ fontSize: "12px", fontStyle: "italic", marginTop: "6px", opacity: 0.85, color: c.acc }}>
                          {cta}
                        </div>
                      )}
                      {hashtags && Array.isArray(hashtags) && hashtags.length > 0 && (
                        <div style={{ fontSize: "11px", marginTop: "6px", opacity: 0.8, color: c.pri, display: "flex", flexWrap: "wrap", gap: "4px" }}>
                          {hashtags.map((tag: string, i: number) => (
                            <span key={i} style={{ background: `${c.acc}15`, padding: "2px 6px", borderRadius: "4px", fontSize: "10px" }}>
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
