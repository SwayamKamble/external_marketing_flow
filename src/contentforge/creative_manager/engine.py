"""Creative Manager Engine – Topic discovery, scoring, and weekly planning.

Educational-first approach: every topic is evaluated by how well it can
TEACH the audience something actionable, not just inform them about news.

Scoring heuristics emphasize:
- Shareability: "I need to show this to someone"
- Saveability: "I'll come back to this later"
- Educational value: "I learned something I can use today"
- Conversation: "I have an opinion on this"
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any

from contentforge.creative_manager.models import (
    CreativeSession,
    DayPlan,
    EngagementScores,
    PlatformAngle,
    TopicIdea,
)


# ─────────────────────────────────────────────────────────
# Research prompt template (educational focus)
# ─────────────────────────────────────────────────────────

_COPYWRITING_SYSTEM_PROMPT = """You are a senior AI & Technology News Research Strategist for an educational AI & Tech brand on social media (@tech_by_pravesh).

Your goal: Find the most important, credible, recent, and highly relevant AI and technology news stories that are worth creating content about today.

## Core Objective

Identify ONLY real news stories related to:

* Artificial Intelligence
* Generative AI
* AI Agents
* LLMs
* Robotics
* Software Engineering
* AI Infrastructure
* AI Startups
* AI Research
* Open Source AI
* Developer Tools
* AI Automation
* Semiconductor & AI Chips
* Cloud AI Platforms
* Emerging Technology
* Cybersecurity related to AI
* AI Policy & Regulation
* AGI Research
* Enterprise AI Adoption

The news must be:

* Recent
* Factually verified
* From credible sources
* Currently being discussed by the tech community
* Valuable enough to create educational content around
* Relevant to students, engineers, founders, creators, professionals, and AI enthusiasts

---

## STRICT NEWS RULES

ONLY include actual news.

DO NOT include:

* Evergreen educational topics
* Tutorials
* Framework explanations
* General AI concepts
* Productivity advice
* Career advice
* Tool lists
* Opinion-only content
* Motivational content
* Historical events
* Generic trend reports without a specific news trigger

Every item MUST be tied to a real news event.

---

## RECENCY REQUIREMENTS

Only include news published within the last 14 days.

Prioritize:

* Last 24 hours
* Last 3 days
* Last 7 days

If no high-quality stories exist in the last 24 hours, expand to 14 days.

Older stories must be rejected.

---

## SOURCE QUALITY RULES

Only use information from highly credible sources such as:

* OpenAI
* Anthropic
* Google
* Microsoft
* Meta
* NVIDIA
* xAI
* Hugging Face
* Mistral
* DeepMind
* AWS
* GitHub
* Official Company Blogs
* Research Papers
* ArXiv
* Reuters
* Bloomberg
* TechCrunch
* The Verge
* VentureBeat
* Wired
* MIT Technology Review

Avoid low-quality sources.

---

## NEWS SELECTION CRITERIA

A story should only be selected if it satisfies at least one:

* Major AI breakthrough
* Significant product release
* Important model launch
* Major research publication
* New AI capability
* Enterprise AI adoption milestone
* AI regulation update
* Significant AI partnership
* Open-source AI release
* AI infrastructure development
* Robotics advancement
* AI safety development
* Major benchmark achievement
* Industry-changing announcement

---

## VIRALITY & CONTENT POTENTIAL SCORING

Score every story:

* newsworthiness (1-10)
* viral_potential (1-10)
* educational_value (1-10)
* discussion_potential (1-10)
* shareability (1-10)
* relevance_to_ai_audience (1-10)

Only include stories where:

* newsworthiness >= 8
* educational_value >= 8
* relevance_to_ai_audience >= 8
* viral_potential >= 7

---

## REQUIRED RESEARCH

For every story provide:

### News Details

* exact headline
* company/organization
* announcement date
* publication date
* source name
* source URL

### Story Summary

Explain:

* What happened
* Why it matters
* What changed
* Who is affected
* Potential impact

### Educational Breakdown

Explain:

* Underlying technology
* Industry significance
* Long-term implications
* Opportunities created
* Risks or limitations

### Content Creation Potential

Explain:

* Why people would care
* Why it is worth posting
* What audience segment it targets
* What educational angle should be used

---

## PLATFORM MATCHING

For each story determine the best platforms:

* instagram
* linkedin
* x

Only include platforms where the story naturally fits.

Provide:

* why_it_works
* recommended_format
* primary_goal

Formats:

Instagram:

* carousel
* reel
* infographic
* news_carousel

LinkedIn:

* carousel
* document
* article

X:

* thread
* visual_thread
* news_thread

---

## REQUIRED OUTPUT FORMAT

Return STRICTLY VALID JSON ONLY.

