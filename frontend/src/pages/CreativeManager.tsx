import { useState, useEffect, useRef } from "react";
import {
  Sparkles, Copy, Check, BookOpen,
  Calendar, Zap, ArrowRight, ArrowLeft, Loader, ChevronRight, ChevronLeft,
  MessageSquare, Send, ChevronDown, ChevronUp, Wand2,
  Search, TrendingUp, GraduationCap, Newspaper, Flame,
} from "lucide-react";
import {
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

// Quick Prompt types
export interface SeriesDay {
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

export interface SeriesPlan {
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
  news_date?: string;
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



// Series theme presets - each series gets a unique visual identity
export const SERIES_THEMES = [
  { name: "aurora", pri: "#8b5cf6", sec: "#06b6d4", acc: "#c084fc", border: "#8b5cf6", badgeBg: "rgba(139,92,246,0.15)", badgeText: "#c084fc", gradient: "from-violet-600 to-cyan-500" },
  { name: "ember", pri: "#f97316", sec: "#ef4444", acc: "#fbbf24", border: "#f97316", badgeBg: "rgba(249,115,22,0.15)", badgeText: "#fdba74", gradient: "from-orange-500 to-red-500" },
  { name: "forest", pri: "#10b981", sec: "#84cc16", acc: "#34d399", border: "#10b981", badgeBg: "rgba(16,185,129,0.15)", badgeText: "#6ee7b7", gradient: "from-emerald-500 to-lime-500" },
  { name: "ocean", pri: "#3b82f6", sec: "#0891b2", acc: "#60a5fa", border: "#3b82f6", badgeBg: "rgba(59,130,246,0.15)", badgeText: "#93c5fd", gradient: "from-blue-500 to-teal-500" },
  { name: "sunset", pri: "#f59e0b", sec: "#ec4899", acc: "#fcd34d", border: "#f59e0b", badgeBg: "rgba(245,158,11,0.15)", badgeText: "#fde68a", gradient: "from-amber-500 to-pink-500" },
  { name: "neon", pri: "#a3e635", sec: "#d946ef", acc: "#bef264", border: "#a3e635", badgeBg: "rgba(163,230,53,0.15)", badgeText: "#bef264", gradient: "from-lime-400 to-fuchsia-500" },
  { name: "midnight", pri: "#6366f1", sec: "#475569", acc: "#818cf8", border: "#6366f1", badgeBg: "rgba(99,102,241,0.15)", badgeText: "#a5b4fc", gradient: "from-indigo-500 to-slate-600" },
  { name: "coral", pri: "#fb7185", sec: "#fdba74", acc: "#fda4af", border: "#fb7185", badgeBg: "rgba(251,113,133,0.15)", badgeText: "#fda4af", gradient: "from-rose-400 to-orange-300" },
  { name: "dracula", pri: "#ff79c6", sec: "#bd93f9", acc: "#8be9fd", border: "#ff79c6", badgeBg: "rgba(255,121,198,0.15)", badgeText: "#ff79c6", gradient: "from-pink-500 to-purple-700" },
  { name: "nord", pri: "#88c0d0", sec: "#81a1c1", acc: "#8fbcbb", border: "#88c0d0", badgeBg: "rgba(136,192,208,0.15)", badgeText: "#88c0d0", gradient: "from-sky-400 to-slate-700" },
  { name: "obsidian", pri: "#f59e0b", sec: "#4b5563", acc: "#fbbf24", border: "#f59e0b", badgeBg: "rgba(245,158,11,0.15)", badgeText: "#fcd34d", gradient: "from-yellow-600 to-zinc-900" },
  { name: "retro", pri: "#22c55e", sec: "#15803d", acc: "#4ade80", border: "#22c55e", badgeBg: "rgba(34,197,94,0.15)", badgeText: "#4ade80", gradient: "from-green-500 to-neutral-900" },
  { name: "minimalist", pri: "#18181b", sec: "#71717a", acc: "#09090b", border: "#18181b", badgeBg: "rgba(24,24,27,0.08)", badgeText: "#18181b", gradient: "from-neutral-200 to-neutral-400" },
  { name: "lavender", pri: "#a78bfa", sec: "#c084fc", acc: "#c084fc", border: "#a78bfa", badgeBg: "rgba(167,139,250,0.15)", badgeText: "#c084fc", gradient: "from-violet-500 to-purple-900" },
];

export function getSeriesTheme(sessionId: string | null, topicTheme?: string | null): typeof SERIES_THEMES[0] {
  const seed = (topicTheme && topicTheme.trim()) || sessionId;
  if (!seed) return SERIES_THEMES[0];

  if (topicTheme) {
    const topicLower = topicTheme.toLowerCase();
    if (topicLower.includes("gpt") || topicLower.includes("claude") || topicLower.includes("gemini") || topicLower.includes("openai") || topicLower.includes("anthropic") || topicLower.includes("llm") || topicLower.includes("model") || topicLower.includes("ai model")) {
      return SERIES_THEMES.find(t => t.name === "aurora") || SERIES_THEMES[0];
    }
    if (topicLower.includes("open source") || topicLower.includes("github") || topicLower.includes("repo") || topicLower.includes("open-source")) {
      return SERIES_THEMES.find(t => t.name === "forest") || SERIES_THEMES[0];
    }
    if (topicLower.includes("business") || topicLower.includes("startup") || topicLower.includes("deal") || topicLower.includes("policy") || topicLower.includes("law") || topicLower.includes("regulation") || topicLower.includes("acquisition")) {
      return SERIES_THEMES.find(t => t.name === "obsidian") || SERIES_THEMES[0];
    }
    if (topicLower.includes("code") || topicLower.includes("developer") || topicLower.includes("programming") || topicLower.includes("devops") || topicLower.includes("terminal") || topicLower.includes("hack")) {
      return SERIES_THEMES.find(t => t.name === "retro") || SERIES_THEMES[0];
    }
  }

  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;
  }
  return SERIES_THEMES[Math.abs(hash) % SERIES_THEMES.length];
}

export function buildDayPrompt(
  day: SeriesDay,
  plan: SeriesPlan,
  platform: string,
  qpSessionId: string | null,
  selectedThemeName?: string
): string {
  const intent = plan.intent || {} as any;
  const topic = intent.topic_theme || "AI & Tech";
  const audience = intent.target_audience || "AI enthusiasts, developers, tech professionals";
  const difficulty = intent.difficulty_level || "intermediate";
  const totalDays = plan.days?.length || 1;

  const defaultThemeName = intent.topic_theme
    ? getSeriesTheme(null, intent.topic_theme).name
    : getSeriesTheme(qpSessionId).name;
  const themeName = selectedThemeName || defaultThemeName;
  const theme = SERIES_THEMES.find(t => t.name === themeName) || SERIES_THEMES[0];

  // Provide specific styling instructions based on the selected series theme
  let themeDescription = "";
  if (theme.name === "aurora" || theme.name === "midnight" || theme.name === "ocean") {
    themeDescription = `Modern high-tech and software theme. Dark backgrounds, sleek glowing card borders using ${theme.pri}, soft neon accents using ${theme.acc}, and readable modern body text. Ideal for tech, AI, development, and engineering topics.`;
  } else if (theme.name === "dracula") {
    themeDescription = `Dracula gothic tech theme. Dark charcoal/black backgrounds, rich violet border using ${theme.pri}, vibrant hot fuchsia accents using ${theme.acc}. Mystical and high-contrast styling. Perfect for web development and software engineering.`;
  } else if (theme.name === "nord") {
    themeDescription = `Sleek Arctic Nord theme. Cool gray-blue backgrounds, frosty cyan borders using ${theme.pri}, soft glacier blue/teal accents using ${theme.acc}. Calm, clean code, open-source engineering style.`;
  } else if (theme.name === "obsidian") {
    themeDescription = `Premium Obsidian Gold theme. Ultra-dark obsidian backgrounds, solid metallic gold borders using ${theme.pri}, bright amber highlights using ${theme.acc}. Highly premium and executive feel. Ideal for startup guides, finance, and career development.`;
  } else if (theme.name === "retro") {
    themeDescription = `Retro terminal monochrome theme. Pure black backgrounds, glowing classic phosphor green borders using ${theme.pri}, phosphor accents using ${theme.acc}, monospaced styling. Vintage hacker aesthetic.`;
  } else if (theme.name === "minimalist") {
    themeDescription = `Clean editorial Light Mode theme. Pure white or light gray backgrounds, dark charcoal text using ${theme.sec}, clean black borders using ${theme.pri}, minimalist structural alignment. Academic, highly readable, clean styling.`;
  } else if (theme.name === "lavender") {
    themeDescription = `Soft Lavender and Amethyst theme. Dark violet-gray backgrounds, soft lavender borders using ${theme.pri}, bright amethyst accents using ${theme.acc}. Modern, creative, friendly aesthetic.`;
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

## PREMIUM VISUAL COMPONENT LIBRARY DIRECTIVE
To make the design highly visual, premium, and engaging, you must design and use these reusable visual components with inline CSS styles customized to the selected theme:
1. **Mock Speeches/Tweet Cards**:
   - Styled cards representing social comments, reviews, or quote blocks.
   - Include a profile icon placeholder (an elegant colored circle with initials), display name (e.g., "Developer Pro"), handle (e.g., "@dev_pro"), and a verified badge.
   - A speech bubble indicator tail or standard clean layout with a prominent text body.
2. **Tabbed IDE Code Frames (For Code & Tech)**:
   - A dark, sleek IDE frame with macOS window buttons (red, yellow, green circles on top-left).
   - A top tab bar containing mock tab headers (e.g. \`main.py\`, \`index.js\`, \`styles.css\`), with the active tab styled to match the primary/accent color theme.
   - Syntactically colored code tags inside a \`<pre><code>\` block, styled with monospace font and generous padding.
3. **Pros & Cons / Misconception vs Reality Panels**:
   - Split side-by-side or stacked container cards.
   - "Misconception" card has red border, red warning icon/badge, and strike-through text or red indicator.
   - "Reality" or "Best Practice" card has green border, green checkmark icon/badge, and highlighted text.
4. **Metrics & KPI Showcase Panels**:
   - Grid or row of cards with large bold numbers/metrics (e.g., "10x", "+250%", "4.8ms") in accent/primary color with brief label text below.
5. **Component Breakdown Diagrams**:
   - Containers with clear label badges pointing to internal feature descriptions using thin borders or visual connectors/dots.
6. **Process Timelines**:
   - Vertical or horizontal steps linked with animated or highlighted dashed connector borders, with each step marked by a numbered badge (e.g. "Step 1", "Step 2").
7. **Highlight & Alert Callout Badges**:
   - Colored pills or cards using badgeBg and badgeText, or a glowing accent color border, to instantly draw focus to key insights.

---

## LAYOUT ALTERNATION & STRICT ALIGNMENT CONSTRAINTS (NO OVERLAPPING)
To ensure the output looks professional, well-aligned, and strictly avoids overlapping elements:
1. **Alternating Layout Structure**:
   - You MUST alternate slide layout types to prevent monotony:
     - Slide 1: Cover Layout (Centered headline, visual theme gradient backdrop, large brand header).
     - Slide 2: Split Pain-Point Layout (50% Problem statement card, 50% visual alert/callout box).
     - Slide 3: Code/IDE Frame or Tabbed Diagram component.
     - Slide 4: Split Compare / Misconception vs Reality Panel or Metrics Grid.
     - Slide 5: Process Timeline or Detailed component list.
     - Slide 6: Centered Summary Card with highlight badges.
     - Slide 7: Call to Action (Large bold CTAs, preview text, clean social icons).
2. **Strict Non-Overlapping Layout Rules**:
   - Use **CSS Flexbox** or **Grid** on elements inside the main slide area.
   - NEVER use raw \`position: absolute\` on dynamic text elements (headings, body content) that could expand and overlap.
   - Use relative margins (\`margin-bottom: 20px\`, etc.) and padding to separate blocks cleanly.
   - If using columns, use \`display: flex; gap: 30px;\` to ensure they never overlap.
   - Ensure the slide title, body text, and visual component have dedicated height envelopes:
     - Header/Brand block: top 8% of slide height.
     - Title block: max 15% of slide height.
     - Body text: max 20% of slide height.
     - Visual component / Diagram area: 45% - 55% of slide height (must have container with fixed height/flex-grow).
     - Footer / Swipe indicator: bottom 8% of slide height.
3. **No Overflows & Auto-Scaling**:
   - Slide height is strictly fixed at 1350px. Element sizing, line-heights, and margins must leave enough safe area.
   - If body text is longer, reduce font size slightly (e.g. down to 26px) to fit all components comfortably without overflow or overlap.

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
          btn.innerHTML = \`Rendering Slide \${i+1} of \${slides.length}...\\nThis may take a moment.\`;
          const slide = slides[i];
          
          // Save original styles before screenshotting
          const originalTransform = slide.style.transform;
          const originalMarginBottom = slide.style.marginBottom;
          const originalBorderRadius = slide.style.borderRadius;
          const originalPosition = slide.style.position;
          
          // Temporarily force non-scaled 4:5 layout for html2canvas
          slide.style.transform = 'none';
          slide.style.marginBottom = '0';
          slide.style.borderRadius = '0';
          slide.style.position = 'relative';
          
          // Force layout recalculation
          slide.offsetHeight;
          
          const canvas = await html2canvas(slide, {
            width: 1080,
            height: 1350,
            scale: 2, // 2x high resolution
            useCORS: true,
            allowTaint: true,
            scrollX: 0,
            scrollY: 0,
            windowWidth: 1080,
            windowHeight: 1350
          });
          
          // Restore original responsive styles
          slide.style.transform = originalTransform;
          slide.style.marginBottom = originalMarginBottom;
          slide.style.borderRadius = originalBorderRadius;
          slide.style.position = originalPosition;
          
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


export function buildNewsSlidePrompt(
  day: SeriesDay,
  plan: SeriesPlan,
  platform: string,
  qpSessionId: string | null,
  selectedThemeName?: string
): string {
  const intent = plan.intent || {} as any;
  const topic = intent.topic_theme || "AI & Tech News";
  const audience = intent.target_audience || "AI enthusiasts, developers, tech professionals";
  const difficulty = intent.difficulty_level || "intermediate";

  const defaultThemeName = intent.topic_theme
    ? getSeriesTheme(null, intent.topic_theme).name
    : getSeriesTheme(qpSessionId).name;
  const themeName = selectedThemeName || defaultThemeName;
  const theme = SERIES_THEMES.find(t => t.name === themeName) || SERIES_THEMES[0];

  // Provide specific styling instructions based on the selected series theme
  let themeDescription = "";
  if (theme.name === "aurora" || theme.name === "midnight" || theme.name === "ocean") {
    themeDescription = `Modern high-tech and software theme. Dark backgrounds, sleek glowing card borders using ${theme.pri}, soft neon accents using ${theme.acc}, and readable modern body text. Ideal for tech, AI, development, and engineering topics.`;
  } else if (theme.name === "dracula") {
    themeDescription = `Dracula gothic tech theme. Dark charcoal/black backgrounds, rich violet border using ${theme.pri}, vibrant hot fuchsia accents using ${theme.acc}. Mystical and high-contrast styling. Perfect for web development and software engineering.`;
  } else if (theme.name === "nord") {
    themeDescription = `Sleek Arctic Nord theme. Cool gray-blue backgrounds, frosty cyan borders using ${theme.pri}, soft glacier blue/teal accents using ${theme.acc}. Calm, clean code, open-source engineering style.`;
  } else if (theme.name === "obsidian") {
    themeDescription = `Premium Obsidian Gold theme. Ultra-dark obsidian backgrounds, solid metallic gold borders using ${theme.pri}, bright amber highlights using ${theme.acc}. Highly premium and executive feel. Ideal for startup guides, finance, and career development.`;
  } else if (theme.name === "retro") {
    themeDescription = `Retro terminal monochrome theme. Pure black backgrounds, glowing classic phosphor green borders using ${theme.pri}, phosphor accents using ${theme.acc}, monospaced styling. Vintage hacker aesthetic.`;
  } else if (theme.name === "minimalist") {
    themeDescription = `Clean editorial Light Mode theme. Pure white or light gray backgrounds, dark charcoal text using ${theme.sec}, clean black borders using ${theme.pri}, minimalist structural alignment. Academic, highly readable, clean styling.`;
  } else if (theme.name === "lavender") {
    themeDescription = `Soft Lavender and Amethyst theme. Dark violet-gray backgrounds, soft lavender borders using ${theme.pri}, bright amethyst accents using ${theme.acc}. Modern, creative, friendly aesthetic.`;
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

  // Generate strictly 3-4 slides:
  // Slide 1: Hook (catchy & curiosity-generating)
  // Slide 2: Core News (factual details, benchmarks, release date)
  // Slide 3: Implications (why it matters / takeaway)
  // Slide 4: CTA
  const slides = [
    `### Slide 1: Hook
- **Purpose**: Grab the user's attention instantly. Must be catchy and curiosity-generating.
- **Heading**: ${day.hook || day.title}
- **Body Content**: Breaking AI Update: ${day.title}
- **Visual Concept**: Visual backdrop using theme gradient (${theme.gradient}), large bold headline that stops the scroll, swipe-right chevron icon.
- **Layout**: Centered cover layout with brand header at the top and swipe indicator at the bottom.
- **Slide Explanation & Rationale**: Hook the target audience ("${audience}") on the core news breakthrough.`,
    `### Slide 2: Core News Details
- **Purpose**: Present the raw news facts, features, benchmarks, and details.
- **Heading**: What Happened
- **Body Content**: ${day.key_points.slice(0, 3).join(" | ") || day.teaching_goal}
- **News Release Date Badge**: News Date: ${day.notes || "Recent Breakthrough"}
- **Visual Concept**: Highly structured grid containing key stats, features, or benchmarks. Include a "Breaking Badge" or comparison card if appropriate.
- **Layout**: Clear grid layout, showing 2-3 feature boxes, clean alignment.
- **Slide Explanation & Rationale**: Provide pure technical facts and news details.`,
    `### Slide 3: Implications & Takeaways
- **Purpose**: Detail the implications of this news and why it matters for the AI/tech industry.
- **Heading**: Why It Matters
- **Body Content**: ${day.angle || "How this changes the landscape and what it means for builders, developers, and businesses."}
- **Visual Concept**: Process flow or metric list card. High contrast callout box pointing to key impact.
- **Layout**: Split screen or centered focus card detailing the core implications.
- **Slide Explanation & Rationale**: Connect the news to the viewer's professional or technical interests.`,
    `### Slide 4: Call to Action (CTA)
- **Purpose**: Direct user engagement and conversion.
- **Heading**: ${day.cta || "Save for Reference"}
- **Body Content**: Follow @tech_by_pravesh | Share this news update | Save to read later
- **Visual Concept**: Large, bold call-to-action buttons styled with the theme accent color (${theme.acc}), accompanied by social handle badges.
- **Layout**: CTA slide layout with action items centered in the main visual canvas.
- **Slide Explanation & Rationale**: Prompt the user to save, share, or comment.`
  ];

  const detailedSlides = slides.join("\n\n");
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
- A global sticky control toolbar at the top with a "Download All Slides (ZIP)" button.
- A vertical stack of slide wrappers (e.g. \`<div class="slide-wrapper" id="slide-X">\`).
- Mobile-optimized typography (large, bold, high-contrast)
- STRICT slide count: **exactly 4 slides total**. Do NOT generate 5 or more slides.

---

## News Context
- **News Topic**: "${topic}"
- **Platform**: ${platformLabel}
- **Target Audience**: ${audience}
- **Difficulty Level**: ${difficulty}

---

## CRITICAL: News-Wide Visual Theme Consistency
**ALL slides of this post MUST use the EXACT SAME visual theme (same fonts, styling, structure, and component library).**

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
- **Brand Header**: Top 8% of every slide shows "@tech_by_pravesh" + news category badge + slide counter (e.g., "03/04") in consistent style
- **Footer**: Bottom 8% shows swipe indicator on non-final slides

---

## PREMIUM VISUAL COMPONENT LIBRARY DIRECTIVE (STRICT NO OVERLAPPING & PERFECT ALIGNMENT)
To make the design highly visual, premium, and engaging, you must design and use these reusable visual components with inline CSS styles customized to the selected theme:
1. **Mock Speeches/Tweet Cards**:
   - Styled cards representing social comments, reviews, or quote blocks.
   - Include a profile icon placeholder (an elegant colored circle with initials), display name (e.g., "Developer Pro"), handle (e.g., "@dev_pro"), and a verified badge.
2. **Metrics & KPI Showcase Panels**:
   - Grid or row of cards with large bold numbers/metrics (e.g., "10x", "+250%", "4.8ms") in accent/primary color with brief label text below.
3. **Pros & Cons / Misconception vs Reality Panels**:
   - Split side-by-side or stacked container cards.
4. **Alert/Warning Callout Boxes**:
   - Clean boxes with a warning icon for common warnings/takeaways.

---

## LAYOUT STRUCTURE & STRICT ALIGNMENT CONSTRAINTS (NO OVERLAPPING)
To ensure the output looks professional, well-aligned, and strictly avoids overlapping elements:
1. **Strict Non-Overlapping Layout Rules**:
   - You MUST use **CSS Flexbox** or **Grid** on elements inside the main slide area.
   - **NEVER use raw \`position: absolute\` on dynamic text elements (headings, body content) that could expand and overlap each other.**
   - Make sure all components have perfect alignment, centered columns or grids, and clean padding.
   - Use relative margins (\`margin-bottom: 20px\`, etc.) and padding to separate blocks cleanly.
   - If using columns, use \`display: flex; gap: 30px;\` to ensure they never overlap.
   - Ensure the slide title, body text, and visual component have dedicated height envelopes:
     - Header/Brand block: top 8% of slide height.
     - Title block: max 15% of slide height.
     - Body text: max 20% of slide height.
     - Visual component / Diagram area: 45% - 55% of slide height (must have container with fixed height/flex-grow).
     - Footer / Swipe indicator: bottom 8% of slide height.
2. **No Overflows & Auto-Scaling**:
   - Slide height is strictly fixed at 1350px. Element sizing, line-heights, and margins must leave enough safe area.
   - If body text is longer, reduce font size slightly (e.g. down to 26px) to fit all components comfortably without overflow or overlap.

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
  <title>News Post: ${day.title}</title>
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

  <!-- Sticky control toolbar -->
  <div class="toolbar">
    <button class="download-btn" id="download-zip-btn" onclick="downloadAllJPGs()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
      Download All Slides (ZIP)
    </button>
  </div>

  <div class="deck-container">
    <!-- Generated slides wrapper stack -->
  </div>

  <script>
    async function downloadAllJPGs() {
      const btn = document.getElementById('download-zip-btn');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      
      const zip = new JSZip();
      const slides = document.querySelectorAll('.slide-wrapper');
      
      try {
        for (let i = 0; i < slides.length; i++) {
          btn.innerHTML = \`Rendering Slide \${i+1} of \${slides.length}...\\nThis may take a moment.\`;
          const slide = slides[i];
          
          const originalTransform = slide.style.transform;
          const originalMarginBottom = slide.style.marginBottom;
          const originalBorderRadius = slide.style.borderRadius;
          const originalPosition = slide.style.position;
          
          slide.style.transform = 'none';
          slide.style.marginBottom = '0';
          slide.style.borderRadius = '0';
          slide.style.position = 'relative';
          
          const canvas = await html2canvas(slide, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            logging: false,
            width: 1080,
            height: 1350
          });
          
          slide.style.transform = originalTransform;
          slide.style.marginBottom = originalMarginBottom;
          slide.style.borderRadius = originalBorderRadius;
          slide.style.position = originalPosition;
          
          const imgData = canvas.toDataURL('image/jpeg', 0.95);
          const base64Data = imgData.split(',')[1];
          zip.file(\`slide_\${i+1}.jpg\`, base64Data, {base64: true});
        }
        
        btn.innerHTML = 'Creating ZIP file...';
        const content = await zip.generateAsync({type: 'blob'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(content);
        link.download = 'news_slides_${day.day_number}.zip';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (err) {
        console.error(err);
        alert('Error rendering slides: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  </script>
</body>
</html>
\`\`\`

## Copy-Pasteable Caption & Hashtags:
After the HTML code block, you MUST generate the complete post caption:
- Structured using short, double-spaced paragraphs (1-2 sentences max).
- Start with a compelling hook related to "${day.hook}".
- Mention the news date: **${day.notes || "Today"}**.
- Include 3-5 relevant hashtags (such as #ai, #tech, #artificialintelligence matching the news topic).
- End with a clear call-to-action inviting comments, follows, or shares.
- Clearly label this block: \`### Final Social Media Caption:\` so it can be easily copied.
`;
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
  const [error, setError] = useState<string | null>(null);

  // ── Quick Prompt & News Studio Pipeline State (6-step flow) ──
  const [mode, setMode] = useState<"choose" | "quick" | "news">("choose");
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
  const [qpSelectedTheme, setQpSelectedTheme] = useState<string | null>(null);
  const [copiedPromptId, setCopiedPromptId] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Derive the series theme from the topic title, local storage, or session ID, with deduplication against other sessions
  const getUniqueSeriesThemeName = () => {
    const defaultName = qpPlan?.intent?.topic_theme
      ? getSeriesTheme(null, qpPlan.intent.topic_theme).name
      : getSeriesTheme(qpSessionId).name;

    if (!qpSessionsList || qpSessionsList.length === 0) return defaultName;

    // Collect all theme names currently used by other finalized or active sessions
    const usedThemeNames = new Set<string>();
    qpSessionsList.forEach((s) => {
      // Exclude the current session
      if (s.id === qpSessionId) return;

      // 1. Check if the session has a custom selected theme in localStorage
      const saved = localStorage.getItem(`creative_theme_${s.id}`);
      if (saved) {
        usedThemeNames.add(saved);
        return;
      }

      // 2. Otherwise derive it from the topic title or session ID
      const planTheme = s.series_plan?.intent?.topic_theme;
      if (planTheme) {
        usedThemeNames.add(getSeriesTheme(null, planTheme).name);
      } else if (s.id) {
        usedThemeNames.add(getSeriesTheme(s.id).name);
      }
    });

    // If the default theme name is already used, find the first unused theme in SERIES_THEMES
    if (usedThemeNames.has(defaultName)) {
      const unused = SERIES_THEMES.find(t => !usedThemeNames.has(t.name));
      if (unused) return unused.name;
    }

    return defaultName;
  };

  const defaultThemeName = getUniqueSeriesThemeName();
  const activeThemeName = qpSelectedTheme || (qpSessionId ? localStorage.getItem(`creative_theme_${qpSessionId}`) : null) || defaultThemeName;
  const seriesTheme = SERIES_THEMES.find(t => t.name === activeThemeName) || SERIES_THEMES[0];



  // Fetch previous sessions on load
  const loadPreviousSessions = async () => {
    try {
      const quickRes = await listQuickSessions();
      setQpSessionsList(quickRes.sessions || []);
    } catch (e) {
      console.error("Failed to load previous sessions", e);
    }
  };

  useEffect(() => {
    if (!qpSessionId) {
      loadPreviousSessions();
    }
  }, [qpSessionId]);

  // News Studio start handler (triggers automatic Discovery session creation)
  const handleNewsStart = async () => {
    setQpLoading(true);
    setError(null);
    setQpContentFilter("news");
    setQpSeriesLength(1);
    setQpPlatform("instagram");
    setQpUserTopic("");
    try {
      const res = await startQuickSession(1, "news", "", "instagram");
      setQpSessionId(res.session_id);
      setQpDiscoveryPrompt(res.discovery_prompt);
      setQpStep(1); // Set to step 1 (Prompt Discovery Prompt)
      setMode("news");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to start News Studio");
    } finally {
      setQpLoading(false);
    }
  };

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
      const isNews = res.content_filter === "news";
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
        setQpStep(isNews ? 1 : 2);
      } else {
        setQpStep(1);
      }
      setQpSelectedTheme(null);
      setMode(isNews ? "news" : "quick");
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
    setQpSelectedTheme(null);
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
                SocialHQ
              </h1>
              <p className="text-xs text-slate-500">Educational Content Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono bg-slate-800 text-slate-400 px-3 py-1.5 rounded-lg border border-slate-700">
              {weekId}
            </span>
            {qpSessionId && (
              <button
                onClick={resetQuickPrompt}
                className="text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-slate-700 transition"
              >
                Exit Session
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">{error}</div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* ── MODE CHOOSER ── */}
        {mode === "choose" && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 flex items-center justify-center border border-violet-500/20">
              <Sparkles size={48} className="text-violet-400" />
            </div>
            <div className="text-center max-w-lg">
              <h2 className="text-3xl font-bold mb-3 bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
                SocialHQ
              </h2>
              <p className="text-slate-400 leading-relaxed">
                Choose your workflow to create content that your audience will{" "}
                <strong className="text-violet-400">save</strong>,{" "}
                <strong className="text-pink-400">share</strong>, and{" "}
                <strong className="text-amber-400">learn from</strong>.
              </p>
            </div>

            {/* Mode Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
              {/* News Studio Mode */}
              <div
                onClick={handleNewsStart}
                className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 cursor-pointer hover:border-violet-500/50 hover:bg-slate-900/80 transition group"
              >
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Newspaper size={28} className="text-violet-400" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 mb-2">News Studio</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  Discover trending AI & Tech news, select a post topic, review technical details, and generate visual HTML/CSS slide decks.
                </p>
                <div className="flex items-center gap-1 text-violet-400 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Start News Studio Flow</span>
                  <ChevronRight size={14} />
                </div>
              </div>

              {/* Series Studio Mode */}
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
                <h3 className="text-lg font-bold text-slate-100 mb-2">Series Studio</h3>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  Type a simple series idea, let the AI interpret it, research each day, and edit the planned posts.
                </p>
                <div className="flex items-center gap-1 text-amber-400 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Start Series Studio Flow</span>
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
                <p className="text-xs text-slate-500 mb-5">Completed series and news plans ready for production. Click to load and reuse.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {qpSessionsList.filter((s: any) => s.status === "finalized").map((session: any) => {
                    const platformLabels: Record<string, string> = { instagram: "Instagram", linkedin: "LinkedIn", x: "X" };
                    const platformColors: Record<string, string> = { instagram: "#E1306C", linkedin: "#0A66C2", x: "#1DA1F2" };
                    const plat = session.platform || "instagram";
                    const isNews = session.content_filter === "news";
                    return (
                      <div
                        key={session.id}
                        onClick={() => handleLoadQuickSession(session.id)}
                        className={`bg-slate-900/40 border rounded-2xl p-5 cursor-pointer hover:bg-slate-900/60 transition group ${isNews ? "border-violet-500/15 hover:border-violet-500/40" : "border-emerald-500/15 hover:border-emerald-500/40"}`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full border" style={{ color: platformColors[plat], borderColor: platformColors[plat] + "40", backgroundColor: platformColors[plat] + "10" }}>
                              {platformLabels[plat] || plat}
                            </span>
                            <span className="text-xs text-slate-500">{session.series_length} {isNews ? "post" : "days"}</span>
                          </div>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${isNews ? "bg-violet-500/10 text-violet-400 border-violet-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}`}>
                            {isNews ? "News" : "Series"}
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
                          <div className={`flex items-center gap-1 font-medium opacity-0 group-hover:opacity-100 transition-opacity ${isNews ? "text-violet-400" : "text-emerald-400"}`}>
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

            {/* In Progress Sessions */}
            {qpSessionsList.filter((s: any) => s.status !== "finalized").length > 0 && (
              <div className="w-full max-w-4xl mt-10 pt-10 border-t border-slate-800/80">
                <h3 className="text-lg font-bold text-slate-300 mb-5 flex items-center gap-2">
                  <Calendar size={18} className="text-slate-500" />
                  Previous Sessions
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {qpSessionsList.filter((s: any) => s.status !== "finalized").map((session: any) => {
                    const isNews = session.content_filter === "news";
                    return (
                      <div
                        key={session.id}
                        onClick={() => handleLoadQuickSession(session.id)}
                        className={`bg-slate-900/40 border rounded-2xl p-5 cursor-pointer hover:bg-slate-900/60 transition group flex flex-col justify-between ${isNews ? "border-violet-500/15 hover:border-violet-500/40" : "border-amber-500/15 hover:border-amber-500/40"}`}
                      >
                        <div>
                          <div className="flex justify-between items-start mb-3">
                            <span className={`text-xs font-semibold px-2.5 py-1 rounded border capitalize ${isNews ? "bg-violet-500/10 text-violet-400 border-violet-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20"}`}>
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
                          <div className={`flex items-center gap-1 font-medium opacity-0 group-hover:opacity-100 transition-opacity ${isNews ? "text-violet-400" : "text-amber-400"}`}>
                            <span>Continue</span>
                            <ChevronRight size={14} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {(mode === "quick" || mode === "news") && (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <button
                  onClick={resetQuickPrompt}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-800 hover:text-slate-200 text-xs font-semibold text-slate-400 transition cursor-pointer"
                >
                  <ArrowLeft size={12} className="flex-shrink-0" />
                  <span>Back</span>
                </button>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  mode === "news" 
                    ? "bg-gradient-to-br from-violet-500/20 to-indigo-600/20" 
                    : "bg-gradient-to-br from-amber-500/20 to-orange-600/20"
                }`}>
                  {mode === "news" ? (
                    <Newspaper size={16} className="text-violet-400" />
                  ) : (
                    <Wand2 size={16} className="text-amber-400" />
                  )}
                </div>
                <h2 className={`text-lg font-bold bg-gradient-to-r bg-clip-text text-transparent ${
                  mode === "news"
                    ? "from-violet-300 to-indigo-300"
                    : "from-amber-300 to-orange-300"
                }`}>
                  {mode === "news" ? "News Studio Pipeline" : "Series Studio Pipeline"}
                </h2>
              </div>
              {/* Step indicator — clickable for completed steps */}
              <div className="flex items-center gap-1.5">
                {[
                  { n: 1, label: mode === "news" ? "Prompt" : "Input" },
                  { n: 2, label: "Discover" },
                  { n: 3, label: "Pick" },
                  { n: 4, label: "Research" },
                  { n: 5, label: "Review" },
                  { n: 6, label: mode === "news" ? "Slides" : "Prompt" },
                ].map(({ n, label }) => {
                  const isClickable = n <= qpStep && n !== qpStep;
                  const borderClass = qpStep >= n
                    ? (mode === "news" ? "bg-violet-500/20 border-violet-500 text-violet-400" : "bg-amber-500/20 border-amber-500 text-amber-400")
                    : "border-slate-700 text-slate-600";
                  
                  const ringClass = isClickable
                    ? (mode === "news"
                      ? "cursor-pointer hover:scale-110 hover:bg-violet-500/30 hover:shadow-md hover:shadow-violet-500/20"
                      : "cursor-pointer hover:scale-110 hover:bg-amber-500/30 hover:shadow-md hover:shadow-amber-500/20")
                    : (n === qpStep ? (mode === "news" ? "ring-2 ring-violet-400/30" : "ring-2 ring-amber-400/30") : "");

                  return (
                    <div key={n} className="flex items-center gap-1">
                      <button
                        onClick={() => { if (isClickable) setQpStep(n as 1 | 2 | 3 | 4 | 5 | 6); }}
                        disabled={!isClickable}
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold border-2 transition-all ${borderClass} ${ringClass}`}
                      >
                        {qpStep > n ? <Check size={12} /> : n}
                      </button>
                      <span className={`text-[10px] font-medium hidden xl:inline ${
                        isClickable 
                          ? (mode === "news" ? "text-violet-400 cursor-pointer hover:text-violet-300" : "text-amber-400 cursor-pointer hover:text-amber-300") 
                          : (qpStep >= n ? (mode === "news" ? "text-violet-400" : "text-amber-400") : "text-slate-600")
                      }`}
                        onClick={() => { if (isClickable) setQpStep(n as 1 | 2 | 3 | 4 | 5 | 6); }}
                      >{label}</span>
                      {n < 6 && <div className={`w-4 h-0.5 rounded ${qpStep > n ? (mode === "news" ? "bg-violet-500/40" : "bg-amber-500/40") : "bg-slate-800"}`} />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* — Step 1: Flexible Input (Topic + Length + Optional Filter) OR News Discovery Prompt — */}
            {qpStep === 1 && (
              mode === "news" ? (
                <div className="max-w-2xl mx-auto space-y-4">
                  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold text-violet-300 flex items-center gap-2">
                        <Newspaper size={18} /> News Discovery Prompt
                      </h3>
                      <button onClick={() => qpCopyPrompt(qpDiscoveryPrompt, setQpCopied)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 rounded-lg text-xs font-semibold transition">
                        {qpCopied ? <Check size={14} /> : <Copy size={14} />}
                        {qpCopied ? "Copied!" : "Copy Prompt"}
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 mb-2">
                      Copy this pre-built prompt into <strong>Perplexity</strong> to discover the latest AI and Tech news stories.
                    </p>
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 max-h-[35vh] overflow-y-auto whitespace-pre-wrap leading-relaxed">
                      {qpDiscoveryPrompt}
                    </div>
                    <button onClick={() => setQpStep(2)}
                      className="mt-4 w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-violet-500/20 flex items-center justify-center gap-2">
                      <span>Continue to Discover Step</span>
                      <ArrowRight size={18} />
                    </button>
                  </div>
                </div>
              ) : (
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
            ))}

            {/* ── Step 2: Topic Discovery Prompt + Paste ── */}
            {qpStep === 2 && (
              <div className="space-y-4">
                {mode !== "news" && (
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
                )}
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className={`text-lg font-bold flex items-center gap-2 mb-3 ${mode === "news" ? "text-violet-300" : "text-emerald-300"}`}>
                      <ArrowRight size={18} /> Paste Perplexity Results
                    </h3>
                    {mode === "news" && (
                      <button onClick={() => qpCopyPrompt(qpDiscoveryPrompt, setQpCopied)}
                        className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition border border-slate-700">
                        {qpCopied ? <Check size={10} /> : <Copy size={10} />}
                        <span>View Discovery Prompt</span>
                      </button>
                    )}
                  </div>
                  <textarea value={qpPastedTopics} onChange={(e) => setQpPastedTopics(e.target.value)}
                    placeholder="Paste the response from Perplexity here..."
                    className="w-full h-[25vh] bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 resize-none focus:outline-none focus:border-violet-500/50 transition" />
                  <button onClick={handleQpSubmitTopics} disabled={qpLoading || !qpPastedTopics.trim()}
                    className={`mt-3 w-full font-bold py-3 px-6 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-40 ${
                      mode === "news"
                        ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-500/20"
                        : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20"
                    }`}>
                    {qpLoading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                    Parse & Show Topics
                  </button>
                </div>
              </div>
            )}

            {/* ── Step 3: Topic Selection ── */}
            {qpStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    <TrendingUp size={18} className={mode === "news" ? "text-violet-400" : "text-amber-400"} /> 
                    {mode === "news" ? "Select a News Topic for Your Slide Deck" : "Select a Topic for Your Series"}
                  </h3>
                  <span className="text-xs text-slate-500">{qpDiscoveredTopics.length} topics discovered</span>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {qpDiscoveredTopics.map((topic) => {
                    return (
                      <div key={topic.id} onClick={() => handleQpSelectTopic(topic.id)}
                        className={`bg-slate-900/60 border border-slate-800 rounded-2xl p-5 cursor-pointer transition-all hover:scale-[1.005] ${
                          mode === "news" ? "hover:border-violet-500/40" : "hover:border-amber-500/40"
                        }`}>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                              <h4 className="font-bold text-slate-100 text-base">{topic.title}</h4>
                              {topic.relevance_score > 0 && (
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                  mode === "news" 
                                    ? "bg-violet-500/15 text-violet-400 border-violet-500/20" 
                                    : "bg-amber-500/15 text-amber-400 border-amber-500/20"
                                }`}>
                                  {topic.relevance_score.toFixed(1)}
                                </span>
                              )}
                            </div>

                            {/* News Date */}
                            <div className="flex items-center gap-2 mb-2.5 px-3 py-1.5 rounded-xl bg-slate-950/45 border border-slate-800/50 text-xs w-fit">
                              <Calendar size={12} className={`${mode === "news" ? "text-violet-400" : "text-amber-400"} flex-shrink-0`} />
                              <span className="font-semibold text-slate-300">
                                {topic.news_date ? `News Date: ${topic.news_date}` : "News Date: Unknown"}
                              </span>
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
                          <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center border ${
                            mode === "news" 
                              ? "bg-violet-500/10 border-violet-500/20 text-violet-400" 
                              : "bg-amber-500/10 border-amber-500/20 text-amber-400"
                          }`}>
                            {qpLoading ? <Loader size={16} className="animate-spin" /> : <ArrowRight size={16} />}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ── Step 4: Deep Research Prompt + Paste ── */}
            {qpStep === 4 && (
              <div className="space-y-4">
                {qpSelectedTopic && (
                  <div className={`border rounded-2xl p-4 ${
                    mode === "news" ? "bg-violet-500/5 border-violet-500/20" : "bg-amber-500/5 border-amber-500/20"
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp size={14} className={mode === "news" ? "text-violet-400" : "text-amber-400"} />
                      <span className={`text-xs font-bold ${mode === "news" ? "text-violet-400" : "text-amber-400"}`}>Selected Topic</span>
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
                  <h3 className={`text-lg font-bold flex items-center gap-2 mb-3 ${mode === "news" ? "text-violet-300" : "text-emerald-300"}`}>
                    <ArrowRight size={18} /> Paste Research Results
                  </h3>
                  <textarea value={qpPastedResearch} onChange={(e) => setQpPastedResearch(e.target.value)}
                    placeholder="Paste the response from Claude/Perplexity here..."
                    className="w-full h-[20vh] bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 resize-none focus:outline-none focus:border-violet-500/50 transition" />
                  <button onClick={handleQpSubmitResearch} disabled={qpLoading || !qpPastedResearch.trim()}
                    className={`mt-3 w-full font-bold py-3 px-6 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-40 ${
                      mode === "news"
                        ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-500/20"
                        : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20"
                    }`}>
                    {qpLoading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                    Parse & Review Plan
                  </button>
                </div>
              </div>
            )}

            {/* Step 5: Day-by-Day Review + Per-Day Prompt Carousel */}
            {qpStep === 5 && qpPlan && (() => {
              const activeDay = qpPlan.days.find(d => d.day_number === qpActivePromptDay) || qpPlan.days[0];
              const dayPrompt = activeDay 
                ? (mode === "news"
                  ? buildNewsSlidePrompt(activeDay, qpPlan, qpPlatform, qpSessionId, seriesTheme.name)
                  : buildDayPrompt(activeDay, qpPlan, qpPlatform, qpSessionId, seriesTheme.name))
                : "";
              return (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-4">
                      <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                        <Calendar size={18} style={{ color: seriesTheme.pri }} /> 
                        {mode === "news" ? "News Post Review" : `Series Plan - ${qpPlan.days.length} Days`}
                      </h3>
                      {/* Theme Selector */}
                      <div className="flex items-center gap-2 bg-slate-950/40 border border-slate-800/80 rounded-xl px-2.5 py-1">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Visual Theme:</span>
                        <select
                          value={seriesTheme.name}
                          onChange={(e) => {
                            const val = e.target.value;
                            setQpSelectedTheme(val);
                            if (qpSessionId) {
                              localStorage.setItem(`creative_theme_${qpSessionId}`, val);
                            }
                          }}
                          className="bg-transparent border-none text-xs font-bold focus:outline-none cursor-pointer pr-1"
                          style={{ color: seriesTheme.pri }}
                        >
                          {SERIES_THEMES.map(theme => (
                            <option key={theme.name} value={theme.name} className="bg-slate-900 text-slate-300 font-sans">
                              {theme.name.charAt(0).toUpperCase() + theme.name.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <button onClick={handleQpApprove} disabled={qpLoading}
                      className={`font-bold py-2 px-5 rounded-xl text-sm transition-all shadow-lg flex items-center gap-2 disabled:opacity-40 ${
                        mode === "news"
                          ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-500/20"
                          : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20"
                      }`}>
                      {qpLoading ? <Loader size={16} className="animate-spin" /> : <Check size={16} />}
                      {mode === "news" ? "Approve & Save to HQ Board" : "Approve & Generate Final Prompt"}
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
                                  <span className="text-sm font-bold" style={{ color: seriesTheme.pri }}>
                                    {mode === "news" ? <Newspaper size={16} /> : day.day_number}
                                  </span>
                                </div>
                                <div>
                                  <h4 className="text-base font-bold text-slate-100">{day.title}</h4>
                                  <span className="text-xs text-slate-500">
                                    {mode === "news" ? `News Date: ${day.notes || "Recent"}` : `Day ${day.day_number} - ${day.content_type}`}
                                  </span>
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
                                {day.teaching_goal && (<div><span className="text-xs font-semibold text-violet-400">{mode === "news" ? "News Details: " : "Teaching Goal: "}</span><span className="text-xs text-slate-400">{day.teaching_goal}</span></div>)}
                                {day.angle && (<div><span className="text-xs font-semibold text-emerald-400">{mode === "news" ? "Implications: " : "Angle: "}</span><span className="text-xs text-slate-400">{day.angle}</span></div>)}
                                {day.key_points.length > 0 && (
                                  <div>
                                    <p className="text-xs font-semibold text-violet-400 mb-1">{mode === "news" ? "Key Facts & Details:" : "Key Points:"}</p>
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
              const dayPrompt6 = activeDay6 
                ? (mode === "news"
                  ? buildNewsSlidePrompt(activeDay6, qpPlan, qpPlatform, qpSessionId, seriesTheme.name)
                  : buildDayPrompt(activeDay6, qpPlan, qpPlatform, qpSessionId, seriesTheme.name))
                : "";
              return (
                <div className="space-y-6">
                  {/* Per-Day Carousel */}
                  <div className="bg-slate-900/60 border rounded-2xl p-6 backdrop-blur" style={{ borderColor: `${seriesTheme.border}44`, borderTop: `3px solid ${seriesTheme.border}` }}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: seriesTheme.badgeText }}>
                          <Sparkles size={18} /> {mode === "news" ? "HTML Slide Deck Production Prompt" : "Per-Day Production Prompts"}
                        </h3>
                        {/* Theme Selector */}
                        <div className="flex items-center gap-2 bg-slate-950/40 border border-slate-800/80 rounded-xl px-2.5 py-1">
                          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Visual Theme:</span>
                          <select
                            value={seriesTheme.name}
                            onChange={(e) => {
                              const val = e.target.value;
                              setQpSelectedTheme(val);
                              if (qpSessionId) {
                                localStorage.setItem(`creative_theme_${qpSessionId}`, val);
                              }
                            }}
                            className="bg-transparent border-none text-xs font-bold focus:outline-none cursor-pointer pr-1"
                            style={{ color: seriesTheme.pri }}
                          >
                            {SERIES_THEMES.map(theme => (
                              <option key={theme.name} value={theme.name} className="bg-slate-900 text-slate-300 font-sans">
                                {theme.name.charAt(0).toUpperCase() + theme.name.slice(1)}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      {mode !== "news" && (
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
                      )}
                    </div>

                    <p className="text-sm text-slate-500 mb-3">
                      <strong style={{ color: seriesTheme.acc }}>{activeDay6?.title}</strong> - {mode === "news" ? "Copy this into Claude, Gemini, or GPT to generate the final HTML/CSS/JS slide deck." : `Copy this into Claude, Gemini, or GPT to generate Day ${qpActivePromptDay}'s content.`}
                    </p>

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
                      {copiedPromptId === qpActivePromptDay ? "Copied!" : `Copy Slide Production Prompt`}
                    </button>
                  </div>

                  {/* Full Production Prompt (collapsible) - Hide for News mode as it's redundant */}
                  {mode !== "news" && qpProductionPrompt && (
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
                    <button onClick={resetQuickPrompt} className={`flex-1 font-semibold py-2.5 px-4 rounded-xl text-sm transition shadow-lg ${
                      mode === "news"
                        ? "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-violet-500/20"
                        : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-emerald-500/20"
                    }`}>Start New Session</button>
                  </div>
                </div>
              );
            })()}

            {/* Floating Chat Assistant (bottom right, Steps 2-6) */}
            {(mode === "quick" || mode === "news") && qpStep >= 2 && (
              <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3 w-[380px] max-w-[90vw]">
                {/* Chat History (expanded) */}
                {qpChatOpen && (
                  <div className="bg-slate-900/95 border border-slate-700 rounded-2xl backdrop-blur-xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col" style={{ height: "400px" }}>
                    <div className="p-3 bg-slate-950/40 border-b border-slate-800 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <MessageSquare size={14} className={mode === "news" ? "text-violet-400" : "text-amber-400"} />
                        <h4 className={`text-xs font-bold ${mode === "news" ? "text-violet-300" : "text-amber-300"}`}>
                          {mode === "news" ? "News Studio Assistant" : "Series Studio Assistant"}
                        </h4>
                      </div>
                      <button onClick={() => setQpChatOpen(false)} className="text-slate-500 hover:text-slate-300 text-xs transition">Close</button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-3 space-y-2">
                      {qpChatHistory.length === 0 && (
                        <div className="text-xs text-slate-600 text-center py-4">
                          <Sparkles size={20} className={`mx-auto mb-2 ${mode === "news" ? "text-violet-400/50" : "text-amber-400/50"}`} />
                          <p className="mb-1.5">Try saying:</p>
                          <div className="space-y-1 text-slate-500">
                            {qpStep < 5 ? (
                              mode === "news" ? (
                                <><p>"Focus on developer implications"</p><p>"Explain benchmarks more deeply"</p></>
                              ) : (
                                <><p>"Focus more on practical tutorials"</p><p>"I want beginner-friendly content"</p></>
                              )
                            ) : (
                              mode === "news" ? (
                                <><p>"Make the hook catchier"</p><p>"Add a slide about performance comparisons"</p></>
                              ) : (
                                <><p>"Improve the hook for day 2"</p><p>"Change day 3 to a reel"</p><p>"Swap day 1 and day 4"</p></>
                              )
                            )}
                          </div>
                        </div>
                      )}
                      {qpChatHistory.map((msg, i) => (
                        <div key={i} className={`text-xs rounded-xl p-2.5 max-w-[85%] ${
                          msg.role === "user" 
                            ? (mode === "news" ? "bg-violet-500/10 text-violet-200 border border-violet-500/20 ml-auto" : "bg-amber-500/10 text-amber-200 border border-amber-500/20 ml-auto") 
                            : "bg-slate-800 text-slate-300 border border-slate-700"
                        }`}>
                          {msg.message}
                        </div>
                      ))}
                      <div ref={chatEndRef} />
                    </div>
                    {/* Chat Input Inside Drawer */}
                    <div className="p-2.5 bg-slate-950/80 border-t border-slate-800 flex gap-2 items-center">
                      <input type="text" value={qpChatMsg} onChange={(e) => setQpChatMsg(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleQpChat(); }}
                        placeholder={qpStep < 5 ? "Ask questions or leave notes..." : "Edit the plan with natural language..."}
                        className={`flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 focus:outline-none transition placeholder-slate-600 ${
                          mode === "news" ? "focus:border-violet-500/50" : "focus:border-amber-500/50"
                        }`} />
                      <button onClick={handleQpChat} disabled={qpLoading || !qpChatMsg.trim()}
                        className={`w-8 h-8 rounded-xl flex items-center justify-center text-white transition disabled:opacity-40 shrink-0 ${
                          mode === "news"
                            ? "bg-violet-600 hover:bg-violet-500 shadow-violet-500/20"
                            : "bg-amber-600 hover:bg-amber-500 shadow-amber-500/20"
                        }`}>
                        {qpLoading ? <Loader size={12} className="animate-spin" /> : <Send size={12} />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Floating Chat Bubble Toggle Button */}
                <button onClick={() => setQpChatOpen(!qpChatOpen)} 
                  className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-all transform hover:scale-105 shrink-0 relative ${
                    qpChatOpen 
                      ? (mode === "news" ? "bg-slate-800 text-violet-400 border border-slate-700 hover:bg-slate-700" : "bg-slate-800 text-amber-400 border border-slate-700 hover:bg-slate-700") 
                      : (mode === "news"
                        ? "bg-gradient-to-r from-violet-500 to-indigo-500 hover:from-violet-400 hover:to-indigo-400 text-white shadow-violet-500/20"
                        : "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 shadow-amber-500/20")
                  }`}>
                  <MessageSquare size={20} />
                  {qpChatHistory.length > 0 && !qpChatOpen && (
                    <span className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full" />
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
