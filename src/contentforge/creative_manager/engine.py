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

_COPYWRITING_SYSTEM_PROMPT = """# Content Generation Instructions for Downstream LLM (Claude, GPT, Gemini, etc.)

After selecting a topic, generate the content in the most suitable format based on the topic and platform.

The goal is not just to create content.

The goal is to create content that:

* Educates
* Gets saved
* Gets shared
* Starts conversations
* Maximizes watch time
* Maximizes retention
* Makes people follow for more

---

# Content Format Selection Rules

Choose the best format automatically.

## Carousel (Preferred)

Use carousel when:

* Explaining concepts
* Breaking down frameworks
* Teaching workflows
* Comparing tools
* Showing step-by-step processes
* Explaining trends
* Creating cheat sheets

### Carousel Specifications

* Aspect Ratio: 1:1
* Size: 1080 x 1080
* Slides: 7–10 slides
* Slide 1 = Hook Only
* Final Slide = CTA

### Carousel Structure

Slide 1:

* Curiosity Hook
* No explanation

Slide 2:

* Why this matters

Slide 3–8:

* Educational content

Slide 9:

* Summary

Slide 10:

* CTA

CTA examples:

* Save this
* Share with your team
* Follow for more AI insights
* Which one surprised you most?

---

## Single Image Post

Use when:

* Presenting one framework
* One comparison
* One chart
* One visual insight
* One statistic with explanation

### Specifications

* Aspect Ratio: 4:5
* Size: 1080 x 1350

Structure:

* Strong headline
* One key takeaway
* Visual hierarchy
* Minimal text

---

## Reel

Use when:

* Demonstrating workflows
* Showing tutorials
* Explaining AI tools
* Showing before/after results
* Debunking myths

### Reel Specifications

* Aspect Ratio: 9:16
* Duration: 30–60 seconds

Structure:

0–3 sec:

* Hook

3–10 sec:

* Problem

10–45 sec:

* Solution

45–60 sec:

* Key takeaway + CTA

---

# Hook Generation Rules

Every content piece MUST begin with a curiosity-driven hook.

Good hooks:

* "Most people use ChatGPT wrong. Here's why."
* "This AI workflow saves me 5 hours every week."
* "Nobody talks about this AI skill."
* "I tested 10 AI tools so you don't have to."
* "The difference between beginners and experts is this."
* "You're probably making this AI mistake."

Avoid:

* Generic titles
* Corporate language
* Clickbait without value
* Overly technical jargon

Hooks should:

* Be simple
* Create curiosity
* Be understandable in under 3 seconds
* Encourage the next slide/view

---

# Educational Standards

Every post must teach:

1. What it is
2. Why it matters
3. How it works
4. Practical applications
5. Common mistakes
6. Actionable takeaway

The audience should learn something useful by the end.

---

# Visual Design Guidelines

Use visual-first teaching.

Avoid:

* Large paragraphs
* Dense text
* Wall of text slides

Prefer:

* Diagrams
* Flowcharts
* Timelines
* Comparison tables
* Framework visuals
* Icons
* Step-by-step visuals

---

# Writing Style

Tone:

* Smart but simple
* Professional but human
* Educational but engaging

Language:

* Short sentences
* Simple words
* No unnecessary jargon

Target audience:

* Students
* Professionals
* Founders
* Developers
* AI enthusiasts
* Tech learners

---

# Content Output Requirements

For every topic generate:

1. Recommended format
2. Number of slides (if carousel)
3. Hook
4. Complete slide-by-slide breakdown
5. Visual instructions for each slide
6. Image generation instructions for each slide
7. On-slide text
8. Caption
9. CTA
10. Hashtags
11. Key takeaway
12. Save-worthy summary

---

# Image Generation Instructions

For every slide provide:

* Detailed visual description
* Layout structure
* Icon suggestions
* Illustration suggestions
* Design hierarchy
* Text placement

The image instructions should be detailed enough that a designer or AI image generator can create the slide without needing additional clarification.

---

# Quality Control Checklist

Before finalizing content verify:

✓ Educational value is high

✓ Hook creates curiosity

✓ Information is accurate

✓ Content is practical

✓ Slides are visually teachable

✓ Save-worthy insights exist

✓ Share-worthy insights exist

✓ Content encourages discussion

✓ Not news-focused

✓ Suitable for Instagram, LinkedIn, and X

✓ Easy to understand

✓ Every slide serves a purpose

✓ Final takeaway is actionable

The final output should be production-ready and require minimal editing before publishing.

"""


