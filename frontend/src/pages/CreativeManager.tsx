import { useState, useEffect, useRef } from "react";
import {
  Sparkles, Copy, Check, BookOpen, Target,
  Calendar, Download, Zap, ArrowRight, ArrowLeft, Loader, ChevronRight, ChevronLeft,
  MessageSquare, Send, ChevronDown, ChevronUp, Wand2,
  Search, TrendingUp, GraduationCap, Newspaper, Flame,
} from "lucide-react";
import {
  startCreativeSession,
  submitCreativeResearch,
  selectCreativeTopics,
  planCreativeWeek,
  getCreativeStatus,
  listCreativeSessions,
  startQuickSession,
  submitQuickTopics,
  selectQuickTopic,
  submitQuickResearch,
  chatQuickEdit,
  approveQuickPlan,
  getQuickStatus,
  listQuickSessions,
} from "../services/creativeApi";

// â”€â”€ Custom SVG Brand Icons â”€â”€
const InstagramIcon = (props: any) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={props.className || ""}
    style={props.style || {}}
    width={props.size || 24}
    height={props.size || 24}
  >
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);

const LinkedinIcon = (props: any) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={props.className || ""}
    style={props.style || {}}
    width={props.size || 24}
    height={props.size || 24}
  >
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect width="4" height="12" x="2" y="9" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const TwitterIcon = (props: any) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={props.className || ""}
    style={props.style || {}}
    width={props.size || 24}
    height={props.size || 24}
  >
    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
  </svg>
);

// â”€â”€ Types â”€â”€
interface EngagementScores {
  shareability: number;
  saveability: number;
  likeability: number;
  conversation: number;
  virality: number;
  educational_value: number;
  overall: number;
}

interface PlatformAngle {
  platform: string;
  hook: string;
  angle: string;
  format: string;
  teaching_approach: string;
  estimated_engagement: string;
}

interface Topic {
  id: string;
  title: string;
  summary: string;
  category: string;
  source: string;
  educational_angle: string;
  why_it_works: string;
  teaching_points: string[];
  best_platforms: string[];
  engagement_scores: EngagementScores;
  platform_angles: PlatformAngle[];
  selected: boolean;
}

interface DayPlan {
  id?: number;
  day: string;
  date: string;
  platform: string;
  topic_id: string;
  topic_title: string;
  content_format: string;
  intent: string;
  hook: string;
  angle: string;
  teaching_goal: string;
  reasoning: string;
  writing_prompt?: string;
}

// Quick Prompt types
interface SeriesDay {
  day_number: number;
  title: string;
  platform: string;
  content_type: string;
  hook: string;
  angle: string;
  teaching_goal: string;
  key_points: string[];
  talking_points: string[];
  slide_outline: any[];
  script: string;
  caption: string;
  cta: string;
  notes: string;
}

interface SeriesPlan {
  intent: any;
  days: SeriesDay[];
  status: string;
  chat_history: { role: string; message: string }[];
}

// interface StructuredIntent {
//   series_length: number;
//   content_filter: string;
//   topic_theme: string;
//   sub_topics: string[];
//   target_audience: string;
//   platform_preferences: string[];
//   content_styles: string[];
//   educational_goals: string[];
//   difficulty_level: string;
//   raw_prompt: string;
// }

interface DiscoveredTopic {
  id: string;
  title: string;
  summary: string;
  why_trending: string;
  relevance_score: number;
  suggested_angles: string[];
  target_audience: string;
  category: string;
}

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  linkedin: "#0A66C2",
  x: "#1DA1F2",
};

const PLATFORM_ICONS: Record<string, any> = {
  instagram: InstagramIcon,
  linkedin: LinkedinIcon,
  x: TwitterIcon,
};

const PLATFORM_LABELS: Record<string, string> = {
  instagram: "Instagram",
  linkedin: "LinkedIn",
  x: "X (Twitter)",
};

const CATEGORY_EMOJIS: Record<string, string> = {
  "how-to": "",
  concept: "",
  framework: "",
  tool: "",
  "myth-buster": "",
  "case-study": "",
  "cheat-sheet": "",
  "behind-the-scenes": "",
  "trend-analysis": "",
  career: "",
};

// Series theme presets - each series gets a unique visual identity
const SERIES_THEMES = [
  { name: "aurora", pri: "#8b5cf6", sec: "#06b6d4", acc: "#c084fc", border: "#8b5cf6", badgeBg: "rgba(139,92,246,0.15)", badgeText: "#c084fc", gradient: "from-violet-600 to-cyan-500" },
  { name: "ember", pri: "#f97316", sec: "#ef4444", acc: "#fbbf24", border: "#f97316", badgeBg: "rgba(249,115,22,0.15)", badgeText: "#fdba74", gradient: "from-orange-500 to-red-500" },
  { name: "forest", pri: "#10b981", sec: "#84cc16", acc: "#34d399", border: "#10b981", badgeBg: "rgba(16,185,129,0.15)", badgeText: "#6ee7b7", gradient: "from-emerald-500 to-lime-500" },
  { name: "ocean", pri: "#3b82f6", sec: "#0891b2", acc: "#60a5fa", border: "#3b82f6", badgeBg: "rgba(59,130,246,0.15)", badgeText: "#93c5fd", gradient: "from-blue-500 to-teal-500" },
  { name: "sunset", pri: "#f59e0b", sec: "#ec4899", acc: "#fcd34d", border: "#f59e0b", badgeBg: "rgba(245,158,11,0.15)", badgeText: "#fde68a", gradient: "from-amber-500 to-pink-500" },
  { name: "neon", pri: "#a3e635", sec: "#d946ef", acc: "#bef264", border: "#a3e635", badgeBg: "rgba(163,230,53,0.15)", badgeText: "#bef264", gradient: "from-lime-400 to-fuchsia-500" },
  { name: "midnight", pri: "#6366f1", sec: "#475569", acc: "#818cf8", border: "#6366f1", badgeBg: "rgba(99,102,241,0.15)", badgeText: "#a5b4fc", gradient: "from-indigo-500 to-slate-600" },
  { name: "coral", pri: "#fb7185", sec: "#fdba74", acc: "#fda4af", border: "#fb7185", badgeBg: "rgba(251,113,133,0.15)", badgeText: "#fda4af", gradient: "from-rose-400 to-orange-300" },
];

function getSeriesTheme(sessionId: string | null): typeof SERIES_THEMES[0] {
  if (!sessionId) return SERIES_THEMES[0];
  let hash = 0;
  for (let i = 0; i < sessionId.length; i++) {
    hash = ((hash << 5) - hash + sessionId.charCodeAt(i)) | 0;
  }
  return SERIES_THEMES[Math.abs(hash) % SERIES_THEMES.length];
}