No markdown.
No explanations.
No notes.
No commentary.
No code blocks.

Return:

[
{
"headline": "",
"company": "",
"announcement_date": "",
"publication_date": "",
"source_name": "",
"source_url": "",
"news_category": "",
"summary": "",
"why_it_matters": "",
"educational_breakdown": {
"technology_involved": "",
"industry_significance": "",
"long_term_impact": "",
"opportunities": [],
"risks_or_limitations": []
},
"content_potential": {
"why_people_will_care": "",
"why_it_is_worth_posting": "",
"target_audience": [],
"recommended_educational_angle": ""
},
"best_platforms": ["instagram","linkedin","x"],
"platform_strategy": {
"instagram": {
"why_it_works": "",
"recommended_format": "",
"primary_goal": ""
},
"linkedin": {
"why_it_works": "",
"recommended_format": "",
"primary_goal": ""
},
"x": {
"why_it_works": "",
"recommended_format": "",
"primary_goal": ""
}
},
"scores": {
"newsworthiness": 9,
"viral_potential": 9,
"educational_value": 9,
"discussion_potential": 9,
"shareability": 9,
"relevance_to_ai_audience": 10
},
"suggested_hooks": {
"instagram": "",
"linkedin": "",
"x": ""
}
}
]

## FINAL FILTER

Before returning any story, verify:

* It is real news.
* It happened recently.
* It is not an evergreen topic.
* It comes from a reliable source.
* It has genuine educational value.
* It is relevant to AI and technology.
* It is likely to interest the AI community.
* It is worthy of being turned into a social media post.

Return only the highest-quality AI and technology news stories available right now.