_RESEARCH_PROMPT = """You are a senior content strategist for an educational AI & Tech brand on social media (@tech_by_pravesh).

Your goal: Find **{topic_count} educational content topics** about AI, technology, software, productivity, automation, engineering, and emerging tech that have strong viral potential while delivering genuine educational value.

## Core Objective
Generate topics that help audiences:
- Learn something new
- Understand complex concepts simply
- Gain practical skills
- Discover useful frameworks
- Save time at work
- Improve career opportunities
- Understand emerging technology trends

Every topic must provide actionable educational value while also maximizing engagement.

---

## Content Strategy Rules
The content should NOT be news reporting.
Avoid:
- Company funding announcements
- Product launches without educational lessons
- Generic AI news summaries
- Celebrity AI stories
- Clickbait without educational value

Instead, focus on:
- Concepts
- Frameworks
- Tutorials
- Workflows
- Mental models
- Case studies
- Tool breakdowns
- Industry shifts explained
- Career development
- Productivity systems
- Engineering lessons
- AI implementation techniques

---

## Platform Audience and Content Match Selection
For each topic, determine which platform(s) it is BEST suited for based on the target audience:
- **instagram**: Best for visual step-by-step guides, checklists, code snippet cards, and quick visual tutorials (carousel, reel, single-image).
- **linkedin**: Best for professional insights, software architecture, career advice, and case studies (long-form, document carousel).
- **x**: Best for opinions, hot takes, engineering trends, and quick tips (thread, short post).

Include only the recommended platforms for the topic in the `best_platforms` array (must contain one or more of: "instagram", "linkedin", "x").

---

## Topic Quality Requirements
Every topic must:
- Be educational
- Be highly relevant in today's AI & Tech landscape
- Have strong audience demand
- Be searchable and discussable
- Work across multiple platforms
- Be understandable by non-experts
- Be useful for students, professionals, creators, founders, engineers, or AI enthusiasts

---

## Virality & Scoring Evaluation
For each topic assign scores from 1-10:
- viral_potential
- educational_value
- shareability
- saveability
- conversation_potential
- practicality

Only recommend topics where:
- educational_value >= 8
- practicality >= 8
- viral_potential >= 7

---

## Required Output Format
Return a JSON array with this exact structure:

```json
[
  {{
    "title": "Clear specific topic",
    "summary": "2-3 sentence educational overview",
    "bucket": "shareable | saveable | conversation-starter | career-growth | ai-workflow | trend-education",
    "category": "how-to | concept | framework | tool | myth-buster | case-study | cheat-sheet | behind-the-scenes | trend-analysis | career",
    "educational_angle": "What the audience learns",
    "teaching_points": [
      "Specific lesson 1",
      "Specific lesson 2",
      "Specific lesson 3"
    ],
    "best_platforms": ["instagram", "linkedin"],
    "platform_strategy": {{
      "instagram": {{
        "why_it_works": "Why IG users will save/share it",
        "best_format": "carousel | infographic | reel",
        "primary_goal": "saves | shares | reach"
      }},
      "linkedin": {{
        "why_it_works": "Why professionals will engage",
        "best_format": "carousel | document | article",
        "primary_goal": "shares | comments | discussions"
      }},
      "x": {{
        "why_it_works": "Why it sparks conversation",
        "best_format": "thread | visual_thread",
        "primary_goal": "bookmarks | retweets | discussions"
      }}
    }},
    "scores": {{
      "viral_potential": 9,
      "educational_value": 10,
      "shareability": 9,
      "saveability": 10,
      "conversation_potential": 8,
      "practicality": 10
    }},
    "why_it_can_go_viral": "Detailed explanation of why this topic has strong viral potential while remaining educational",
    "source": "Trend, framework, industry discussion, AI workflow, technical concept, developer practice, productivity method, etc.",
    "suggested_hooks": {{
      "instagram": "Strong carousel cover hook",
      "linkedin": "Professional opening hook",
      "x": "Thread opening hook"
    }},
    "suggested_formats": {{
      "instagram": "carousel | infographic | reel",
      "linkedin": "carousel | document | article",
      "x": "thread | visual_thread"
    }},
    "suggested_angles": {{
      "instagram": "Visual-first educational angle",
      "linkedin": "Professional/business angle",
      "x": "Discussion-provoking angle"
    }}
  }}
]
```

## CRITICAL RULES
- Every topic MUST be **educational** — it teaches, explains, or demonstrates something
- No pure news items (no "Company X just raised $Y" unless there's a lesson)
- No generic motivation ("why you should learn to code")
- Each topic must have at least 3 specific teaching_points
- Hooks must be attention-grabbing and platform-appropriate
- The JSON must be valid and parseable
- Return ONLY the JSON array, no other text

## Niche: {niche}

Find {topic_count} educational topics now.
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
        return _RESEARCH_PROMPT.format(niche=niche, topic_count=topic_count)

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
        """Extract a JSON array from pasted text (with markdown fence support)."""
        # Try fenced code blocks first
        fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        candidates: list[str] = list(fenced)

        # Try raw text
        cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        candidates.append(cleaned)

        # Try finding array bounds
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end > start:
            candidates.append(cleaned[start:end + 1])

        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate:
                continue
            # Normalize smart quotes
            candidate = candidate.replace("\u201c", '"').replace("\u201d", '"')
            candidate = candidate.replace("\u2018", "'").replace("\u2019", "'")
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    # Maybe it's wrapped: {"topics": [...]}
                    for key in ("topics", "results", "data", "content"):
                        if key in parsed and isinstance(parsed[key], list):
                            return parsed[key]
                    return [parsed]
            except json.JSONDecodeError:
                continue
        return None