function buildDayPrompt(day: SeriesDay, plan: SeriesPlan, platform: string, qpSessionId: string | null): string {
  const intent = plan.intent || {} as any;
  const topic = intent.topic_theme || "AI & Tech";
  const audience = intent.target_audience || "AI enthusiasts, developers, tech professionals";
  const difficulty = intent.difficulty_level || "intermediate";
  const totalDays = plan.days?.length || 1;

  const theme = getSeriesTheme(qpSessionId);

  // Provide specific styling instructions based on the selected series theme
  let themeDescription = "";
  if (theme.name === "aurora" || theme.name === "midnight" || theme.name === "ocean") {
    themeDescription = `Modern high-tech and software theme. Dark backgrounds, sleek glowing card borders using ${theme.pri}, soft neon accents using ${theme.acc}, and readable modern body text. Ideal for tech, AI, development, and engineering topics.`;
  } else if (theme.name === "ember" || theme.name === "sunset") {
    themeDescription = `Warm, energetic, and high-impact theme. Dark slate backgrounds with orange, pink, or amber accents. Card components have solid warm borders using ${theme.pri}. Dynamic gradients using ${theme.gradient}. Ideal for business, productivity, marketing, and motivational topics.`;
  } else if (theme.name === "forest") {
    themeDescription = `Organic, fresh, and modern theme. Emerald/lime/green gradients. Green accent elements. Very clean and fresh developer terminal or sustainability feel. Ideal for coding tutorials, clean architecture, finance, or nature-inspired tech.`;
  } else if (theme.name === "neon") {
    themeDescription = `Futuristic cyberpunk neon theme. Lime/fuchsia accents. High energy, dark/neon contrast. Ideal for bleeding-edge technology, web3, AI, game dev, and creative design.`;
  } else {
    // coral
    themeDescription = `Modern friendly and creative theme. Rose and orange soft colors. Warm, premium, very accessible and visual. Ideal for design, user experience, product management, and creative strategy.`;
  }

  // Compute next day info to display in CTA
  const nextDayNum = day.day_number + 1;
  const nextDay = plan.days?.find(d => d.day_number === nextDayNum);
  let nextDayInfo = "";
  if (nextDay) {
    nextDayInfo = `Stay tuned for Day ${nextDayNum}: ${nextDay.title || nextDay.hook || "the next part of this series!"}`;
  } else {
    nextDayInfo = `This concludes the series! Stay tuned for more educational content.`;
  }

  // Build detailed slide-by-slide section with full content
  let detailedSlides = "";
  if (day.slide_outline && day.slide_outline.length > 0) {
    const outlineSlides = [...day.slide_outline];
    const keyPoints = day.key_points || [];
    let paddingIdx = 0;

    // We want at least 5 slides in total. Since a CTA slide is appended if not present,
    // we need the outline to have at least 4 slides. If it has less, we pad it.
    while (outlineSlides.length < 4 && paddingIdx < keyPoints.length) {
      outlineSlides.push({
        slide_number: outlineSlides.length + 1,
        slide_title: `Core Concept: ${keyPoints[paddingIdx].split(" ").slice(0, 5).join(" ")}`,
        slide_content: keyPoints[paddingIdx],
        visual_concept: "Diagram or themed card visualizing this key teaching point.",
      });
      paddingIdx++;
    }

    // If still less than 4, add a summary slide
    if (outlineSlides.length < 4) {
      outlineSlides.push({
        slide_number: outlineSlides.length + 1,
        slide_title: "Key Takeaway",
        slide_content: day.teaching_goal || "Understand the core mechanism and apply it in your daily workflow.",
        visual_concept: "Summary highlight badge with main actionable takeaway.",
      });
    }

    // Clip to maximum 7 slides so with the CTA slide appended it is at most 8 slides
    const limitedOutline = outlineSlides.slice(0, 7);

    detailedSlides = limitedOutline.map((s: any, idx: number) => {
      const num = s.slide_number || idx + 1;
      const title = s.slide_title || `Slide ${num}`;
      const content = s.slide_content || "";
      const visual = s.visual_cue || s.visual_concept || "";
      const tpContext = day.talking_points && day.talking_points[idx] ? day.talking_points[idx] : "Detailed walkthrough and implementation steps of this concept.";
      return `### Slide ${num}: ${title}
- **Heading**: ${title}
- **Body Content**: ${content}
- **Visual Concept**: ${visual || "Use a relevant diagram, icon set, or illustration that supports the teaching point"}
- **Layout**: ${num === 1 ? "Cover slide - large bold title centered, subtitle below, brand handle at top" : num === limitedOutline.length ? "CTA slide - clear action text centered, follow/save prompt, brand handle" : "Teaching slide - heading top 20%, body content center, visual element fills 40-60% of canvas"}
- **Slide Explanation & Rationale**: ${tpContext}`;
    }).join("\n\n");

    // Ensure there is always a CTA slide at the end of detailedSlides
    const lastSlideIsCta = limitedOutline.some(s => s.slide_title?.toLowerCase().includes("cta") || s.slide_title?.toLowerCase().includes("action") || s.slide_title?.toLowerCase().includes("follow"));
    if (!lastSlideIsCta) {
      const ctaNum = limitedOutline.length + 1;
      const finalCta = `### Slide ${ctaNum}: Call to Action
- **Purpose**: Direct user engagement and conversion.
- **Heading**: ${day.cta || "Save for Later"}
- **Body Content**: Follow @tech_by_pravesh | Share this post with someone | Save to read again
- **Next Day Preview**: ${nextDayInfo}
- **Visual Concept**: Large, bold call-to-action buttons styled with the theme accent color (${theme.acc}), accompanied by social handle badges.
- **Layout**: CTA slide layout with action items centered in the main visual canvas.
- **Slide Explanation & Rationale**: Conversion zone. Directs the user to take action (save/follow/comment) and teases the next topic: "${nextDayInfo}".`;
      detailedSlides += "\n\n" + finalCta;
    }
  } else {
    // Generate detailed slide structure from key points & talking points
    const kps = day.key_points || [];
    const tps = day.talking_points || [];

    // We want total slides to be between 5 and 8.
    // Total slides = Cover (1) + Problem (2) + finalKps.length + Summary (1) + CTA (1) = 5 + finalKps.length - 1
    // To make total slides >= 5, finalKps.length must be >= 1.
    // To make total slides <= 8, finalKps.length must be <= 4.
    const paddedKps = [...kps];
    const paddedTps = [...tps];

    if (paddedKps.length === 0) {
      paddedKps.push(`Implement the core solution for "${topic}" using best-practice patterns.`);
      paddedTps.push(`Practical walkthrough of the implementation details, focusing on setting up components and configuring them correctly.`);
    }

    const finalKps = paddedKps.slice(0, 4);
    const finalTps = paddedTps.slice(0, 4);

    const slides = [
      `### Slide 1: Cover / Hook
- **Purpose**: Grab the user's attention instantly.
- **Heading**: ${day.hook || day.title}
- **Body Content**: ${day.title} (Series Day ${day.day_number}/${totalDays})
- **Series Day Indicator**: Day ${day.day_number} of ${totalDays} (${day.day_number}/${totalDays})
- **Visual Concept**: Eye-catching backdrop using theme gradient (${theme.gradient}), large bold headline, swipe-right chevron icon.
- **Layout**: Centered cover layout with brand header at the top and swipe indicator at the bottom.
- **Slide Explanation & Rationale**: Hook the target audience ("${audience}") on the core series theme ("${topic}") with a clear hook statement.`,
      `### Slide 2: The Problem / The Angle
- **Purpose**: Set the context, explain the pain point or core thesis.
- **Heading**: The Challenge
- **Body Content**: ${day.angle || "Why this specific topic is crucial to understand and what problems it solves."}
- **Visual Concept**: Split layout featuring a problem statement in an Alert/Warning Callout Box with a visual warning icon.
- **Layout**: Top 20% heading, center left 45% problem description, center right 45% visual pain-point illustration.
- **Slide Explanation & Rationale**: Establish the problem or learning gap for the user. Explain why existing methods are problematic to motivate learning.`,
    ];

    finalKps.forEach((kp, i) => {
      const tpContext = finalTps[i] || "Detailed walkthrough of this core concept to ensure complete understanding.";
      const visualIdea = topic.toLowerCase().includes("code") || topic.toLowerCase().includes("python") || topic.toLowerCase().includes("programming") || kp.toLowerCase().includes("code")
        ? "IDE Code Block Frame with syntax highlighting demonstrating this concept in action."
        : "A comparison grid or high-impact process step illustrating this point.";

      slides.push(`### Slide ${i + 3}: Teaching Point ${i + 1} - ${kp.split(" ").slice(0, 6).join(" ")}
- **Heading**: ${kp.split(" ").slice(0, 6).join(" ")}
- **Body Content**: ${kp}
- **Visual Concept**: ${visualIdea}
- **Layout**: Balanced teaching layout: Header top, core content and visual component side-by-side or stacked, swipe footer.
- **Slide Explanation & Rationale**: ${tpContext}`);
    });

    slides.push(`### Slide ${finalKps.length + 3}: Summary / Key Takeaway
- **Purpose**: Synthesize the day's teaching into a single high-value, memorable conclusion.
- **Heading**: Key Takeaway
- **Body Content**: ${day.teaching_goal || "Understand the core mechanism taught today and implement it in your workflow."}
- **Visual Concept**: Focus card centered on the slide using a highlight badge with the text "SUMMARY" or "TAKEAWAY".
- **Layout**: Minimalist high-contrast centered card layout.
- **Slide Explanation & Rationale**: Summarize the core teaching point. Give a clear actionable direction to apply what has been learned: "${day.teaching_goal}".`);

    slides.push(`### Slide ${finalKps.length + 4}: Actionable Call to Action
- **Purpose**: Direct user engagement and conversion.
- **Heading**: ${day.cta || "Save for Later"}
- **Body Content**: Follow @tech_by_pravesh | Share this post with someone | Save to read again
- **Next Day Preview**: ${nextDayInfo}
- **Visual Concept**: Large, bold call-to-action buttons styled with the theme accent color (${theme.acc}), accompanied by social handle badges.
- **Layout**: CTA slide layout with action items centered in the main visual canvas.
- **Slide Explanation & Rationale**: Prompt the user to bookmark, follow, or ask a question in the comment section to drive high algorithmic engagement and tease the next topic: "${nextDayInfo}".`);

    detailedSlides = slides.join("\n\n");
  }

  const platformLabel = PLATFORM_LABELS[platform] || platform;

  return `# Generate Production-Ready Carousel Slides in HTML/CSS/JS (ZIP Download Support)

## OUTPUT FORMAT: Unified HTML Slide Deck File
Generate a **single, unified HTML file** containing all slides nested as slide containers. This allows previewing all slides in the browser and downloading them all at once as a ZIP of JPGs.

The unified HTML file must contain:
- Standard vertical dimension slide containers: **1080px wide x 1350px tall** (4:5 aspect ratio for ${platformLabel})
- Fully self-contained styles (no external dependencies except Google Fonts)
- Included CDN libraries:
  - \`html2canvas\` for rendering slides to images: \`https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js\`
  - \`jszip\` for packaging images into a single zip file: \`https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js\`
- A global sticky control toolbar at the top with a **"Download All Slides (ZIP)"** button.
- A vertical stack of slide wrappers (e.g. \`<div class="slide-wrapper" id="slide-X">\`).
- Mobile-optimized typography (large, bold, high-contrast)
- Strict count of **between 5 and 8 slides total (minimum 5, maximum 8)**.

---

## Series Context
- **Series Theme**: "${topic}"
- **Platform**: ${platformLabel}
- **Day**: ${day.day_number} of ${totalDays}
- **Target Audience**: ${audience}
- **Difficulty Level**: ${difficulty}

---

## CRITICAL: Series-Wide Visual Theme Consistency
This is Day ${day.day_number} of a ${totalDays}-day series on "${topic}".
**ALL slides across ALL days of this series MUST use the EXACT SAME visual theme (same fonts, styling, structure, and component library).**

### Selected Theme Specification:
- **Theme Name**: ${theme.name}
- **Visual Style**: ${themeDescription}
- **Primary Color (headings, main accents)**: \`${theme.pri}\`
- **Secondary Color (body text, captions)**: \`${theme.sec}\`
- **Accent Color (badges, highlights, CTAs)**: \`${theme.acc}\`
- **Border Styling Color**: \`${theme.border}\`
- **Badge Styling**: Background color \`${theme.badgeBg}\` with text color \`${theme.badgeText}\`
- **Heading Font**: A bold Google Font (e.g., "Outfit", "Space Grotesk", "Plus Jakarta Sans") - SAME font every day
- **Body Font**: A readable Google Font (e.g., "Inter", "DM Sans") - SAME font every day
- **Brand Header**: Top 8% of every slide shows "@tech_by_pravesh" + series progress indicator (e.g., "Day ${day.day_number}/${totalDays}") + slide counter (e.g., "03/08") in consistent style
- **Footer**: Bottom 8% shows swipe indicator on non-final slides

---

## Detailed Slide-by-Slide Specification

Generate each of the following slides as a separate HTML slide wrapper. For each slide, use the visual components listed above where appropriate.

${detailedSlides}

---

## HTML/CSS/JS Requirements for the Unified Slide Deck File

### CRITICAL CODE OUTPUT REQUIREMENTS
1. You MUST include a physical, styled "Download All Slides (ZIP)" button inside a sticky control toolbar at the top of the HTML body. Do NOT replace it with comments or placeholders.
2. The button styling and control toolbar styling MUST be physically written in the CSS block.
3. The JavaScript '<script>' block containing the 'downloadAllJPGs()' function MUST be fully implemented and included at the bottom of the body. You must copy the JavaScript block verbatim without any modifications or shortcuts.

\`\`\`html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Series Day ${day.day_number}: ${day.title}</title>
  <link href="https://fonts.googleapis.com/css2?family=[HEADING_FONT]:wght@600;700;800;900&family=[BODY_FONT]:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- CDNs for capturing slides and zipping them -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
  
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0f172a;
      color: #f1f5f9;
      font-family: '[BODY_FONT]', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 20px;
    }
    
    /* Control Toolbar */
    .toolbar {
      position: sticky;
      top: 20px;
      z-index: 10000;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(12px);
      padding: 12px 24px;
      border-radius: 16px;
      margin-bottom: 40px;
      display: flex;
      gap: 15px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    .download-btn {
      background: ${theme.acc};
      color: #0f172a;
      border: none;
      padding: 12px 24px;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      transition: all 0.2s ease;
    }
    
    .download-btn:hover {
      transform: translateY(-2px);
      opacity: 0.95;
    }
    
    .download-btn:disabled {
      background: #475569;
      color: #94a3b8;
      cursor: not-allowed;
      transform: none;
    }
    
    /* Slide Deck Layout & Responsive Scaling */
    .deck-container {
      display: flex;
      flex-direction: column;
      gap: 40px;
    }
    
    .slide-wrapper {
      width: 1080px;
      height: 1350px;
      position: relative;
      overflow: hidden;
      border-radius: 16px;
      background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617);
      box-shadow: 0 20px 50px rgba(0,0,0,0.4);
      transform-origin: top center;
      display: flex;
      flex-direction: column;
    }
    
    @media (max-width: 1200px) {
        .slide-wrapper { transform: scale(0.8); margin-bottom: -270px; }
    }
    @media (max-width: 900px) {
        .slide-wrapper { transform: scale(0.6); margin-bottom: -540px; }
    }
    @media (max-width: 700px) {
        .slide-wrapper { transform: scale(0.4); margin-bottom: -810px; }
    }
    @media (max-width: 500px) {
        .slide-wrapper { transform: scale(0.3); margin-bottom: -945px; }
    }

    /* Core Slide Layout Elements */
    .slide-header {
      height: 108px;
      padding: 0 60px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: '[HEADING_FONT]', sans-serif;
      font-size: 24px;
      color: #94a3b8;
    }
    .slide-header .progress { display: flex; align-items: center; gap: 16px; }
    
    .badge {
      background: ${theme.badgeBg};
      color: ${theme.badgeText};
      padding: 10px 20px;
      border-radius: 30px;
      font-weight: 700;
      border: 1px solid ${theme.border}44;
    }

    .slide-main {
      flex: 1;
      padding: 40px 80px;
      display: flex;
      flex-direction: column;
    }

    .slide-footer {
      height: 108px;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 26px;
      font-weight: 600;
      color: #64748b;
      gap: 12px;
    }

    /* Typography & Hierarchy */
    .title {
      font-family: '[HEADING_FONT]', sans-serif;
      font-size: 72px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 30px;
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .title-num { color: ${theme.pri}; }
    .subtitle {
      font-size: 36px;
      color: #cbd5e1;
      line-height: 1.4;
      margin-bottom: 50px;
      font-weight: 500;
    }

    /* INSERT ADDITIONAL SLIDE-SPECIFIC COMPONENT STYLES BELOW */
  </style>
</head>
<body>

  <!-- Sticky control toolbar (MUST BE PRESENT IN BODY - DO NOT MODIFY) -->
  <div class="toolbar">
    <button class="download-btn" id="download-zip-btn" onclick="downloadAllJPGs()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
      Download All Slides (ZIP)
    </button>
  </div>

  <div class="deck-container">
    <!-- INSERT YOUR GENERATED SLIDES HERE. Each slide wrapper MUST use class "slide-wrapper" -->
    <!-- E.g. <div class="slide-wrapper" id="slide-1"> ... </div> -->
  </div>

  <!-- Physical Script block (MUST BE PRESENT - DO NOT MODIFY) -->
  <script>
    async function downloadAllJPGs() {
      const btn = document.getElementById('download-zip-btn');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      
      const zip = new JSZip();
      const slides = document.querySelectorAll('.slide-wrapper');
      
      try {
        for (let i = 0; i < slides.length; i++) {
          btn.innerHTML = \`Rendering Slide \${i+1} of \${slides.length}...\`;
          const slide = slides[i];
          
          const canvas = await html2canvas(slide, {
            width: 1080,
            height: 1350,
            scale: 2 // 2x resolution
          });
          
          const imgData = canvas.toDataURL('image/jpeg', 0.95).split(',')[1];
          zip.file(\`slide-\${i+1}.jpg\`, imgData, {base64: true});
        }
        
        btn.innerHTML = 'Generating ZIP archive...';
        const zipBlob = await zip.generateAsync({type: 'blob'});
        
        const link = document.createElement('a');
        link.download = 'day-${day.day_number}-carousel.zip';
        link.href = URL.createObjectURL(zipBlob);
        link.click();
      } catch (err) {
        console.error('Failed to export slides:', err);
        alert('Failed to generate export ZIP. Check browser console.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  </script>
</body>
</html>
\`\`\`

### Style Rules:
- Heading text: 48-72px, font-weight 700-900, using the heading font
- Body text: 28-36px, font-weight 400-600, using the body font
- Max 25 words per slide body (concise, high-retention copy)
- Use CSS gradients, shadows, and border-radius for premium feel
- Include subtle background patterns or shapes for visual interest
- All text must have sufficient contrast (WCAG AA minimum)
- Use the theme's accent color for emphasis, badges, and interactive elements

---

## Final Requirements
- Generate a SINGLE, UNIFIED HTML/CSS/JS file containing ALL slides nested in a clean vertical deck layout.
- Use the EXACT same theme (colors, fonts, component styles) for every slide wrapper.
- The theme must be relevant to and complement "${topic}".
- No placeholder text - every word must be real, final, publishable content.
- **Self-Contained Export ZIP Script**: The unified HTML slide deck file must include the sticky download toolbar and the \`html2canvas\` + \`jszip\` script as specified above so that clicking it triggers a high-resolution ZIP export of all slides.
- **Copy-Pasteable Caption & Hashtags**: After the HTML code block, you MUST generate the complete post caption for this day:
  - Structured using short, double-spaced paragraphs (1-2 sentences max).
  - Include 3-5 relevant hashtags (such as tech, programming, AI matching "${topic}").
  - Start with a compelling hook related to "${day.hook}".
  - End with a clear call-to-action inviting followers, comments, or saves.
  - Clearly label this block: \`### Final Social Media Caption:\` so it can be easily copied.
`;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-slate-400 truncate">{label}</span>
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value * 10}%`, background: color }}
        />
      </div>
      <span className="w-8 text-right font-mono text-slate-300">{value.toFixed(1)}</span>
    </div>
  );
}

function PlatformBadge({ platform }: { platform: string }) {
  const Icon = PLATFORM_ICONS[platform] || Zap;
  const color = PLATFORM_COLORS[platform] || "#888";
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold"
      style={{ background: `${color}22`, color, border: `1px solid ${color}44` }}
    >
      <Icon size={12} />
      {PLATFORM_LABELS[platform] || platform}
    </span>
  );
}

export default function CreativeManager({ weekId }: { weekId: string }) {
  // â”€â”€ Existing Manual Pipeline State â”€â”€
  const [tab, setTab] = useState<"research" | "topics" | "planner" | "export">("research");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [researchPrompt, setResearchPrompt] = useState("");
  const [pastedResearch, setPastedResearch] = useState("");
  const [topics, setTopics] = useState<Topic[]>([]);
  const [plan, setPlan] = useState<DayPlan[]>([]);
  const [niche, setNiche] = useState("AI & Tech");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sessionsList, setSessionsList] = useState<any[]>([]);
  const [copiedPromptId, setCopiedPromptId] = useState<number | null>(null);
  const [platformFilter, setPlatformFilter] = useState<string>("all");

  // â”€â”€ Quick Prompt Pipeline State (6-step flow) â”€â”€
  const [mode, setMode] = useState<"choose" | "manual" | "quick">("choose");
  const [qpStep, setQpStep] = useState<1 | 2 | 3 | 4 | 5 | 6>(1);
  const [qpSessionId, setQpSessionId] = useState<string | null>(null);
  const [qpSeriesLength, setQpSeriesLength] = useState(7);
  const [qpContentFilter, setQpContentFilter] = useState<string>("");
  const [qpPlatform, setQpPlatform] = useState<string>("instagram");
  const [qpUserTopic, setQpUserTopic] = useState("");
  const [qpDiscoveryPrompt, setQpDiscoveryPrompt] = useState("");
  const [qpPastedTopics, setQpPastedTopics] = useState("");
  const [qpDiscoveredTopics, setQpDiscoveredTopics] = useState<DiscoveredTopic[]>([]);
  const [qpSelectedTopic, setQpSelectedTopic] = useState<DiscoveredTopic | null>(null);
  const [qpDeepResearchPrompt, setQpDeepResearchPrompt] = useState("");
  const [qpPastedResearch, setQpPastedResearch] = useState("");
  const [qpPlan, setQpPlan] = useState<SeriesPlan | null>(null);
  const [qpProductionPrompt, setQpProductionPrompt] = useState("");
  const [qpChatMsg, setQpChatMsg] = useState("");
  const [qpChatHistory, setQpChatHistory] = useState<{ role: string; message: string }[]>([]);
  const [qpLoading, setQpLoading] = useState(false);
  const [qpCopied, setQpCopied] = useState(false);
  const [qpCopiedProd, setQpCopiedProd] = useState(false);
  const [qpExpandedDays, setQpExpandedDays] = useState<Set<number>>(new Set());
  const [qpSessionsList, setQpSessionsList] = useState<any[]>([]);
  const [qpActivePromptDay, setQpActivePromptDay] = useState(1);
  const [qpChatOpen, setQpChatOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Derive the series theme from the session ID
  const seriesTheme = getSeriesTheme(qpSessionId);

  const copyWritingPrompt = (dayIndex: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPromptId(dayIndex);
    setTimeout(() => setCopiedPromptId(null), 2000);
  };

  // Fetch previous sessions on load
  const loadPreviousSessions = async () => {
    try {
      const [manualRes, quickRes] = await Promise.all([
        listCreativeSessions(),
        listQuickSessions(),
      ]);
      setSessionsList(manualRes.sessions || []);
      setQpSessionsList(quickRes.sessions || []);
    } catch (e) {
      console.error("Failed to load previous sessions", e);
    }
  };

  useEffect(() => {
    if (!sessionId && !qpSessionId) {
      loadPreviousSessions();
    }
  }, [sessionId, qpSessionId]);

  const handleLoadSession = async (sid: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCreativeStatus(sid);
      setSessionId(res.session_id);
      setNiche(res.niche || "AI & Tech");
      setResearchPrompt(res.research_prompt || "");
      setStatus(res.status);
      setTopics(res.topics || []);
      setPlan(res.weekly_plan || []);
      setSelectedIds(new Set((res.topics || []).filter((t: any) => t.selected).map((t: any) => t.id)));

      // Determine tab based on status
      if (res.status === "planned") {
        setTab("planner");
      } else if (res.status === "topics_ready") {
        setTab("topics");
      } else {
        setTab("research");
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load session");
    } finally {
      setLoading(false);
    }
  };

  // Start session
  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await startCreativeSession(weekId, niche);
      setSessionId(res.session_id);
      setResearchPrompt(res.research_prompt);
      setStatus("input_needed");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to start session");
    } finally {
      setLoading(false);
    }
  };

  // Submit research
  const handleSubmitResearch = async () => {
    if (!sessionId || !pastedResearch.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await submitCreativeResearch(sessionId, pastedResearch);
      setTopics(res.topics || []);
      setStatus("topics_ready");
      setSelectedIds(new Set((res.topics || []).map((t: Topic) => t.id)));
      setTab("topics");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to parse research");
    } finally {
      setLoading(false);
    }
  };

  // Select topics and plan
  const handlePlanWeek = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      await selectCreativeTopics(sessionId, Array.from(selectedIds));
      const res = await planCreativeWeek(sessionId);
      setPlan(res.plan || []);
      setStatus("planned");
      setTab("planner");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to plan week");
    } finally {
      setLoading(false);
    }
  };

  const copyPrompt = () => {
    navigator.clipboard.writeText(researchPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleTopic = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const tabClass = (t: string) =>
    `px-5 py-3 text-sm font-semibold rounded-xl transition-all cursor-pointer ${tab === t
      ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25"
      : "text-slate-400 hover:text-white hover:bg-slate-800"
    }`;

  // â”€â”€ Quick Prompt Handlers (6-step flow) â”€â”€

  const handleQpStart = async () => {
    setQpLoading(true);
    setError(null);
    try {
      const res = await startQuickSession(qpSeriesLength, qpContentFilter, qpUserTopic, qpPlatform);
      setQpSessionId(res.session_id);

      if (res.status === "research_prompt_ready" && res.deep_research_prompt) {
        // PATH A: User provided topic → skip to step 4 (research)
        setQpSelectedTopic(res.selected_topic || null);
        setQpDeepResearchPrompt(res.deep_research_prompt);
        setQpDiscoveryPrompt("");
        setQpStep(4);
      } else {
        // PATH B: No topic → discovery flow (step 2)
        setQpDiscoveryPrompt(res.discovery_prompt);
        setQpStep(2);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to start session");
    } finally {
      setQpLoading(false);
    }
  };

  const handleQpSubmitTopics = async () => {
    if (!qpSessionId || !qpPastedTopics.trim()) return;
    setQpLoading(true);
    setError(null);
    try {
      const res = await submitQuickTopics(qpSessionId, qpPastedTopics);
      setQpDiscoveredTopics(res.topics || []);
      setQpStep(3);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to parse topics");
    } finally {
      setQpLoading(false);
    }
  };

  const handleQpSelectTopic = async (topicId: string) => {
    if (!qpSessionId) return;
    setQpLoading(true);
    setError(null);
    try {
      const res = await selectQuickTopic(qpSessionId, topicId);
      setQpSelectedTopic(res.selected_topic);
      setQpDeepResearchPrompt(res.deep_research_prompt);
      setQpStep(4);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to select topic");
    } finally {
      setQpLoading(false);
    }
  };

  const handleQpSubmitResearch = async () => {
    if (!qpSessionId || !qpPastedResearch.trim()) return;
    setQpLoading(true);
    setError(null);
    try {
      const res = await submitQuickResearch(qpSessionId, qpPastedResearch);
      setQpPlan(res.plan);
      setQpExpandedDays(new Set([1]));
      setQpStep(5);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to parse research");
    } finally {
      setQpLoading(false);
    }
  };

  const handleQpChat = async () => {
    if (!qpSessionId || !qpChatMsg.trim()) return;
    setQpLoading(true);
    setError(null);
    try {
      const res = await chatQuickEdit(qpSessionId, qpChatMsg);
      if (res.plan) setQpPlan(res.plan);
      setQpChatHistory(res.chat_history || []);
      setQpChatMsg("");
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to apply edit");
    } finally {
      setQpLoading(false);
    }
  };

  const handleQpApprove = async () => {
    if (!qpSessionId) return;
    setQpLoading(true);
    setError(null);
    try {
      const res = await approveQuickPlan(qpSessionId);
      setQpProductionPrompt(res.production_prompt);
      setQpPlan(res.plan);
      setQpStep(6);
      // Refresh sessions list so Saved Topics updates on dashboard
      loadPreviousSessions();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to approve plan");
    } finally {
      setQpLoading(false);
    }
  };

  const handleLoadQuickSession = async (sid: string) => {
    setQpLoading(true);
    setError(null);
    try {
      const res = await getQuickStatus(sid);
      setQpSessionId(res.id);
      setQpContentFilter(res.content_filter || "");
      setQpDiscoveryPrompt(res.discovery_prompt || "");
      setQpDiscoveredTopics(res.discovered_topics || []);
      setQpSelectedTopic(res.selected_topic || null);
      setQpDeepResearchPrompt(res.deep_research_prompt || "");
      setQpChatHistory(res.chat_history || []);
      const plan = res.series_plan;
      if (plan && plan.days && plan.days.length > 0) {
        setQpPlan(plan);
        setQpExpandedDays(new Set([1]));
      }
      setQpProductionPrompt(res.production_prompt || "");
      const si = res.structured_intent || {};
      setQpSeriesLength(si.series_length || 7);
      setQpUserTopic(si.topic_theme || "");
      setQpPlatform(si.platform || "instagram");

      // Determine step from status
      const status = res.status || "created";
      if (status === "finalized" && res.production_prompt) {
        setQpStep(6);
      } else if (status === "plan_review" && plan?.days?.length > 0) {
        setQpStep(5);
      } else if (status === "research_prompt_ready" && res.deep_research_prompt) {
        setQpStep(4);
      } else if (status === "topics_discovered" && (res.discovered_topics || []).length > 0) {
        setQpStep(3);
      } else if (status === "discovery_prompt_ready") {
        setQpStep(2);
      } else {
        setQpStep(1);
      }
      setMode("quick");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load session");
    } finally {
      setQpLoading(false);
    }
  };

  const toggleDayExpand = (dayNum: number) => {
    setQpExpandedDays((prev) => {
      const next = new Set(prev);
      if (next.has(dayNum)) next.delete(dayNum);
      else next.add(dayNum);
      return next;
    });
  };

  const qpCopyPrompt = (text: string, setter: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setter(true);
    setTimeout(() => setter(false), 2000);
  };

  const resetQuickPrompt = () => {
    setQpSessionId(null);
    setQpSeriesLength(7);
    setQpContentFilter("");
    setQpPlatform("instagram");
    setQpUserTopic("");
    setQpDiscoveryPrompt("");
    setQpPastedTopics("");
    setQpDiscoveredTopics([]);
    setQpSelectedTopic(null);
    setQpDeepResearchPrompt("");
    setQpPastedResearch("");
    setQpPlan(null);
    setQpProductionPrompt("");
    setQpChatMsg("");
    setQpChatHistory([]);
    setQpStep(1);
    setQpActivePromptDay(1);
    setQpChatOpen(false);
    setMode("choose");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Sparkles size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                Creative Manager
              </h1>
              <p className="text-xs text-slate-500">Educational Content Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {status !== "idle" && (
              <span className="text-xs font-semibold bg-violet-500/10 text-violet-400 px-3 py-1.5 rounded-lg border border-violet-500/20 capitalize">
                Status: {status.replace("_", " ")}
              </span>
            )}
            <span className="text-xs font-mono bg-slate-800 text-slate-400 px-3 py-1.5 rounded-lg border border-slate-700">
              {weekId}
            </span>
            {sessionId && (
              <button
                onClick={() => {
                  setSessionId(null);
                  setStatus("idle");
                  setTopics([]);
                  setPlan([]);
                  setResearchPrompt("");
                  setPastedResearch("");
                }}
                className="text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-slate-700 transition"
              >
                Exit Session
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        {sessionId && (
          <div className="max-w-7xl mx-auto px-6 pb-3 flex gap-2">
            <button onClick={() => setTab("research")} className={tabClass("research")}>
              <span className="flex items-center gap-2"><BookOpen size={14} /> Research</span>
            </button>
            <button onClick={() => setTab("topics")} className={tabClass("topics")} disabled={topics.length === 0}>
              <span className="flex items-center gap-2"><Target size={14} /> Topics ({topics.length})</span>
            </button>
            <button onClick={() => setTab("planner")} className={tabClass("planner")} disabled={plan.length === 0}>
              <span className="flex items-center gap-2"><Calendar size={14} /> Weekly Plan</span>
            </button>
            <button onClick={() => setTab("export")} className={tabClass("export")} disabled={plan.length === 0}>
              <span className="flex items-center gap-2"><Download size={14} /> Export</span>
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">{error}</div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* â”€â”€ MODE CHOOSER â”€â”€ */}
        {!sessionId && mode === "choose" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 flex items-center justify-center border border-violet-500/20">
              <Sparkles size={48} className="text-violet-400" />
            </div>
            <div className="text-center max-w-lg">
              <h2 className="text-3xl font-bold mb-3 bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
                Creative Manager
              </h2>
              <p className="text-slate-400 leading-relaxed">
                Choose your workflow to create educational content that your audience will{" "}
                <strong className="text-violet-400">save</strong>,{" "}
                <strong className="text-pink-400">share</strong>, and{" "}
                <strong className="text-amber-400">learn from</strong>.
              </p>
            </div>

            {/* Mode Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
              {/* Manual Research Mode */}
              <div
                onClick={() => setMode("manual")}
                className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 cursor-pointer hover:border-violet-500/50 hover:bg-slate-900/80 transition group"
              >
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <BookOpen size={28} className="text-violet-400" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">Manual Research</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  Get a research prompt, paste results from ChatGPT/Perplexity, score topics, and plan your week.
                </p>
                <div className="flex items-center gap-1 text-violet-400 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Start Manual Flow</span>
                  <ChevronRight size={14} />
                </div>
              </div>

              {/* Quick Prompt Mode */}
              <div
                onClick={() => setMode("quick")}
                className="bg-slate-900/60 border border-amber-500/20 rounded-2xl p-6 cursor-pointer hover:border-amber-500/50 hover:bg-slate-900/80 transition group relative overflow-hidden"
              >
                <div className="absolute top-3 right-3 px-2 py-0.5 bg-amber-500/15 text-amber-400 text-[10px] font-bold rounded-full border border-amber-500/20">
                  AI-Powered
                </div>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-600/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Wand2 size={28} className="text-amber-400" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">Quick Prompt</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  Type a simple idea, AI interprets it, generates a research prompt, and lets you review & edit day-by-day.
                </p>
                <div className="flex items-center gap-1 text-amber-400 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Start Quick Flow</span>
                  <ChevronRight size={14} />
                </div>
              </div>
            </div>

            {/* Saved Topics (finalized quick prompt sessions) */}
            {qpSessionsList.filter((s: any) => s.status === "finalized").length > 0 && (
              <div className="w-full max-w-4xl mt-12 pt-12 border-t border-slate-800/80">
                <h3 className="text-xl font-bold text-slate-200 mb-2 flex items-center gap-2">
                  <Sparkles size={20} className="text-emerald-400" />
                  Saved Topics
                </h3>
                <p className="text-xs text-slate-500 mb-5">Completed series plans ready for production. Click to load and reuse.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {qpSessionsList.filter((s: any) => s.status === "finalized").map((session: any) => {
                    const platformLabels: Record<string, string> = { instagram: "Instagram", linkedin: "LinkedIn", x: "X" };
                    const platformColors: Record<string, string> = { instagram: "#E1306C", linkedin: "#0A66C2", x: "#1DA1F2" };
                    const plat = session.platform || "instagram";
                    return (
                      <div
                        key={session.id}
                        onClick={() => handleLoadQuickSession(session.id)}
                        className="bg-slate-900/40 border border-emerald-500/15 rounded-2xl p-5 cursor-pointer hover:border-emerald-500/40 hover:bg-slate-900/60 transition group"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full border" style={{ color: platformColors[plat], borderColor: platformColors[plat] + "40", backgroundColor: platformColors[plat] + "10" }}>
                              {platformLabels[plat] || plat}
                            </span>
                            <span className="text-xs text-slate-500">{session.series_length} days</span>
                          </div>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Saved
                          </span>
                        </div>
                        <h4 className="font-bold text-base text-slate-200 group-hover:text-white transition mb-1 line-clamp-2">
                          {session.selected_topic_title || session.topic_theme || session.user_prompt}
                        </h4>
                        {session.content_filter && (
                          <span className="text-[10px] text-slate-500 capitalize">{session.content_filter.replace("_", " ")}</span>
                        )}
                        <div className="mt-4 text-xs text-slate-500 flex justify-between items-center border-t border-slate-800/60 pt-3">
                          <span>{new Date(session.created_at).toLocaleDateString()}</span>
                          <div className="flex items-center gap-1 text-emerald-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                            <span>Load</span>
                            <ChevronRight size={14} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* In Progress & Manual Sessions */}
            {(sessionsList.length > 0 || qpSessionsList.filter((s: any) => s.status !== "finalized").length > 0) && (
              <div className="w-full max-w-4xl mt-10 pt-10 border-t border-slate-800/80">
                <h3 className="text-lg font-bold text-slate-300 mb-5 flex items-center gap-2">
                  <Calendar size={18} className="text-slate-500" />
                  Previous Sessions
                </h3>
                <div className="grid grid-cols-1 gap-4">
                  {/* Manual sessions */}
                  {sessionsList.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => { setMode("manual"); handleLoadSession(session.id); }}
                      className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 cursor-pointer hover:border-violet-500/50 hover:bg-slate-900/60 transition group flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex justify-between items-start mb-3">
                          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20 capitalize">
                            {session.status.replace("_", " ")}
                          </span>
                          <span className="text-xs text-slate-500 font-mono bg-slate-800/50 px-2 py-0.5 rounded border border-slate-700/50">
                            {session.week_id}
                          </span>
                        </div>
                        <h4 className="font-bold text-base text-slate-200 group-hover:text-white transition">
                          Niche: {session.niche}
                        </h4>
                      </div>
                      <div className="mt-6 text-xs text-slate-500 flex justify-between items-center border-t border-slate-800/60 pt-3">
                        <span>{new Date(session.created_at).toLocaleString()}</span>
                        <div className="flex items-center gap-1 text-violet-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                          <span>Load Plan</span>
                          <ChevronRight size={14} />
                        </div>
                      </div>
                    </div>
                  ))}
                  {/* Quick prompt sessions (in progress only) */}
                  {qpSessionsList.filter((s: any) => s.status !== "finalized").map((session: any) => (
                    <div
                      key={session.id}
                      onClick={() => handleLoadQuickSession(session.id)}
                      className="bg-slate-900/40 border border-amber-500/15 rounded-2xl p-5 cursor-pointer hover:border-amber-500/40 hover:bg-slate-900/60 transition group flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex justify-between items-start mb-3">
                          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 capitalize">
                            {session.status.replace("_", " ")}
                          </span>
                          {session.platform && (
                            <span className="text-[10px] text-slate-500 capitalize">{session.platform}</span>
                          )}
                        </div>
                        <h4 className="font-bold text-base text-slate-200 group-hover:text-white transition line-clamp-2">
                          {session.selected_topic_title || session.topic_theme || session.user_prompt}
                        </h4>
                      </div>
                      <div className="mt-6 text-xs text-slate-500 flex justify-between items-center border-t border-slate-800/60 pt-3">
                        <span>{new Date(session.created_at).toLocaleString()}</span>
                        <div className="flex items-center gap-1 text-amber-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                          <span>Continue</span>
                          <ChevronRight size={14} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* â”€â”€ MANUAL MODE: IDLE STATE â”€â”€ */}
        {!sessionId && mode === "manual" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
            <button onClick={() => setMode("choose")} className="self-start text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1 transition">
              Back to mode selection
            </button>
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 flex items-center justify-center border border-violet-500/20">
              <BookOpen size={48} className="text-violet-400" />
            </div>
            <div className="text-center max-w-lg">
              <h2 className="text-3xl font-bold mb-3 bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
                Manual Research Flow
              </h2>
              <p className="text-slate-400 leading-relaxed">
                Get a research prompt, paste results from ChatGPT or Perplexity, and plan your week.
              </p>
            </div>
            <div className="flex flex-col items-center gap-4 w-full max-w-md">
              <div className="w-full">
                <label className="text-xs text-slate-500 mb-1 block">Content Niche</label>
                <input
                  type="text"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  placeholder="AI & Tech"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-violet-500 transition"
                />
              </div>
              <button
                onClick={handleStart}
                disabled={loading}
                className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3.5 px-6 rounded-xl transition-all shadow-lg shadow-violet-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <Loader size={18} className="animate-spin" /> : <Sparkles size={18} />}
                Start Creative Session
              </button>
            </div>
          </div>
        )}

        {/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */}
        {/* â•â•â•  QUICK PROMPT MODE (6-step flow)  â•â•â•â•â•â•â•â• */}
        {/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */}
        {mode === "quick" && (
          <div>
            {/* Quick Prompt Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <button onClick={resetQuickPrompt} className="text-xs text-slate-500 hover:text-slate-300 transition">Back</button>
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-600/20 flex items-center justify-center">
                  <Wand2 size={16} className="text-amber-400" />
                </div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-amber-300 to-orange-300 bg-clip-text text-transparent">
                  Quick Prompt Pipeline
                </h2>
              </div>
              {/* Step indicator — clickable for completed steps */}
              <div className="flex items-center gap-1.5">
                {[
                  { n: 1, label: "Input" },
                  { n: 2, label: "Discover" },
                  { n: 3, label: "Pick" },
                  { n: 4, label: "Research" },
                  { n: 5, label: "Review" },
                  { n: 6, label: "Prompt" },
                ].map(({ n, label }) => {
                  const isClickable = n <= qpStep && n !== qpStep;
                  return (
                    <div key={n} className="flex items-center gap-1">
                      <button
                        onClick={() => { if (isClickable) setQpStep(n as 1 | 2 | 3 | 4 | 5 | 6); }}
                        disabled={!isClickable}
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold border-2 transition-all ${qpStep >= n
                          ? "bg-amber-500/20 border-amber-500 text-amber-400"
                          : "border-slate-700 text-slate-600"
                          } ${isClickable ? "cursor-pointer hover:scale-110 hover:bg-amber-500/30 hover:shadow-md hover:shadow-amber-500/20" : n === qpStep ? "ring-2 ring-amber-400/30" : ""}`}
                      >
                        {qpStep > n ? <Check size={12} /> : n}
                      </button>
                      <span className={`text-[10px] font-medium hidden xl:inline ${isClickable ? "text-amber-400 cursor-pointer hover:text-amber-300" : qpStep >= n ? "text-amber-400" : "text-slate-600"}`}
                        onClick={() => { if (isClickable) setQpStep(n as 1 | 2 | 3 | 4 | 5 | 6); }}
                      >{label}</span>
                      {n < 6 && <div className={`w-4 h-0.5 rounded ${qpStep > n ? "bg-amber-500/40" : "bg-slate-800"}`} />}
                    </div>
                  );
                })}
              </div>
            </div>



            {/* — Step 1: Flexible Input (Topic + Length + Optional Filter) — */}
            {qpStep === 1 && (
              <div className="max-w-2xl mx-auto">
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur">
                  <h3 className="text-xl font-bold text-amber-300 mb-2 flex items-center gap-2">
                    <Wand2 size={20} /> What do you want to create?
                  </h3>
                  <p className="text-sm text-slate-400 mb-6">
                    Describe your idea below, or leave it empty and we'll discover trending topics for you.
                  </p>

                  {/* Topic Input */}
                  <div className="mb-6">
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">Your Topic <span className="text-slate-600 font-normal">(optional)</span></label>
                    <textarea
                      value={qpUserTopic}
                      onChange={(e) => setQpUserTopic(e.target.value)}
                      placeholder={"e.g. \"7 day series on hidden tricks of Claude\"\nor \"AI automation workflows that save 10+ hours/week\"\n\nLeave empty to discover trending topics"}
                      rows={3}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-600 resize-none focus:outline-none focus:border-amber-500/50 transition leading-relaxed"
                    />
                  </div>

                  {/* Series Length */}
                  <div className="mb-6">
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">Series Length</label>
                    <div className="flex flex-wrap gap-2">
                      {[3, 5, 7, 10, 14, 30].map((n) => (
                        <button key={n} onClick={() => setQpSeriesLength(n)}
                          className={`px-4 py-2.5 rounded-xl text-sm font-bold border-2 transition-all ${qpSeriesLength === n
                            ? "border-amber-500 bg-amber-500/15 text-amber-300 shadow-lg shadow-amber-500/10"
                            : "border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-300"}`}
                        >{n} days</button>
                      ))}
                    </div>
                  </div>

                  {/* Platform */}
                  <div className="mb-6">
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">Platform</label>
                    <div className="flex gap-2">
                      {([
                        { id: "instagram", icon: <span className="text-xs font-black">IG</span>, label: "Instagram", clr: "#E1306C" },
                        { id: "linkedin", icon: <span className="text-xs font-black">in</span>, label: "LinkedIn", clr: "#0A66C2" },
                        { id: "x", icon: <span className="text-xs font-black">X</span>, label: "X (Twitter)", clr: "#1DA1F2" },
                      ] as const).map((p) => (
                        <button key={p.id} onClick={() => setQpPlatform(p.id)}
                          className="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all"
                          style={qpPlatform === p.id
                            ? { borderColor: p.clr, backgroundColor: `${p.clr}15` }
                            : { borderColor: "#1e293b", backgroundColor: "rgba(2,6,23,0.4)" }}
                        >
                          <span style={{ color: p.clr }}>{p.icon}</span>
                          <span className={`text-xs font-bold ${qpPlatform === p.id ? "text-slate-200" : "text-slate-400"}`}>{p.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Content Filter — Optional */}
                  <div className="mb-6">
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">Content Filter <span className="text-slate-600 font-normal">(optional)</span></label>
                    <div className="grid grid-cols-2 gap-2">
                      {([
                        { id: "", icon: <Sparkles size={16} />, label: "All / None", desc: "No specific filter", clr: "#64748b" },
                        { id: "educational", icon: <GraduationCap size={16} />, label: "Educational", desc: "Tutorials & frameworks", clr: "#8b5cf6" },
                        { id: "news", icon: <Newspaper size={16} />, label: "Latest News", desc: "Recent developments", clr: "#3b82f6" },
                        { id: "trending_ai", icon: <Flame size={16} />, label: "Trending AI", desc: "Hot tools & techniques", clr: "#f97316" },
                      ] as const).map((f) => (
                        <button key={f.id} onClick={() => setQpContentFilter(f.id)}
                          className="flex items-center gap-3 p-3 rounded-xl border-2 text-left transition-all"
                          style={qpContentFilter === f.id
                            ? { borderColor: f.clr, backgroundColor: `${f.clr}15` }
                            : { borderColor: "#1e293b", backgroundColor: "rgba(2,6,23,0.4)" }}
                        >
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${f.clr}20`, color: f.clr }}>{f.icon}</div>
                          <div>
                            <div className="font-bold text-slate-200 text-xs">{f.label}</div>
                            <div className="text-[10px] text-slate-500">{f.desc}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Smart Button */}
                  <button onClick={handleQpStart} disabled={qpLoading}
                    className={`w-full font-bold py-3.5 px-6 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-40 ${qpUserTopic.trim()
                        ? "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20"
                        : "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white shadow-amber-500/20"
                      }`}
                  >
                    {qpLoading ? <Loader size={18} className="animate-spin" /> : qpUserTopic.trim() ? <ArrowRight size={18} /> : <Search size={18} />}
                    {qpUserTopic.trim() ? "Generate Research Prompt" : "Discover Trending Topics"}
                  </button>

                  {/* Helper text */}
                  {!qpUserTopic.trim() && (
                    <p className="text-[10px] text-slate-600 text-center mt-3">
                      We'll generate a prompt for Perplexity to find the best trending topics for your series.
                    </p>
                  )}
                  {qpUserTopic.trim() && (
                    <p className="text-[10px] text-slate-600 text-center mt-3">
                      We'll generate a deep research prompt for Claude/Perplexity based on your topic. Discovery steps will be skipped.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* â”€â”€ Step 2: Topic Discovery Prompt + Paste â”€â”€ */}
            {qpStep === 2 && (
              <div className="space-y-4">
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold text-violet-300 flex items-center gap-2">
                      <Search size={18} /> Topic Discovery Prompt
                    </h3>
                    <button onClick={() => qpCopyPrompt(qpDiscoveryPrompt, setQpCopied)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 rounded-lg text-xs font-semibold transition">
                      {qpCopied ? <Check size={14} /> : <Copy size={14} />}
                      {qpCopied ? "Copied!" : "Copy Prompt"}
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">Copy this into <strong>Perplexity</strong> to discover trending topics, then paste the result below.</p>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 max-h-[30vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {qpDiscoveryPrompt}
                  </div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                  <h3 className="text-lg font-bold text-emerald-300 flex items-center gap-2 mb-3">
                    <ArrowRight size={18} /> Paste Perplexity Results
                  </h3>
                  <textarea value={qpPastedTopics} onChange={(e) => setQpPastedTopics(e.target.value)}
                    placeholder="Paste the response from Perplexity here..."
                    className="w-full h-[20vh] bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 resize-none focus:outline-none focus:border-emerald-500/50 transition" />
                  <button onClick={handleQpSubmitTopics} disabled={qpLoading || !qpPastedTopics.trim()}
                    className="mt-3 w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-40">
                    {qpLoading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                    Parse & Show Topics
                  </button>
                </div>
              </div>
            )}

            {/* â”€â”€ Step 3: Topic Selection â”€â”€ */}
            {qpStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    <TrendingUp size={18} className="text-amber-400" /> Select a Topic for Your Series
                  </h3>
                  <span className="text-xs text-slate-500">{qpDiscoveredTopics.length} topics discovered</span>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {qpDiscoveredTopics.map((topic) => (
                    <div key={topic.id} onClick={() => handleQpSelectTopic(topic.id)}
                      className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 cursor-pointer transition-all hover:scale-[1.005] hover:border-amber-500/40">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1.5">
                            <h4 className="font-bold text-slate-100 text-base">{topic.title}</h4>
                            {topic.relevance_score > 0 && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/20">
                                {topic.relevance_score.toFixed(1)}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-400 mb-2">{topic.summary}</p>
                          {topic.why_trending && (
                            <p className="text-xs text-emerald-400/80 mb-2">
                              <span className="font-semibold">Why trending:</span> {topic.why_trending}
                            </p>
                          )}
                          {topic.suggested_angles.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {topic.suggested_angles.slice(0, 4).map((angle, i) => (
                                <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                                  {angle.length > 50 ? angle.substring(0, 50) + "..." : angle}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                          {qpLoading ? <Loader size={16} className="animate-spin text-amber-400" /> : <ArrowRight size={16} className="text-amber-400" />}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* â”€â”€ Step 4: Deep Research Prompt + Paste â”€â”€ */}
            {qpStep === 4 && (
              <div className="space-y-4">
                {qpSelectedTopic && (
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp size={14} className="text-amber-400" />
                      <span className="text-xs font-bold text-amber-400">Selected Topic</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-100">{qpSelectedTopic.title}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">{qpSelectedTopic.summary}</p>
                  </div>
                )}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold text-violet-300 flex items-center gap-2">
                      <BookOpen size={18} /> Deep Research Prompt
                    </h3>
                    <button onClick={() => qpCopyPrompt(qpDeepResearchPrompt, setQpCopied)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 rounded-lg text-xs font-semibold transition">
                      {qpCopied ? <Check size={14} /> : <Copy size={14} />}
                      {qpCopied ? "Copied!" : "Copy Prompt"}
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">Copy this into <strong>Claude</strong> or <strong>Perplexity</strong>, then paste the research result below.</p>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 max-h-[25vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {qpDeepResearchPrompt}
                  </div>
                </div>
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                  <h3 className="text-lg font-bold text-emerald-300 flex items-center gap-2 mb-3">
                    <ArrowRight size={18} /> Paste Research Results
                  </h3>
                  <textarea value={qpPastedResearch} onChange={(e) => setQpPastedResearch(e.target.value)}
                    placeholder="Paste the response from Claude/Perplexity here..."
                    className="w-full h-[20vh] bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 resize-none focus:outline-none focus:border-emerald-500/50 transition" />
                  <button onClick={handleQpSubmitResearch} disabled={qpLoading || !qpPastedResearch.trim()}
                    className="mt-3 w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-40">
                    {qpLoading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                    Parse & Review Plan
                  </button>
                </div>
              </div>
            )}

            {/* Step 5: Day-by-Day Review + Per-Day Prompt Carousel */}
            {qpStep === 5 && qpPlan && (() => {
              const activeDay = qpPlan.days.find(d => d.day_number === qpActivePromptDay) || qpPlan.days[0];
              const dayPrompt = activeDay ? buildDayPrompt(activeDay, qpPlan, qpPlatform, qpSessionId) : "";
              return (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                      <Calendar size={18} style={{ color: seriesTheme.pri }} /> Series Plan - {qpPlan.days.length} Days
                      <span className="text-xs font-normal px-2 py-0.5 rounded-full ml-2" style={{ background: seriesTheme.badgeBg, color: seriesTheme.badgeText, border: `1px solid ${seriesTheme.border}33` }}>
                        {seriesTheme.name}
                      </span>
                    </h3>
                    <button onClick={handleQpApprove} disabled={qpLoading}
                      className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-2 px-5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 disabled:opacity-40">
                      {qpLoading ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                      Approve & Generate Final Prompt
                    </button>
                  </div>

                  <div className="flex gap-4" style={{ minHeight: "calc(100vh - 320px)" }}>
                    {/* LEFT: Day Cards (scrollable) */}
                    <div className="w-[55%] space-y-3 overflow-y-auto pr-2" style={{ maxHeight: "calc(100vh - 320px)" }}>
                      {qpPlan.days.map((day) => {
                        const isExpanded = qpExpandedDays.has(day.day_number);
                        const isActive = day.day_number === qpActivePromptDay;
                        return (
                          <div key={day.day_number}
                            className={`bg-slate-900/60 border rounded-2xl backdrop-blur overflow-hidden transition cursor-pointer ${isActive ? "ring-1" : "hover:border-slate-700"}`}
                            style={{ borderLeft: `4px solid ${seriesTheme.border}`, borderColor: isActive ? seriesTheme.border : undefined, boxShadow: isActive ? `0 0 12px ${seriesTheme.border}22` : undefined }}
                            onClick={() => setQpActivePromptDay(day.day_number)}
                          >
                            <div onClick={(e) => { e.stopPropagation(); toggleDayExpand(day.day_number); }} className="p-4 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: seriesTheme.badgeBg }}>
                                  <span className="text-sm font-bold" style={{ color: seriesTheme.pri }}>{day.day_number}</span>
                                </div>
                                <div>
                                  <h4 className="text-base font-bold text-slate-100">{day.title}</h4>
                                  <span className="text-xs text-slate-500">Day {day.day_number} - {day.content_type}</span>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <PlatformBadge platform={day.platform} />
                                {isExpanded ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
                              </div>
                            </div>
                            {isExpanded && (
                              <div className="px-4 pb-4 space-y-2 border-t border-slate-800/60 pt-3">
                                {day.hook && (<div><span className="text-xs font-semibold" style={{ color: seriesTheme.acc }}>Hook: </span><span className="text-xs text-slate-300 italic">"{day.hook}"</span></div>)}
                                {day.teaching_goal && (<div><span className="text-xs font-semibold text-violet-400">Teaching Goal: </span><span className="text-xs text-slate-400">{day.teaching_goal}</span></div>)}
                                {day.angle && (<div><span className="text-xs font-semibold text-emerald-400">Angle: </span><span className="text-xs text-slate-400">{day.angle}</span></div>)}
                                {day.key_points.length > 0 && (
                                  <div>
                                    <p className="text-xs font-semibold text-violet-400 mb-1">Key Points:</p>
                                    <ul className="text-xs text-slate-400 space-y-0.5">
                                      {day.key_points.map((kp, i) => (<li key={i} className="flex items-start gap-1.5"><span className="text-violet-500 mt-0.5">-</span> {kp}</li>))}
                                    </ul>
                                  </div>
                                )}
                                {day.slide_outline && day.slide_outline.length > 0 && (
                                  <div>
                                    <p className="text-xs font-semibold text-pink-400 mb-1">Slide Outline:</p>
                                    <div className="space-y-1">
                                      {day.slide_outline.map((slide: any, i: number) => (
                                        <div key={i} className="bg-slate-950/60 rounded-lg p-2 text-xs"><span className="font-bold text-slate-300">Slide {slide.slide_number || i + 1}: </span><span className="text-slate-400">{slide.slide_title} - {slide.slide_content}</span></div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {day.script && (<div><p className="text-xs font-semibold text-blue-400 mb-1">Script:</p><p className="text-xs text-slate-400 bg-slate-950/60 rounded-lg p-2 whitespace-pre-wrap">{day.script}</p></div>)}
                                {day.caption && (<div><p className="text-xs font-semibold text-emerald-400 mb-1">Caption:</p><p className="text-xs text-slate-400 bg-slate-950/60 rounded-lg p-2 whitespace-pre-wrap">{day.caption}</p></div>)}
                                {day.cta && (<div><span className="text-xs font-semibold text-rose-400">CTA: </span><span className="text-xs text-slate-400">{day.cta}</span></div>)}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* RIGHT: Per-Day Prompt Carousel (sticky) */}
                    <div className="w-[45%] sticky top-32 self-start">
                      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl backdrop-blur overflow-hidden flex flex-col" style={{ maxHeight: "calc(100vh - 320px)", borderTop: `3px solid ${seriesTheme.border}` }}>
                        {/* Carousel Header */}
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                          <div>
                            <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: seriesTheme.badgeText }}>
                              <Sparkles size={16} /> Day {qpActivePromptDay} Prompt
                            </h3>
                            <p className="text-xs text-slate-500 mt-0.5">{activeDay?.title}</p>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button onClick={() => setQpActivePromptDay(Math.max(1, qpActivePromptDay - 1))} disabled={qpActivePromptDay <= 1}
                              className="w-7 h-7 rounded-lg flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-400 transition disabled:opacity-30">
                              <ChevronLeft size={14} />
                            </button>
                            <span className="text-xs text-slate-500 font-mono px-2">{qpActivePromptDay}/{qpPlan.days.length}</span>
                            <button onClick={() => setQpActivePromptDay(Math.min(qpPlan.days.length, qpActivePromptDay + 1))} disabled={qpActivePromptDay >= qpPlan.days.length}
                              className="w-7 h-7 rounded-lg flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-400 transition disabled:opacity-30">
                              <ChevronRight size={14} />
                            </button>
                          </div>
                        </div>

                        {/* Day Dots */}
                        <div className="flex gap-1 px-4 py-2 border-b border-slate-800/60 justify-center flex-wrap">
                          {qpPlan.days.map(d => (
                            <button key={d.day_number} onClick={() => setQpActivePromptDay(d.day_number)}
                              className="w-6 h-6 rounded-full text-[10px] font-bold transition-all"
                              style={{
                                background: d.day_number === qpActivePromptDay ? seriesTheme.pri : "rgba(100,116,139,0.2)",
                                color: d.day_number === qpActivePromptDay ? "#fff" : "#94a3b8",
                                boxShadow: d.day_number === qpActivePromptDay ? `0 0 8px ${seriesTheme.pri}44` : undefined,
                              }}>
                              {d.day_number}
                            </button>
                          ))}
                        </div>

                        {/* Prompt Content */}
                        <div className="flex-1 overflow-y-auto p-4">
                          <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap leading-relaxed">{dayPrompt}</pre>
                        </div>

                        {/* Copy Button */}
                        <div className="p-3 border-t border-slate-800">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(dayPrompt);
                              setCopiedPromptId(qpActivePromptDay);
                              setTimeout(() => setCopiedPromptId(null), 2000);
                            }}
                            className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-sm font-semibold transition"
                            style={{ background: seriesTheme.badgeBg, color: seriesTheme.badgeText, border: `1px solid ${seriesTheme.border}33` }}>
                            {copiedPromptId === qpActivePromptDay ? <Check size={14} /> : <Copy size={14} />}
                            {copiedPromptId === qpActivePromptDay ? "Copied!" : `Copy Day ${qpActivePromptDay} Prompt`}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Step 6: Production Prompt (per-day carousel + full prompt) */}
            {qpStep === 6 && qpPlan && (() => {
              const activeDay6 = qpPlan.days.find(d => d.day_number === qpActivePromptDay) || qpPlan.days[0];
              const dayPrompt6 = activeDay6 ? buildDayPrompt(activeDay6, qpPlan, qpPlatform, qpSessionId) : "";
              return (
                <div className="space-y-6">
                  {/* Per-Day Carousel */}
                  <div className="bg-slate-900/60 border rounded-2xl p-6 backdrop-blur" style={{ borderColor: `${seriesTheme.border}44`, borderTop: `3px solid ${seriesTheme.border}` }}>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: seriesTheme.badgeText }}>
                        <Sparkles size={18} /> Per-Day Production Prompts
                      </h3>
                      <div className="flex items-center gap-1.5">
                        <button onClick={() => setQpActivePromptDay(Math.max(1, qpActivePromptDay - 1))} disabled={qpActivePromptDay <= 1}
                          className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-400 transition disabled:opacity-30">
                          <ArrowLeft size={14} />
                        </button>
                        <span className="text-sm text-slate-400 font-mono px-3">Day {qpActivePromptDay} of {qpPlan.days.length}</span>
                        <button onClick={() => setQpActivePromptDay(Math.min(qpPlan.days.length, qpActivePromptDay + 1))} disabled={qpActivePromptDay >= qpPlan.days.length}
                          className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-400 transition disabled:opacity-30">
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>

                    <p className="text-sm text-slate-500 mb-3"><strong style={{ color: seriesTheme.acc }}>{activeDay6?.title}</strong> - Copy this into Claude, Gemini, or GPT to generate Day {qpActivePromptDay}'s content.</p>

                    <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 font-mono max-h-[40vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">{dayPrompt6}</pre>

                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(dayPrompt6);
                        setCopiedPromptId(qpActivePromptDay);
                        setTimeout(() => setCopiedPromptId(null), 2000);
                      }}
                      className="mt-3 w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-sm font-semibold transition"
                      style={{ background: seriesTheme.badgeBg, color: seriesTheme.badgeText, border: `1px solid ${seriesTheme.border}33` }}>
                      {copiedPromptId === qpActivePromptDay ? <Check size={14} /> : <Copy size={14} />}
                      {copiedPromptId === qpActivePromptDay ? "Copied!" : `Copy Day ${qpActivePromptDay} Prompt`}
                    </button>

                    {/* Day dots */}
                    <div className="flex gap-1.5 mt-3 justify-center flex-wrap">
                      {qpPlan.days.map(d => (
                        <button key={d.day_number} onClick={() => setQpActivePromptDay(d.day_number)}
                          className="w-7 h-7 rounded-full text-[10px] font-bold transition-all"
                          style={{
                            background: d.day_number === qpActivePromptDay ? seriesTheme.pri : "rgba(100,116,139,0.2)",
                            color: d.day_number === qpActivePromptDay ? "#fff" : "#94a3b8",
                          }}>
                          {d.day_number}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Full Production Prompt (collapsible) */}
                  {qpProductionPrompt && (
                    <div className="bg-slate-900/60 border border-emerald-500/20 rounded-2xl p-6 backdrop-blur">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-emerald-300 flex items-center gap-2"><Check size={18} /> Full Series Prompt (All Days)</h3>
                        <button onClick={() => qpCopyPrompt(qpProductionPrompt, setQpCopiedProd)}
                          className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded-lg text-sm font-semibold transition border border-emerald-500/20">
                          {qpCopiedProd ? <Check size={14} /> : <Copy size={14} />}
                          {qpCopiedProd ? "Copied!" : "Copy Full Prompt"}
                        </button>
                      </div>
                      <p className="text-xs text-slate-500 mb-3">This generates content for all {qpPlan.days.length} days in one go.</p>
                      <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 font-mono max-h-[30vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">{qpProductionPrompt}</pre>
                    </div>
                  )}

                  <div className="flex gap-3">
                    <button onClick={() => setQpStep(5)} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2.5 px-4 rounded-xl text-sm transition">Back to Review</button>
                    <button onClick={resetQuickPrompt} className="flex-1 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition shadow-lg shadow-violet-500/20">Start New Session</button>
                  </div>
                </div>
              );
            })()}



            {/* Floating Chat Bar (bottom center, Steps 2-6) */}
            {mode === "quick" && qpStep >= 2 && (
              <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4">
                {/* Chat History (expanded) */}
                {qpChatOpen && (
                  <div className="bg-slate-900/95 border border-slate-700 rounded-2xl mb-2 backdrop-blur-xl shadow-2xl shadow-black/40 max-h-[40vh] overflow-hidden flex flex-col">
                    <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                      <h4 className="text-xs font-bold text-amber-300 flex items-center gap-1.5"><MessageSquare size={12} /> Chat Assistant</h4>
                      <button onClick={() => setQpChatOpen(false)} className="text-slate-500 hover:text-slate-300 text-xs transition">Close</button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-3 space-y-2">
                      {qpChatHistory.length === 0 && (
                        <div className="text-xs text-slate-600 text-center py-4">
                          <p className="mb-1.5">Try saying:</p>
                          <div className="space-y-1 text-slate-500">
                            {qpStep < 5 ? (<><p>"Focus more on practical tutorials"</p><p>"I want beginner-friendly content"</p></>) : (<><p>"Improve the hook for day 2"</p><p>"Change day 3 to a reel"</p><p>"Swap day 1 and day 4"</p></>)}
                          </div>
                        </div>
                      )}
                      {qpChatHistory.map((msg, i) => (
                        <div key={i} className={`text-xs rounded-xl p-2.5 max-w-[85%] ${msg.role === "user" ? "bg-amber-500/10 text-amber-200 border border-amber-500/20 ml-auto" : "bg-slate-800 text-slate-300 border border-slate-700"}`}>
                          {msg.message}
                        </div>
                      ))}
                      <div ref={chatEndRef} />
                    </div>
                  </div>
                )}

                {/* Chat Input Bar */}
                <div className="bg-slate-900/95 border border-slate-700 rounded-2xl backdrop-blur-xl shadow-2xl shadow-black/40 p-2.5 flex gap-2 items-center">
                  <button onClick={() => setQpChatOpen(!qpChatOpen)} className="w-8 h-8 rounded-lg flex items-center justify-center bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 transition shrink-0">
                    <MessageSquare size={14} />
                  </button>
                  <input type="text" value={qpChatMsg} onChange={(e) => setQpChatMsg(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleQpChat(); }}
                    onFocus={() => setQpChatOpen(true)}
                    placeholder={qpStep < 5 ? "Ask questions or leave notes..." : "Edit the plan with natural language..."}
                    className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-amber-500/50 transition placeholder-slate-600" />
                  <button onClick={handleQpChat} disabled={qpLoading || !qpChatMsg.trim()}
                    className="w-9 h-9 rounded-xl flex items-center justify-center bg-amber-600 hover:bg-amber-500 text-white transition disabled:opacity-40 shrink-0">
                    {qpLoading ? <Loader size={14} className="animate-spin" /> : <Send size={14} />}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}




        {/* â”€â”€ RESEARCH TAB â”€â”€ */}
        {sessionId && tab === "research" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Prompt */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-violet-300 flex items-center gap-2">
                  <BookOpen size={18} /> Research Prompt
                </h3>
                <button
                  onClick={copyPrompt}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 rounded-lg text-xs font-semibold transition"
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  {copied ? "Copied!" : "Copy Prompt"}
                </button>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                Copy this prompt into <strong>ChatGPT</strong> or <strong>Perplexity</strong> and paste the result below.
              </p>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 font-mono max-h-[50vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                {researchPrompt}
              </div>
            </div>

            {/* Paste area */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
              <h3 className="text-lg font-bold text-emerald-300 flex items-center gap-2 mb-4">
                <ArrowRight size={18} /> Paste Research Results
              </h3>
              <textarea
                value={pastedResearch}
                onChange={(e) => setPastedResearch(e.target.value)}
                placeholder="Paste the research response here..."
                className="w-full h-[50vh] bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 font-mono resize-none focus:outline-none focus:border-emerald-500/50 transition"
              />
              <button
                onClick={handleSubmitResearch}
                disabled={loading || !pastedResearch.trim()}
                className="mt-4 w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-40"
              >
                {loading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                Analyze & Score Topics
              </button>
            </div>
          </div>
        )}

        {/* â”€â”€ TOPICS TAB â”€â”€ */}
        {sessionId && tab === "topics" && (
          <div>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-5">
              <div>
                <h2 className="text-xl font-bold text-slate-200">
                  Discovered Topics
                  <span className="text-sm text-slate-500 ml-2">({selectedIds.size} selected)</span>
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Filter topics by platform to target specific audiences.</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-500 font-semibold mr-1">Filter:</span>
                {["all", "instagram", "linkedin", "x"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPlatformFilter(p)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition cursor-pointer ${platformFilter === p
                      ? "bg-violet-600/25 border-violet-500/50 text-violet-300 font-bold"
                      : "bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                      }`}
                  >
                    {p === "all" ? "All Platforms" : p === "x" ? "X (Twitter)" : p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>

              <button
                onClick={handlePlanWeek}
                disabled={loading || selectedIds.size === 0}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-2.5 px-5 rounded-xl text-sm transition-all shadow-lg shadow-violet-500/20 flex items-center gap-2 disabled:opacity-40"
              >
                {loading ? <Loader size={16} className="animate-spin" /> : <Calendar size={16} />}
                Plan Week with Selected
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {topics
                .filter((t) => {
                  if (platformFilter === "all") return true;
                  return (t.best_platforms || []).map((bp) => bp.toLowerCase()).includes(platformFilter);
                })
                .map((topic) => {
                  const isSelected = selectedIds.has(topic.id);
                  const emoji = CATEGORY_EMOJIS[topic.category] || "";
                  const s = topic.engagement_scores;

                  return (
                    <div
                      key={topic.id}
                      onClick={() => toggleTopic(topic.id)}
                      className={`bg-slate-900/60 border rounded-2xl p-5 backdrop-blur cursor-pointer transition-all hover:scale-[1.01] ${isSelected
                        ? "border-violet-500/50 shadow-lg shadow-violet-500/10"
                        : "border-slate-800 hover:border-slate-700"
                        }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {emoji && <span className="text-xl">{emoji}</span>}
                          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                            {topic.category}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-bold px-2.5 py-1 rounded-full ${s.overall >= 7
                              ? "bg-emerald-500/15 text-emerald-400"
                              : s.overall >= 5
                                ? "bg-amber-500/15 text-amber-400"
                                : "bg-slate-700 text-slate-400"
                              }`}
                          >
                            {s.overall.toFixed(1)}/10
                          </span>
                          <div
                            className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition ${isSelected ? "bg-violet-600 border-violet-500" : "border-slate-600"
                              }`}
                          >
                            {isSelected && <Check size={14} />}
                          </div>
                        </div>
                      </div>

                      <h3 className="text-base font-bold text-slate-100 mb-1.5 leading-snug">{topic.title}</h3>
                      <p className="text-xs text-slate-400 mb-3 leading-relaxed">{topic.summary}</p>

                      {/* Teaching points */}
                      {topic.teaching_points.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs font-semibold text-violet-400 mb-1">What they'll learn:</p>
                          <ul className="text-xs text-slate-400 space-y-0.5">
                            {topic.teaching_points.slice(0, 3).map((tp, i) => (
                              <li key={i} className="flex items-start gap-1.5">
                                <span className="text-violet-500 mt-0.5">-</span>
                                {tp}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Platforms */}
                      <div className="flex gap-1.5 mb-3 flex-wrap">
                        {(topic.best_platforms || []).map((p) => (
                          <PlatformBadge key={p} platform={p} />
                        ))}
                      </div>

                      {/* Scores */}
                      <div className="space-y-1.5">
                        <ScoreBar label="Educational" value={s.educational_value} color="#8b5cf6" />
                        <ScoreBar label="Saveable" value={s.saveability} color="#10b981" />
                        <ScoreBar label="Shareable" value={s.shareability} color="#3b82f6" />
                        <ScoreBar label="Conversation" value={s.conversation} color="#f59e0b" />
                        <ScoreBar label="Viral" value={s.virality} color="#ef4444" />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* â”€â”€ PLANNER TAB â”€â”€ */}
        {sessionId && tab === "planner" && (
          <div>
            <h2 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
              <Calendar size={22} className="text-violet-400" /> Weekly Content Plan
            </h2>

            <div className="grid grid-cols-1 gap-4">
              {plan.map((day, i) => {
                const color = PLATFORM_COLORS[day.platform] || "#888";
                const Icon = PLATFORM_ICONS[day.platform] || Zap;

                return (
                  <div
                    key={i}
                    className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 backdrop-blur hover:border-slate-700 transition"
                    style={{ borderLeft: `4px solid ${color}` }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center"
                          style={{ background: `${color}20` }}
                        >
                          <Icon size={20} style={{ color }} />
                        </div>
                        <div>
                          <span className="text-sm font-bold text-slate-200 capitalize">{day.day}</span>
                          <span className="text-xs text-slate-500 ml-2">{day.date}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 capitalize">
                          {day.content_format}
                        </span>
                        <PlatformBadge platform={day.platform} />
                      </div>
                    </div>

                    <h3 className="text-base font-bold text-slate-100 mb-1">{day.topic_title}</h3>

                    {day.hook && (
                      <div className="mb-2">
                        <span className="text-xs font-semibold text-amber-400">Hook: </span>
                        <span className="text-xs text-slate-300 italic">"{day.hook}"</span>
                      </div>
                    )}

                    {day.teaching_goal && (
                      <div className="mb-2">
                        <span className="text-xs font-semibold text-violet-400">Teaching Goal: </span>
                        <span className="text-xs text-slate-400">{day.teaching_goal}</span>
                      </div>
                    )}

                    {day.angle && (
                      <div className="mb-2">
                        <span className="text-xs font-semibold text-emerald-400">Angle: </span>
                        <span className="text-xs text-slate-400">{day.angle}</span>
                      </div>
                    )}

                    {day.reasoning && (
                      <p className="text-xs text-slate-500 italic mt-2 border-t border-slate-800 pt-2">
                        {day.reasoning}
                      </p>
                    )}

                    {day.writing_prompt && (
                      <div className="mt-4 border-t border-slate-800/80 pt-3 flex justify-end">
                        <button
                          onClick={() => copyWritingPrompt(i, day.writing_prompt || "")}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/20 hover:bg-violet-600/35 text-violet-300 rounded-lg text-xs font-semibold transition border border-violet-500/20"
                        >
                          {copiedPromptId === i ? <Check size={12} /> : <Copy size={12} />}
                          {copiedPromptId === i ? "Copied Prompt!" : "Copy Writing Prompt"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* â”€â”€ EXPORT TAB â”€â”€ */}
        {sessionId && tab === "export" && (
          <div className="max-w-4xl mx-auto">
            <h2 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
              <Download size={22} className="text-violet-400" /> Export Plan
            </h2>

            <div className="grid grid-cols-1 gap-4">
              {/* Markdown */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                <h3 className="text-sm font-bold text-emerald-300 mb-3">Markdown</h3>
                <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 font-mono max-h-[40vh] overflow-y-auto whitespace-pre-wrap">
                  {plan
                    .map(
                      (d) =>
                        `## ${d.day.charAt(0).toUpperCase() + d.day.slice(1)} (${d.date})\n**Platform:** ${PLATFORM_LABELS[d.platform] || d.platform}\n**Format:** ${d.content_format}\n**Topic:** ${d.topic_title}\n**Hook:** ${d.hook}\n**Teaching Goal:** ${d.teaching_goal}\n**Angle:** ${d.angle}\n`
                    )
                    .join("\n---\n\n")}
                </pre>
                <button
                  onClick={() => {
                    const md = plan
                      .map(
                        (d) =>
                          `## ${d.day.charAt(0).toUpperCase() + d.day.slice(1)} (${d.date})\n**Platform:** ${PLATFORM_LABELS[d.platform] || d.platform}\n**Format:** ${d.content_format}\n**Topic:** ${d.topic_title}\n**Hook:** ${d.hook}\n**Teaching Goal:** ${d.teaching_goal}\n**Angle:** ${d.angle}`
                      )
                      .join("\n\n---\n\n");
                    navigator.clipboard.writeText(md);
                  }}
                  className="mt-3 w-full bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 font-semibold py-2 px-4 rounded-lg text-xs transition flex items-center justify-center gap-1.5"
                >
                  <Copy size={14} /> Copy Markdown
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