"""



# ─────────────────────────────────────────────────────────
# Keyword-based engagement scoring heuristics
# ─────────────────────────────────────────────────────────

_SAVEABLE_KEYWORDS = {
    "how to", "guide", "tutorial", "step by step", "cheat sheet", "framework",
    "template", "checklist", "tips", "tricks", "workflow", "process", "method",
    "strategy", "playbook", "blueprint", "roadmap", "reference", "learn",
    "masterclass", "breakdown", "explained", "deep dive", "crash course",
}

_SHAREABLE_KEYWORDS = {
    "surprising", "most people", "nobody talks about", "underrated", "myth",
    "misconception", "truth about", "mistake", "wrong", "better way", "secret",
    "changed my mind", "game-changing", "overlooked", "hidden", "powerful",
    "mind-blowing", "simple trick", "one thing", "stop doing",
}

_CONVERSATION_KEYWORDS = {
    "opinion", "debate", "controversial", "unpopular", "hot take", "vs",
    "versus", "compare", "which is better", "should you", "is it worth",
    "agree or disagree", "what do you think", "overrated", "underrated",
    "prediction", "future of",
}

_EDUCATIONAL_KEYWORDS = {
    "learn", "teach", "explain", "understand", "concept", "how", "why",
    "what is", "beginner", "advanced", "fundamentals", "basics", "deep dive",
    "architecture", "system design", "algorithm", "pattern", "principle",
    "best practice", "anti-pattern", "common mistake", "pitfall",
}

_VIRAL_KEYWORDS = {
    "everyone", "no one", "most people", "99%", "first time", "never",
    "always", "breaking", "just", "finally", "insane", "crazy", "wild",
    "leaked", "revealed", "exposed", "proof", "real reason",
}


def _keyword_score(text: str, keywords: set[str]) -> float:
    """Score 0-10 based on keyword density in text."""
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw in lower)
    # Normalize: 0 hits = 2, 1 hit = 5, 2 hits = 7, 3+ hits = 8-10
    if hits == 0:
        return 2.0
    if hits == 1:
        return 5.0
    if hits == 2:
        return 7.0
    return min(10.0, 7.5 + hits * 0.5)


def _category_multiplier(category: str) -> dict[str, float]:
    """Boost scores based on category characteristics."""
    cat = category.lower().strip()
    defaults = {"save": 1.0, "share": 1.0, "convo": 1.0, "edu": 1.0, "viral": 1.0}

    if cat in ("how-to", "tutorial", "guide"):
        return {**defaults, "save": 1.4, "edu": 1.3}
    if cat in ("cheat-sheet", "reference", "checklist"):
        return {**defaults, "save": 1.5, "share": 1.2, "edu": 1.2}
    if cat in ("framework", "concept", "architecture"):
        return {**defaults, "save": 1.3, "edu": 1.4, "share": 1.1}
    if cat in ("myth-buster", "misconception"):
        return {**defaults, "share": 1.4, "convo": 1.3, "viral": 1.2}
    if cat in ("case-study", "behind-the-scenes"):
        return {**defaults, "share": 1.2, "convo": 1.2, "edu": 1.2}
    if cat in ("trend-analysis",):
        return {**defaults, "convo": 1.3, "share": 1.2}
    if cat in ("career", "skills"):
        return {**defaults, "save": 1.3, "share": 1.3, "edu": 1.1}
    if cat in ("tool", "tool-review"):
        return {**defaults, "save": 1.3, "edu": 1.2}
    return defaults


def _platform_format_for_category(category: str) -> dict[str, str]:
    """Suggest best content format per platform based on category."""
    cat = category.lower().strip()
    if cat in ("how-to", "tutorial", "guide", "framework", "concept"):
        return {"instagram": "carousel", "linkedin": "carousel", "x": "thread"}
    if cat in ("cheat-sheet", "reference", "checklist"):
        return {"instagram": "carousel", "linkedin": "single_image", "x": "thread"}
    if cat in ("myth-buster", "misconception"):
        return {"instagram": "carousel", "linkedin": "single_image", "x": "thread"}
    if cat in ("case-study", "behind-the-scenes"):
        return {"instagram": "carousel", "linkedin": "carousel", "x": "thread"}
    if cat in ("tool", "tool-review"):
        return {"instagram": "reel", "linkedin": "carousel", "x": "thread"}
    if cat in ("trend-analysis",):
        return {"instagram": "carousel", "linkedin": "single_image", "x": "thread"}
    if cat in ("career", "skills"):
        return {"instagram": "carousel", "linkedin": "single_image", "x": "thread"}
    return {"instagram": "carousel", "linkedin": "single_image", "x": "thread"}


# ─────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────

class CreativeManagerEngine:
    """Stateless engine for topic discovery, scoring, and planning.

    All methods are deterministic heuristics — no LLM calls.
    The user pastes research from ChatGPT/Perplexity, and this
    engine parses, scores, and plans from it.
    """

    def generate_research_prompt(self, niche: str = "AI & Tech", topic_count: int = 12) -> str:
        """Generate a prompt the user copies into ChatGPT/Perplexity."""
        from datetime import datetime
        current_date_str = datetime.now().strftime("%B %d, %Y")
        return _RESEARCH_PROMPT.format(niche=niche, topic_count=topic_count, current_date=current_date_str)

    def parse_topics(self, raw_text: str) -> list[TopicIdea]:
        """Parse pasted research JSON into TopicIdea objects with scoring."""
        parsed = self._extract_json_array(raw_text)
        if not parsed:
            return []

        topics: list[TopicIdea] = []
        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue

            import uuid
            topic_id = f"tp_{uuid.uuid4().hex[:10]}"
            category = str(item.get("category", "")).strip()
            summary = str(item.get("summary", "")).strip()
            educational_angle = str(item.get("educational_angle", "")).strip()
            teaching_points = item.get("teaching_points", [])
            if not isinstance(teaching_points, list):
                teaching_points = []
            teaching_points = [str(tp).strip() for tp in teaching_points if str(tp).strip()]

            why_it_works = str(item.get("why_it_works", "")).strip()
            if not why_it_works:
                why_it_works = str(item.get("why_it_can_go_viral", "")).strip()

            source = str(item.get("source", "")).strip()
            news_date = str(item.get("news_date", "")).strip()
            if not news_date or news_date.lower() in ("recent", "today", "now", "current", "latest", "unknown", "n/a", "recent breakthrough"):
                news_date = datetime.now().strftime("%B %d, %Y")
            best_platforms = item.get("best_platforms", ["instagram", "linkedin", "x"])
            if not isinstance(best_platforms, list):
                best_platforms = ["instagram", "linkedin", "x"]
            best_platforms = [str(p).strip().lower() for p in best_platforms if str(p).strip()]
            if not best_platforms:
                best_platforms = ["instagram", "linkedin", "x"]

            # Score the topic: Prefer LLM scores if available, otherwise calculate from keywords
            scores_dict = item.get("scores", {})
            if isinstance(scores_dict, dict) and scores_dict:
                viral_raw = float(scores_dict.get("viral_potential", scores_dict.get("virality", 5.0)))
                edu_raw = float(scores_dict.get("educational_value", 5.0))
                share_raw = float(scores_dict.get("shareability", 5.0))
                save_raw = float(scores_dict.get("saveability", 5.0))
                convo_raw = float(scores_dict.get("conversation_potential", scores_dict.get("conversation", 5.0)))
                like_raw = float(scores_dict.get("likeability", (save_raw + share_raw + edu_raw) / 3))
            else:
                blob = f"{title} {summary} {educational_angle} {why_it_works} {' '.join(teaching_points)}"
                multiplier = _category_multiplier(category)

                save_raw = _keyword_score(blob, _SAVEABLE_KEYWORDS) * multiplier["save"]
                share_raw = _keyword_score(blob, _SHAREABLE_KEYWORDS) * multiplier["share"]
                convo_raw = _keyword_score(blob, _CONVERSATION_KEYWORDS) * multiplier["convo"]
                edu_raw = _keyword_score(blob, _EDUCATIONAL_KEYWORDS) * multiplier["edu"]
                viral_raw = _keyword_score(blob, _VIRAL_KEYWORDS) * multiplier["viral"]

                # Teaching points boost educational value
                if len(teaching_points) >= 3:
                    edu_raw = min(10.0, edu_raw + 1.5)
                elif len(teaching_points) >= 2:
                    edu_raw = min(10.0, edu_raw + 0.8)
                like_raw = (save_raw + share_raw + edu_raw) / 3 + 1.0

            # Clamp scores
            save = min(10.0, max(0.0, save_raw))
            share = min(10.0, max(0.0, share_raw))
            like = min(10.0, max(0.0, like_raw))
            convo = min(10.0, max(0.0, convo_raw))
            edu = min(10.0, max(0.0, edu_raw))
            viral = min(10.0, max(0.0, viral_raw))

            # Weighted overall (educational value weighted heavily)
            overall = round(
                save * 0.20 + share * 0.15 + like * 0.10 + convo * 0.15 + edu * 0.30 + viral * 0.10,
                1,
            )

            scores = EngagementScores(
                shareability=round(share, 1),
                saveability=round(save, 1),
                likeability=round(like, 1),
                conversation=round(convo, 1),
                virality=round(viral, 1),
                educational_value=round(edu, 1),
                overall=overall,
            )

            # Build platform angles
            suggested_hooks = item.get("suggested_hooks", {})
            suggested_angles = item.get("suggested_angles", {})
            suggested_formats = item.get("suggested_formats", {})
            platform_strategy = item.get("platform_strategy", {})
            default_formats = _platform_format_for_category(category)

            platform_angles: list[PlatformAngle] = []
            for plat in ("instagram", "linkedin", "x"):
                hook = ""
                angle = ""
                fmt = ""

                # Try root-level mappings first
                if isinstance(suggested_hooks, dict):
                    hook = str(suggested_hooks.get(plat, "")).strip()
                if isinstance(suggested_angles, dict):
                    angle = str(suggested_angles.get(plat, "")).strip()
                if isinstance(suggested_formats, dict):
                    fmt = str(suggested_formats.get(plat, "")).strip()

                # Fallback to platform_strategy if present
                if isinstance(platform_strategy, dict) and plat in platform_strategy:
                    plat_strat = platform_strategy[plat]
                    if isinstance(plat_strat, dict):
                        if not hook:
                            hook = str(plat_strat.get("hook", "")).strip()
                        if not angle:
                            angle = str(plat_strat.get("why_it_works", plat_strat.get("angle", ""))).strip()
                        if not fmt:
                            fmt = str(plat_strat.get("best_format", plat_strat.get("format", ""))).strip()

                if not fmt:
                    fmt = default_formats.get(plat, "carousel")

                # Generate teaching approach per platform
                if plat == "instagram":
                    teaching = "Visual step-by-step with clear takeaways on each slide"
                elif plat == "linkedin":
                    teaching = "Professional insight with data and actionable framework"
                else:
                    teaching = "Punchy thread with one key lesson per tweet"

                platform_angles.append(PlatformAngle(
                    platform=plat,
                    hook=hook,
                    angle=angle,
                    format=fmt,
                    teaching_approach=teaching,
                    estimated_engagement="high" if overall >= 6.5 else ("medium" if overall >= 4.5 else "low"),
                ))

            topics.append(TopicIdea(
                id=topic_id,
                title=title,
                summary=summary,
                category=category,
                source=source,
                news_date=news_date,
                educational_angle=educational_angle,
                why_it_works=why_it_works,
                teaching_points=teaching_points,
                best_platforms=best_platforms,
                engagement_scores=scores,
                platform_angles=platform_angles,
            ))

        # Sort by overall score descending
        topics.sort(key=lambda t: t.engagement_scores.overall, reverse=True)
        return topics

    def plan_week(self, topics: list[TopicIdea], week_id: str) -> list[DayPlan]:
        """Generate a 7-day content calendar from selected topics.

        Strategy:
        - Mon/Thu: Instagram carousel (savable educational deep-dive)
        - Tue: LinkedIn insight (professional teaching)
        - Wed: Instagram reel (reach through quick education)
        - Fri: X thread (timely educational breakdown)
        - Sat: LinkedIn carousel (weekend learning)
        - Sun: Instagram single_image (lighter educational recap)
        """
        if not topics:
            return []

        # Parse week_id to get dates
        try:
            year, week_num = week_id.split("-W")
            # Monday of that ISO week
            monday = datetime.strptime(f"{year}-W{int(week_num)}-1", "%Y-W%W-%w")
        except Exception:
            monday = datetime.now()

        day_slots = [
            ("monday", "instagram", "carousel", "educate", "Deep-dive educational carousel"),
            ("tuesday", "linkedin", "single_image", "teach", "Professional insight post"),
            ("wednesday", "instagram", "reel", "demonstrate", "Quick visual tutorial"),
            ("thursday", "instagram", "carousel", "explain", "Step-by-step guide"),
            ("friday", "x", "thread", "educate", "Educational thread breakdown"),
            ("saturday", "linkedin", "carousel", "teach", "Weekend deep learning"),
            ("sunday", "instagram", "single_image", "educate", "Visual recap / cheat sheet"),
        ]

        plan: list[DayPlan] = []

        # Assign topics round-robin, prioritizing highest-scored
        available = list(topics)

        for i, (day, platform, fmt, intent, desc) in enumerate(day_slots):
            if not available:
                available = list(topics)  # Reuse if fewer topics than days

            # Find best topic for this platform
            best_idx = 0
            best_score = -1.0
            for j, t in enumerate(available):
                score = t.engagement_scores.overall
                # Bonus if this platform is in best_platforms
                if platform in t.best_platforms:
                    score += 1.5
                if score > best_score:
                    best_score = score
                    best_idx = j

            topic = available.pop(best_idx)
            date_str = (monday + timedelta(days=i)).strftime("%Y-%m-%d")

            # Get platform-specific angle
            plat_angle = next((pa for pa in topic.platform_angles if pa.platform == platform), None)
            hook = plat_angle.hook if plat_angle and plat_angle.hook else topic.title
            angle = plat_angle.angle if plat_angle and plat_angle.angle else topic.educational_angle
            actual_fmt = plat_angle.format if plat_angle and plat_angle.format else fmt

            # Generate copywriting prompt for external LLM
            writing_prompt = self._generate_writing_prompt(
                day=day,
                platform=platform,
                format_type=actual_fmt,
                topic_title=topic.title,
                topic_summary=topic.summary,
                teaching_goal=topic.educational_angle or f"Teach the audience about {topic.title}",
                teaching_points=topic.teaching_points,
                hook=hook,
                angle=angle,
            )

            plan.append(DayPlan(
                day=day,
                date=date_str,
                platform=platform,
                topic_id=topic.id,
                topic_title=topic.title,
                content_format=actual_fmt,
                intent=intent,
                hook=hook,
                angle=angle,
                teaching_goal=topic.educational_angle or f"Teach the audience about {topic.title}",
                reasoning=f"{desc}. {topic.why_it_works}",
                writing_prompt=writing_prompt,
            ))

        return plan

    def _generate_writing_prompt(
        self,
        day: str,
        platform: str,
        format_type: str,
        topic_title: str,
        topic_summary: str,
        teaching_goal: str,
        teaching_points: list[str],
        hook: str,
        angle: str,
    ) -> str:
        points_str = "\n".join([f"- {tp}" for tp in teaching_points])
        
        prompt = f"""{_COPYWRITING_SYSTEM_PROMPT}

# SPECIFIC POST TO GENERATE
You are a senior social media copywriter and educator for tech professionals (@tech_by_pravesh).
Your goal is to write a highly engaging, educational post about "{topic_title}".

## Target Platform & Format
* **Platform**: {platform.upper()}
* **Format**: {format_type.upper()}
* **Intent**: {teaching_goal}
* **Angle**: {angle}

## Topic Details
* **Topic**: {topic_title}
* **Overview**: {topic_summary}
* **Teaching Points to Cover**:
{points_str}

## Pre-approved Hook/Headline
Use or build upon this hook: "{hook}"

---

## Content Generation Guidelines

"""

        plat_lower = platform.lower()
        fmt_lower = format_type.lower()

        if plat_lower == "instagram":
            if "carousel" in fmt_lower or "infographic" in fmt_lower:
                prompt += f"""### Carousel Slide-by-Slide Outline
Write the copy for a premium, highly-visual 6-8 slide carousel.

**Slide Size & Dimensions:** Enforce standard vertical dimensions (1080x1350px, 4:5 aspect ratio) for maximum screen coverage and visual impact on mobile feeds.

**Unique Visual Theme Mandate:** This post is a standalone piece of content, not part of a series. The visual theme (colors, background style, fonts) must be unique and different from other posts on the feed to keep the overall feed layout fresh and engaging, and must directly complement the topic of this post: **'{topic_title}'** (Overview: {topic_summary}).

**Premium Visual Component Library:** Choose a diverse set of premium components on different slides to keep the reader engaged. Define and specify distinct component styles for:
- **IDE Code Snippet Frames**: A clean IDE code block with mock macOS-style window controls (red/yellow/green buttons) and syntax highlighting for code examples.
- **Metrics/KPI Showcase Cards**: High-impact statistic widgets displaying large numbers (e.g., '+300% Speed', '10x Faster', '0ms Latency') with clean description badges below them.
- **Before/After Comparison Grids**: A side-by-side or top-down grid structure comparing bad/inefficient practices with good/modern practices.
- **Process Timeline/Steps**: A pipeline progression showing chronological or workflow stages with numbered connector badges (e.g., Step 1 -> Step 2 -> Step 3).
- **Alert/Warning Callout Boxes**: Clean boxes with a yellow/red warning accent border and warning icon for common mistakes or warnings.
- **Highlight Badges**: Tiny capsule-shaped labels (e.g., 'Tip', 'Best Practice', 'Avoid') to accent key terms.

For each slide, provide:
1. **Slide Title**: Large, bold main headline (1-6 words).
2. **Body Text**: Concise supporting bullet points or a single clear sentence (under 25 words per slide).
3. **Visual Cues & Component Styling**: Describe what graphic, diagram, code frame, metrics card, or chart to show.
4. **Layout Placement Blueprint**: Define exact screen positioning zones:
   - **Top 10% (Header Zone)**: Cohesive brand header (e.g. "@tech_by_pravesh"), category tag, and slide index counter (e.g. "03/08").
   - **Center 20-85% (Main Visual Canvas)**: Large graphic/code block and core copy.
   - **Bottom 15% (Footer Zone)**: Swipe arrow callout and page count.

Slide Flow:
* **Slide 1**: Cover slide. Grab attention using the hook.
* **Slide 2**: Problem/Context. Empathize with why this topic matters.
* **Slides 3-6**: Core Teaching Points. Explain step-by-step with clear visual concepts.
* **Slide 7**: Summary. The single most important takeaway.
* **Slide 8**: CTA. Tell them to save this guide and comment their thoughts.

Write the exact slide text now!"""
            elif "reel" in fmt_lower or "video" in fmt_lower:
                prompt += """### Short-Form Video (Reel) Script
Write a complete, word-for-word voiceover script for a 30-60 second educational video. Provide:
1. **Visual Scene**: What the presenter is doing or what is on screen.
2. **Audio/Voiceover**: The exact script to speak.

Video structure:
* **0-3 seconds (Hook)**: Say the pre-approved hook. Start with an energetic visual action or pattern interrupt.
* **3-15 seconds (The Analogy)**: Explain the complex topic using a simple, relatable real-world analogy.
* **15-45 seconds (Actionable Walkthrough)**: Step-by-step explanation of the teaching points.
* **45-60 seconds (CTA)**: A strong call-to-action to save this video and follow for daily tech deep dives."""
            else:
                prompt += f"""### Single-Image Cheat Sheet & Spaced Caption
**Dimensions:** Enforce standard vertical dimensions (1080x1350px, 4:5 aspect ratio) for maximum screen coverage.

**Unique Visual Theme Mandate:** The visual theme (colors, background style, fonts) must be unique and different from other posts on the feed to keep the overall feed layout fresh and engaging, and must directly complement the topic of this post: **'{topic_title}'** (Overview: {topic_summary}).

**Visual Graphic Design:** Describe a high-quality cheat sheet, comparison table, or code snippet card. Detail the layouts, layout zones, and use of premium components (such as IDE frames, highlight badges, or metrics panels).

**Caption**: Write a spaced, clean caption:
* Hook line at the top.
* Spaced short paragraphs.
* Bullet points of the teaching points.
* CTA to save and share."""
                
        elif plat_lower == "linkedin":
            prompt += f"""### Premium LinkedIn Insight Post
Write a thoughtful, professional long-form post for software engineers, tech managers, and founders.

**Unique Visual Theme Mandate:** The visual theme (colors, background style, fonts) must be unique and different from other posts on the feed to keep the overall feed layout fresh and engaging, and must directly complement the topic of this post: **'{topic_title}'** (Overview: {topic_summary}).

* **Style**: Spaced lines, short paragraphs (1-2 sentences), bold key terms, conversational but expert tone.
* **Structure**:
  - **Hook**: Use the pre-approved hook at the top. Follow with double spacing.
  - **The Context**: Explain why this is currently a hot topic in software or AI.
  - **Core Lesson (Actionable list)**: Use bold bullet headers (e.g. "**1. [Actionable Header]**: Description").
  - **Takeaway**: Summarize the value.
  - **Discussion CTA**: Ask a thought-provoking question to invite engineers and managers to share their experiences in the comments. No generic hashtags, only 2-3 relevant ones (e.g., #softwareengineering, #artificialintelligence)."""

        elif plat_lower in ("x", "twitter"):
            prompt += """### Punchy, High-Value X Thread
Write a viral-style educational thread. Each tweet must be under 260 characters.
* **Tweet 1 (Hook)**: Hook tweet using the pre-approved hook. Must promise a specific value or transformation.
* **Tweet 2 (The Background)**: Explain the problem or context.
* **Tweets 3-6 (The Steps)**: One tweet per key teaching point. Break it down using short lines, simple checkmarks, or code snippets if appropriate.
* **Tweet 7 (Summary & CTA)**: Summarize the lesson, and prompt them to bookmark the thread and retweet the first tweet."""

        else:
            prompt += """### Standard Social Post
Write a premium educational post:
1. **Hook**: Start with a punchy opening.
2. **Body**: Spaced paragraphs breaking down the core concepts.
3. **CTA**: End with a clear call-to-action to save/share."""

        prompt += "\n\nGenerate the complete content copy now. Do not include placeholders."
        return prompt

    # ── JSON extraction ──

    @staticmethod
    def _extract_json_array(text: str) -> list[dict] | None:
        """Extract a JSON array from pasted text (with markdown fence support).
        
        Uses a robust two-pass parsing strategy: tries parsing raw candidates first,
        then cleans comments/commas/quotes/escapes and retries with AST fallback.
        """
        def _try_parse_candidates(source: str) -> list[dict] | None:
            # Fenced code blocks
            fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", source, flags=re.IGNORECASE)
            candidates: list[str] = list(fenced)

            # Raw text without fences
            cleaned = re.sub(r"```(?:json)?", "", source, flags=re.IGNORECASE).strip()
            candidates.append(cleaned)

            # Bracket-matched substrings
            candidates.extend(_find_json_arrays(cleaned))

            # First-[ to last-]
            start_arr = cleaned.find("[")
            end_arr = cleaned.rfind("]")
            if start_arr != -1 and end_arr > start_arr:
                candidates.append(cleaned[start_arr:end_arr + 1])

            # Object bounds fallback (if it's wrapped, e.g. {"topics": [...]})
            candidates.extend(_find_json_objects(cleaned))
            start_obj = cleaned.find("{")
            end_obj = cleaned.rfind("}")
            if start_obj != -1 and end_obj > start_obj:
                candidates.append(cleaned[start_obj:end_obj + 1])

            for candidate in candidates:
                candidate = candidate.strip()
                if not candidate:
                    continue

                # Standard JSON
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list):
                        return parsed
                    if isinstance(parsed, dict):
                        # Try to find any list of dicts inside
                        for val in parsed.values():
                            if isinstance(val, list) and len(val) > 0 and all(isinstance(x, dict) for x in val):
                                return val
                        for key in ("topics", "results", "data", "content"):
                            if key in parsed and isinstance(parsed[key], list):
                                return parsed[key]
                        return [parsed]
                except json.JSONDecodeError:
                    pass

                # Python literal eval fallback
                try:
                    import ast
                    candidate_py = _convert_to_python_literals(candidate)
                    parsed = ast.literal_eval(candidate_py)
                    if isinstance(parsed, list):
                        return parsed
                    if isinstance(parsed, dict):
                        for val in parsed.values():
                            if isinstance(val, list) and len(val) > 0 and all(isinstance(x, dict) for x in val):
                                return val
                        for key in ("topics", "results", "data", "content"):
                            if key in parsed and isinstance(parsed[key], list):
                                return parsed[key]
                        return [parsed]
                except Exception:
                    pass

            return None

        # Pass 1: Try raw candidates as-is
        res = _try_parse_candidates(text)
        if res is not None:
            return res

        # Pass 2: Clean the text and retry
        cleaned_text = _clean_json_string(text)
        return _try_parse_candidates(cleaned_text)


# ── Standalone JSON sanitization/matching helper functions ──

def _clean_json_string(s: str) -> str:
    """Clean comments, trailing commas, and normalize quotes in JSON string."""
    # 1. Normalize smart quotes first
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    
    # 2. Tokenize into strings, comments, and structural JSON
    token_pattern = re.compile(
        r'(?P<double_string>"(?:[^"\\]|\\.)*")|'
        r'(?P<single_string>\'(?:[^\'\\]|\\.)*\')|'
        r'(?P<block_comment>\/\*[\s\S]*?\*\/)|'
        r'(?P<line_comment>\/\/[^\n]*)|'
        r'(?P<other>[^"\'/]+|/)'
    )
    
    tokens = []
    for match in token_pattern.finditer(s):
        gd = match.groupdict()
        if gd['double_string']:
            val = gd['double_string']
            if len(val) >= 2:
                q = val[0]
                inner = val[1:-1]
                inner = inner.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                val = q + inner + q
            tokens.append(('string', val))
        elif gd['single_string']:
            val = gd['single_string']
            if len(val) >= 2:
                q = val[0]
                inner = val[1:-1]
                inner = inner.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                val = q + inner + q
            tokens.append(('string', val))
        elif gd['block_comment'] or gd['line_comment']:
            tokens.append(('whitespace', ' '))
        else:
            other_text = gd['other']
            other_text = re.sub(r'=\s*([\w_-]+)\s*:', r'"\1":', other_text)
            tokens.append(('other', other_text))
            
    # 3. Clean equal signs where key is quoted: e.g. = "key" : -> "key" :
    i = 0
    while i < len(tokens):
        if tokens[i][0] == 'other':
            val = tokens[i][1]
            val_stripped = val.rstrip()
            if val_stripped.endswith('='):
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx][0] == 'whitespace':
                    next_idx += 1
                
                if next_idx < len(tokens) and tokens[next_idx][0] == 'string':
                    colon_idx = next_idx + 1
                    while colon_idx < len(tokens) and tokens[colon_idx][0] == 'whitespace':
                        colon_idx += 1
                    
                    if colon_idx < len(tokens) and tokens[colon_idx][0] == 'other' and tokens[colon_idx][1].lstrip().startswith(':'):
                        trailing_whitespace = val[len(val_stripped):]
                        tokens[i] = ('other', val_stripped[:-1] + trailing_whitespace)
        i += 1

    # 4. Rebuild the string while omitting trailing commas
    result_parts = []
    for i, (tok_type, tok_val) in enumerate(tokens):
        if tok_type == 'other' and tok_val.strip() == ',':
            next_idx = i + 1
            is_trailing = False
            while next_idx < len(tokens):
                next_type, next_val = tokens[next_idx]
                if next_type == 'whitespace':
                    next_idx += 1
                    continue
                if next_type == 'other':
                    val_strip = next_val.strip()
                    if not val_strip:
                        next_idx += 1
                        continue
                    if val_strip[0] in ('}', ']'):
                        is_trailing = True
                    break
                break
            if is_trailing:
                continue
        
        if tok_type == 'other':
            tok_val = re.sub(r',(\s*[\]}])', r'\1', tok_val)
            
        result_parts.append(tok_val)
        
    return "".join(result_parts).strip()


def _convert_to_python_literals(s: str) -> str:
    """Map true/false/null inside non-string regions to Python True/False/None."""
    token_pattern = re.compile(
        r'(?P<double_string>"(?:[^"\\]|\\.)*")|'
        r'(?P<single_string>\'(?:[^\'\\]|\\.)*\')|'
        r'(?P<block_comment>\/\*[\s\S]*?\*\/)|'
        r'(?P<line_comment>\/\/[^\n]*)|'
        r'(?P<other>[^"\'/]+|/)'
    )
    tokens = []
    for match in token_pattern.finditer(s):
        gd = match.groupdict()
        if gd['double_string']:
            tokens.append(gd['double_string'])
        elif gd['single_string']:
            tokens.append(gd['single_string'])
        elif gd['block_comment']:
            tokens.append(gd['block_comment'])
        elif gd['line_comment']:
            tokens.append(gd['line_comment'])
        else:
            other_text = gd['other']
            other_text = re.sub(r'\btrue\b', 'True', other_text)
            other_text = re.sub(r'\bfalse\b', 'False', other_text)
            other_text = re.sub(r'\bnull\b', 'None', other_text)
            tokens.append(other_text)
    return "".join(tokens)


def _find_json_objects(text: str) -> list[str]:
    """Find and extract potential JSON object substrings by matching braces."""
    results = []
    start = -1
    brace_count = 0
    in_string = False
    escape = False
    
    for i, char in enumerate(text):
        if char == '"' and not escape:
            in_string = not in_string
        if in_string:
            if char == '\\' and not escape:
                escape = True
            else:
                escape = False
            continue
            
        if char == '{':
            if brace_count == 0:
                start = i
            brace_count += 1
        elif char == '}':
            if brace_count > 0:
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    results.append(text[start:i+1])
                    start = -1
    return results


def _find_json_arrays(text: str) -> list[str]:
    """Find and extract potential JSON array substrings by matching brackets."""
    results = []
    start = -1
    bracket_count = 0
    in_string = False
    escape = False
    
    for i, char in enumerate(text):
        if char == '"' and not escape:
            in_string = not in_string
        if in_string:
            if char == '\\' and not escape:
                escape = True
            else:
                escape = False
            continue
            
        if char == '[':
            if bracket_count == 0:
                start = i
            bracket_count += 1
        elif char == ']':
            if bracket_count > 0:
                bracket_count -= 1
                if bracket_count == 0 and start != -1:
                    results.append(text[start:i+1])
                    start = -1
    return results
