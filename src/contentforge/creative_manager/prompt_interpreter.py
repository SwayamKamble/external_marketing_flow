"""Quick Prompt Pipeline – OpenAI-powered prompt interpretation and planning.

This module provides the intelligence layer for the "Quick Prompt" feature.
It uses the existing LLM Gateway (Azure OpenAI) to:
  1. Interpret simple user prompts into structured intents
  2. Generate detailed research prompts (matching the existing system's quality)
  3. Parse structured research from external LLMs
  4. Apply chat-based edits to plans
  5. Generate production-ready final prompts
"""

from __future__ import annotations

import json
import re
import ast
from typing import Any

from datetime import datetime
from contentforge.creative_manager.models import (
    DiscoveredTopic,
    SeriesDay,
    SeriesPlan,
    StructuredIntent,
)


# ─────────────────────────────────────────────────────────
# System prompts for OpenAI calls
# ─────────────────────────────────────────────────────────

_INTERPRET_SYSTEM_PROMPT = """You are a content strategy AI assistant. Your job is to interpret a user's simple prompt about a content series idea and extract structured information from it.

The user will give you a simple prompt like:
- "7 day series on hidden tricks of Claude"
- "10 days of advance python series"
- "5 day AI workflow automation series for LinkedIn"
- "Create a week-long series about system design patterns"

You must extract the following information:

1. **series_length**: Number of days/episodes. Default to 7 if not specified.
2. **topic_theme**: The main theme/topic of the series.
3. **sub_topics**: A list of 3-8 potential sub-topics/angles for individual days.
4. **target_audience**: Who would benefit most (e.g., "AI enthusiasts, developers, tech professionals").
5. **platform_preferences**: Which platforms work best (choose from: "instagram", "linkedin", "x"). If not specified, suggest based on the topic.
6. **content_styles**: Suggested content formats (e.g., "carousel", "reel", "thread", "infographic", "tutorial").
7. **educational_goals**: What the audience will learn by the end of the series (3-5 specific goals).
8. **difficulty_level**: "beginner", "intermediate", or "advanced".

Return ONLY valid JSON with this exact structure:
{
    "series_length": 7,
    "topic_theme": "Hidden tricks of Claude AI",
    "sub_topics": ["topic1", "topic2", ...],
    "target_audience": "AI enthusiasts, developers, content creators",
    "platform_preferences": ["instagram", "linkedin"],
    "content_styles": ["carousel", "reel", "thread"],
    "educational_goals": ["goal1", "goal2", ...],
    "difficulty_level": "intermediate"
}

Return ONLY the JSON, no other text."""


_CHAT_EDIT_SYSTEM_PROMPT = """You are a content strategy assistant helping a user edit a content series plan.
The user wants to make modifications (e.g. "change day 2 hook", "swap day 1 and 3", "make day 3 hook more catchy").

You must identify the changes and return ONLY a JSON object showing the modifications.
Do NOT return the entire plan. Return ONLY the modified fields for the relevant days.

Required Output format:
{
  "summary": "A brief 1-sentence description of the changes you made (e.g. 'Updated the hook on Day 1 to be more attention-grabbing.')",
  "modified_days": [
    {
      "day_number": 1,
      "hook": "The new catchy hook..."
    }
  ]
}

Rules:
1. Include the "summary" key describing the changes you applied.
2. Include "day_number" (integer) for each day you modify.
3. Include ONLY the fields that are changing (e.g. "title", "hook", "script", "caption", "content_type", "platform", "slide_outline", "key_points", "talking_points", "cta", "notes").
4. Do NOT include fields that are not changing.
5. If a field like "key_points" or "slide_outline" is changed, provide the complete new list/array for that field.
6. To delete a day, include {"day_number": X, "action": "delete"}.
7. To swap days (e.g. "swap day 2 and 5"), output both days with their new contents under their respective day_number.
8. Return ONLY the JSON object, no other text."""


# ─────────────────────────────────────────────────────────
# Topic Discovery Prompt (Step 2)
# ─────────────────────────────────────────────────────────

_FILTER_DESCRIPTIONS = {
    "educational": {
        "label": "Educational",
        "focus": "actionable frameworks, step-by-step tutorials, mental models, tool comparisons, workflow breakdowns, and how-to guides that teach the viewer a specific skill or concept they can apply immediately",
        "avoid": "pure news, funding announcements, generic motivation, celebrity tech stories",
        "scoring_priority": "educational_value and practicality must score >= 8",
    },
    "news": {
        "label": "Latest AI & Tech News",
        "focus": "the most important, recent, and groundbreaking AI and AI Tech industry developments, product releases, research paper breakthroughs, model launches (e.g. GPT, Claude, Gemini, open-source models), and major tech updates that occurred in the last 7 days — focused purely on the details, facts, features, and capabilities of the news itself",
        "avoid": "educational tutorials, how-to guides, coding walkthroughs, old news, generic non-AI tech news, non-technical business announcements, funding rumors, celebrity drama",
        "scoring_priority": "timeliness, relevance, and details_richness must score >= 8",
    },
    "trending_ai": {
        "label": "Trending AI Tools & Techniques",
        "focus": "AI tools, models, frameworks, and techniques that are currently trending on social media, HackerNews, ProductHunt, GitHub, and tech Twitter — with practical use-cases, comparisons, and hands-on tutorials",
        "avoid": "outdated tools, vaporware, tools without practical value, pure speculation",
        "scoring_priority": "viral_potential, practicality, and shareability must score >= 8",
    },
}


# Platform-specific content format descriptions
_PLATFORM_CONTENT_DESCRIPTIONS = {
    "instagram": {
        "label": "Instagram",
        "formats": "carousels (6-8 slides), reels (30-60s), single-image posts, and infographic slides",
        "strengths": "visual step-by-step guides, checklists, code snippet cards, quick visual tutorials, and highly saveable educational content",
        "style": "short punchy text, bold visuals, vertical format (1080x1350px), hook-driven first slide",
    },
    "linkedin": {
        "label": "LinkedIn",
        "formats": "long-form posts, document carousels, articles, and professional case studies",
        "strengths": "professional insights, software architecture deep-dives, career advice, frameworks, and case studies with data",
        "style": "thoughtful professional tone, spaced short paragraphs, bold key terms, discussion-oriented CTA",
    },
    "x": {
        "label": "X (Twitter)",
        "formats": "threads (5-12 tweets), short posts, and visual threads with images",
        "strengths": "opinions, hot takes, engineering trends, quick tips, numbered lists, and viral-style educational threads",
        "style": "concise (under 260 chars per tweet), punchy hook tweet, one point per tweet, numbered lists",
    },
}


def _build_topic_discovery_prompt(series_length: int, content_filter: str, platform: str = "instagram") -> str:
    """Generate a Perplexity-optimized prompt to discover trending topics.

    The user copies this to Perplexity and gets back a JSON list of topics.
    """
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    filt = _FILTER_DESCRIPTIONS.get(content_filter, _FILTER_DESCRIPTIONS["educational"])
    plat = _PLATFORM_CONTENT_DESCRIPTIONS.get(platform, _PLATFORM_CONTENT_DESCRIPTIONS["instagram"])

    is_news = content_filter == "news"
    brand_desc = "a senior content strategist for an AI & Tech news and insights brand (@tech_by_pravesh)" if is_news else "a senior content strategist for an educational AI & Tech social media brand (@tech_by_pravesh)"

    news_guideline = ""
    if is_news:
        news_guideline = """
## NEWS-ONLY REQUIREMENT:
- All topics must be PURE AI AND AI TECH NEWS. No generic tech, no educational how-to guides, and no tutorials.
- Focus purely on the actual news, its technical details, specs, capabilities, and benchmarks.
- Strictly avoid any educational or tutorial angle. We want pure news and its details.
"""

    prompt = f"""You are {brand_desc}.

Today's date is **{current_date}**.

## CRITICAL SEARCH INSTRUCTION:
**YOU MUST SEARCH THE WEB** for the most recent trending news, breakthrough releases, open-source repository launches, and active tech discussions in the AI and AI Tech industry that occurred in the last 7 days leading up to **{current_date}**. Do NOT rely on pre-trained historical knowledge. You must fetch fresh, real-time news and breakthroughs.
{news_guideline}
Your task: Discover **8-12 highly engaging trending topics** that would make excellent content for a **{plat['label']} post**. All topics must be fresh, new, and based on breakthroughs, releases, or trends people *love* reading and discussing right now. Do NOT return outdated historical news from previous months/years (like September, etc.).

## Target Platform: {plat['label']}
All content will be published exclusively on **{plat['label']}** using formats like {plat['formats']}.
Topics must work well for: {plat['strengths']}.
Content style: {plat['style']}.

## Content Filter: {filt['label']}

**Focus on**: {filt['focus']}

**Avoid**: {filt['avoid']}

**Scoring priority**: {filt['scoring_priority']}

---

## What Makes a Great Topic?

- It has strong audience demand RIGHT NOW
- It can sustain 1-3 detailed slides or a single breakdown post
- It works exceptionally well on {plat['label']} specifically
- The audience (developers, AI enthusiasts, tech professionals, students) will save, share, and discuss it

---

## Required Output Format

Return a JSON array with 8-12 topics. Each topic:

```json
[
  {{
    "title": "Clear, specific topic title",
    "summary": "2-3 sentence overview of what this topic covers and why it matters right now",
    "why_trending": "Why this topic is trending or relevant right now (cite specific events, launches, or data if possible)",
    "relevance_score": 9.2,
    "suggested_angles": [
      "Angle 1: A specific sub-topic or perspective for a day's content",
      "Angle 2: Another sub-topic...",
      "Angle 3: Another sub-topic..."
    ],
    "target_audience": "Who specifically benefits most from this content",
    "category": "{content_filter}",
    "news_date": "MANDATORY: The exact date when the original news, release, or breakthrough occurred (e.g., June 5, 2026 or 2026-06-05). Do not leave empty."
  }}
]
```

## CRITICAL RULES:
- Return ONLY the JSON array, no other text
- **MANDATORY NEWS DATE**: Every topic MUST include the actual historical date when the news or breakthrough originally occurred in the `news_date` field (e.g., "June 5, 2026" or "2026-06-05"). Do not leave this field empty, do not use relative terms like "today" or "recent", and do not use future post calendar scheduling dates.
- relevance_score is 0-10 based on current trending relevance
- Topics should be diverse — don't cluster around one narrow area
- Every topic must be genuinely useful to the target audience
- All topics must be optimized for {plat['label']} content specifically

Discover the topics now."""
    return prompt



def _parse_discovered_topics(raw_text: str) -> list[DiscoveredTopic] | None:
    """Parse Perplexity response into a list of DiscoveredTopic objects."""
    import uuid

    cleaned = _clean_json_string(raw_text)

    # Try extracting JSON array first
    candidates: list[str] = []

    # Fenced code blocks
    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE)
    candidates.extend(fenced)

    # Raw text
    stripped = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    candidates.append(stripped)

    # Bracket matching
    candidates.extend(_find_json_arrays(stripped))

    # Brace matching (might be a wrapper object)
    candidates.extend(_find_json_objects(stripped))

    parsed_list: list[dict] | None = None

    for c in candidates:
        c = c.strip()
        if not c:
            continue
        for parser in (json.loads, ast.literal_eval):
            try:
                candidate_text = c
                if parser == ast.literal_eval:
                    candidate_text = _convert_to_python_literals(c)
                parsed = parser(candidate_text)
                if isinstance(parsed, list):
                    parsed_list = parsed
                    break
                if isinstance(parsed, dict):
                    # Try common wrapper keys
                    for key in ("topics", "results", "data", "content", "discoveries"):
                        if key in parsed and isinstance(parsed[key], list):
                            parsed_list = parsed[key]
                            break
                    if parsed_list:
                        break
                    # Try any list value
                    for v in parsed.values():
                        if isinstance(v, list) and v and isinstance(v[0], dict):
                            parsed_list = v
                            break
                    if parsed_list:
                        break
            except Exception:
                continue
        if parsed_list:
            break

    if not parsed_list:
        return None

    topics: list[DiscoveredTopic] = []
    for item in parsed_list:
        if not isinstance(item, dict):
            continue
        topics.append(DiscoveredTopic(
            id=str(item.get("id", f"topic_{uuid.uuid4().hex[:8]}")),
            title=str(item.get("title", "")).strip(),
            summary=str(item.get("summary", item.get("description", ""))).strip(),
            why_trending=str(item.get("why_trending", item.get("why_relevant", ""))).strip(),
            relevance_score=float(item.get("relevance_score", item.get("score", 0))),
            suggested_angles=[str(a).strip() for a in item.get("suggested_angles", item.get("angles", []))],
            target_audience=str(item.get("target_audience", "")).strip(),
            news_date=(lambda d: datetime.now().strftime("%B %d, %Y") if not d or d.lower() in ("recent", "today", "now", "current", "latest", "unknown", "n/a", "recent breakthrough") else d)(str(item.get("news_date", "")).strip()),
        ))

    return topics if topics else None


def _build_deep_research_prompt(topic: DiscoveredTopic, series_length: int, content_filter: str, platform: str = "instagram") -> str:
    """Generate a deep research prompt for the selected topic.

    This is similar to _build_research_prompt but with the selected topic baked in.
    Focuses exclusively on the user's chosen platform.
    """
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    filt = _FILTER_DESCRIPTIONS.get(content_filter, _FILTER_DESCRIPTIONS["educational"])
    plat = _PLATFORM_CONTENT_DESCRIPTIONS.get(platform, _PLATFORM_CONTENT_DESCRIPTIONS["instagram"])
    angles_str = "\n".join([f"- {a}" for a in topic.suggested_angles]) if topic.suggested_angles else "- Explore multiple angles and sub-topics"

    # Platform-specific content type guidance
    platform_content_types = {
        "instagram": "carousel, reel, single-image, or infographic",
        "linkedin": "long-form post, document carousel, or article",
        "x": "thread, short post, or visual thread",
    }
    content_types = platform_content_types.get(platform, "carousel, reel, or post")

    if content_filter == "news":
        prompt = f"""You are a senior content strategist for a leading AI & Tech news channel on {plat['label']} (@tech_by_pravesh).

Today's date is **{current_date}**.

Your goal: Generate a detailed **1-day (single post) {plat['label']} news breakdown** about the topic: **"{topic.title}"**.

Make sure all content is highly relevant to the actual news event or breakthrough that occurred on or around **{topic.news_date or current_date}**, referencing specific versions, features, benchmarks, capabilities, and facts. Do NOT use outdated historical information from previous months/years.

## Topic Overview
- **Title**: {topic.title}
- **Summary**: {topic.summary}
- **Why It's Relevant**: {topic.why_trending}
- **News Release Date**: {topic.news_date or current_date}
- **Target Audience**: {topic.target_audience or "AI enthusiasts, developers, tech professionals, students"}

## Target Platform: {plat['label']} ONLY
This news breakdown will be published exclusively on **{plat['label']}**.
Content formats to use: {content_types}.
Content style: {plat['style']}.
Optimize for: {plat['strengths']}.

## Key Aspects to Cover
{angles_str}

## Core Objective
Generate a news breakdown that helps the audience:
- Understand exactly what was released, launched, or discovered (facts, technical specifications, capabilities, and benchmarks)
- Know the actual release date of the news
- Understand the technical implications and significance for the AI industry
- Save/share the post because of its pure utility and clarity on this major breakthrough

---

## Content Strategy Rules
The content must be **PURE news reporting and technical details**.
- **NO educational tutorials, no step-by-step how-to guides, and no coding walkthroughs.**
- Focus purely on the actual facts, specifications, benchmarks, comparisons, and capabilities of this breakthrough.
- Make it a single post plan (1 day/episode).

---

## Content Quality Requirements
Every day's content must:
- Be highly factual and detailed
- Include the exact release date of the news prominently (e.g. in the caption and as notes/details)
- Have a compelling hook that stops the scroll
- Include at least 3 specific key points / features / benchmarks of the news
- Include a clear call-to-action (CTA)

---

## Required Output Format
Return a JSON object with this exact structure:

```json
{{
  "series_title": "{topic.title}",
  "series_summary": "Detailed news breakdown of {topic.title}",
  "days": [
    {{
      "day_number": 1,
      "title": "{topic.title}",
      "platform": "{platform}",
      "content_type": "{content_types.split(',')[0].strip()}",
      "hook": "Attention-grabbing opening line that stops the scroll and highlights the breakthrough",
      "angle": "Detailed news reporting on the breakthrough",
      "teaching_goal": "Understand the features and specs of {topic.title}",
      "key_points": [
        "Major feature/spec/benchmark 1",
        "Major feature/spec/benchmark 2",
        "Major feature/spec/benchmark 3",
        "Major feature/spec/benchmark 4"
      ],
      "talking_points": [
        "Technical detail and explanation for key point 1",
        "Technical detail and explanation for key point 2",
        "Technical detail and explanation for key point 3"
      ],
      "slide_outline": [
        {{
          "slide_number": 1,
          "slide_title": "Breaking: Cover hook title",
          "slide_content": "Brief curiosity generating subtext",
          "visual_cue": "What graphic/UI mockup to show"
        }}
      ],
      "script": "Voiceover script if reel/video",
      "caption": "Full social media caption detailing the news with spacing, news date ({topic.news_date or current_date}) and hashtags",
      "cta": "Clear call-to-action (e.g., Save this for reference, Share with your team)",
      "notes": "{topic.news_date or current_date}"
    }}
  ]
}}
```

## CRITICAL RULES
- Return ONLY the JSON object, no other text
- Provide exactly 1 day (the single news post) in the "days" array
- Do NOT add any educational how-to or tutorial steps. Keep it purely factual and details-rich about the news itself.
"""
        return prompt

    prompt = f"""You are a senior content strategist for an educational AI & Tech brand on {plat['label']} (@tech_by_pravesh).

Today's date is **{current_date}**.

Your goal: Create a detailed **{series_length}-day {plat['label']} content series** about **"{topic.title}"**.

Make sure all content is highly relevant to today's real-world state of this topic as of **{current_date}**, referencing recent versions, model parameters, API updates, or technical practices matching the current AI landscape. Do NOT use outdated historical information from previous months/years.

## Topic Overview
- **Title**: {topic.title}
- **Summary**: {topic.summary}
- **Why It's Relevant**: {topic.why_trending}
- **Content Filter**: {filt['label']}
- **Target Audience**: {topic.target_audience or "AI enthusiasts, developers, tech professionals, students"}

## Target Platform: {plat['label']} ONLY
All {series_length} days of content will be published exclusively on **{plat['label']}**.
Content formats to use: {content_types}.
Content style: {plat['style']}.
Optimize for: {plat['strengths']}.

## Suggested Angles / Sub-topics to Explore
{angles_str}

## Core Objective
Generate content that helps audiences:
- Learn something new and actionable
- Understand complex concepts simply
- Gain practical skills they can use today
- Discover useful frameworks and workflows
- Save time at work
- Improve career opportunities
- Understand emerging technology trends

Every day must provide actionable educational value while also maximizing engagement on {plat['label']}.

---

## Content Strategy Rules
The content should NOT be news reporting.
Avoid:
- Company funding announcements
- Product launches without educational lessons
- Generic AI news summaries
- Celebrity AI stories
- Clickbait without educational value
- Generic motivation

Instead, focus on:
- Concepts & Frameworks
- Step-by-step Tutorials
- Practical Workflows
- Mental Models
- Case Studies & Real Examples
- Tool Breakdowns & Comparisons
- Industry Shifts Explained
- Career Development Tips
- Productivity Systems
- Engineering Lessons
- Implementation Techniques

---

## Content Quality Requirements
Every day's content must:
- Be educational — it teaches, explains, or demonstrates something
- Be optimized specifically for {plat['label']} audience and format
- Have strong audience demand
- Be understandable by the target audience
- Have a compelling hook that stops the scroll
- Include at least 3 specific teaching/key points
- Include a clear call-to-action

---

## Required Output Format
Return a JSON object with this exact structure:

```json
{{
  "series_title": "Descriptive series title",
  "series_summary": "2-3 sentence overview of what this series teaches",
  "days": [
    {{
      "day_number": 1,
      "title": "Clear, specific topic title for this day",
      "platform": "{platform}",
      "content_type": "{content_types.split(',')[0].strip()}",
      "hook": "Attention-grabbing opening line that stops the scroll",
      "angle": "The specific angle/perspective for this content",
      "teaching_goal": "What the viewer will learn from this specific post",
      "key_points": [
        "Specific teaching point 1",
        "Specific teaching point 2",
        "Specific teaching point 3",
        "Specific teaching point 4"
      ],
      "talking_points": [
        "Expanded explanation for point 1",
        "Expanded explanation for point 2",
        "Expanded explanation for point 3"
      ],
      "slide_outline": [
        {{
          "slide_number": 1,
          "slide_title": "Cover slide title",
          "slide_content": "Brief content description",
          "visual_cue": "What graphic/screenshot to show"
        }}
      ],
      "script": "For reels/videos: complete voiceover script with timestamps",
      "caption": "Full social media caption with spacing and hashtags",
      "cta": "Clear call-to-action"
    }}
  ]
}}
```

## CRITICAL RULES
- ALL days must use platform "{platform}" — do NOT assign different platforms
- Every day MUST be educational — it teaches, explains, or demonstrates something
- No pure news items
- No generic motivation
- Each day must have at least 3 specific key_points
- Hooks must be attention-grabbing and optimized for {plat['label']}
- The JSON must be valid and parseable
- Return ONLY the JSON object, no other text
- Content should build on previous days (progressive learning)
- The series should feel cohesive
- Each day should stand alone as a valuable post even if viewed independently

Generate the complete {series_length}-day content series plan now."""
    return prompt


def _build_research_prompt(intent: StructuredIntent) -> str:
    """Generate a research system prompt incorporating ALL features from the existing prompt.

    This mirrors the quality and structure of _RESEARCH_PROMPT from engine.py,
    but tailored to the user's specific series intent.
    """
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    platforms_str = ", ".join(intent.platform_preferences) if intent.platform_preferences else "instagram, linkedin, x"
    goals_str = "\n".join([f"- {g}" for g in intent.educational_goals]) if intent.educational_goals else "- Learn practical skills\n- Understand key concepts\n- Gain actionable knowledge"
    sub_topics_str = "\n".join([f"- {st}" for st in intent.sub_topics]) if intent.sub_topics else ""

    prompt = f"""You are a senior content strategist for an educational AI & Tech brand on social media (@tech_by_pravesh).

Today's date is **{current_date}**.

Your goal: Create a detailed **{intent.series_length}-day content series** about **"{intent.topic_theme}"** that has strong viral potential while delivering genuine educational value. All topics must be highly relevant to today's state of the AI & Tech landscape as of **{current_date}**.

## Series Overview
- **Theme**: {intent.topic_theme}
- **Length**: {intent.series_length} days
- **Target Audience**: {intent.target_audience or "AI enthusiasts, developers, tech professionals, students"}
- **Difficulty Level**: {intent.difficulty_level}
- **Platforms**: {platforms_str}

## Educational Goals
By the end of this series, the audience should:
{goals_str}

{f'''## Suggested Sub-topics to Cover
{sub_topics_str}
''' if sub_topics_str else ''}
## Core Objective
Generate content that helps audiences:
- Learn something new and actionable
- Understand complex concepts simply
- Gain practical skills they can use today
- Discover useful frameworks and workflows
- Save time at work
- Improve career opportunities
- Understand emerging technology trends

Every day must provide actionable educational value while also maximizing engagement.

---

## Content Strategy Rules
The content should NOT be news reporting.
Avoid:
- Company funding announcements
- Product launches without educational lessons
- Generic AI news summaries
- Celebrity AI stories
- Clickbait without educational value
- Generic motivation ("why you should learn to code")

Instead, focus on:
- Concepts & Frameworks
- Step-by-step Tutorials
- Practical Workflows
- Mental Models
- Case Studies & Real Examples
- Tool Breakdowns & Comparisons
- Industry Shifts Explained
- Career Development Tips
- Productivity Systems
- Engineering Lessons
- Implementation Techniques

---

## Platform Audience and Content Match Selection
For each day, determine which platform it is BEST suited for based on the content:
- **instagram**: Best for visual step-by-step guides, checklists, code snippet cards, and quick visual tutorials (carousel, reel, single-image, infographic).
- **linkedin**: Best for professional insights, software architecture, career advice, and case studies (long-form, document carousel, article).
- **x**: Best for opinions, hot takes, engineering trends, and quick tips (thread, short post, visual_thread).

---

## Content Quality Requirements
Every day's content must:
- Be educational — it teaches, explains, or demonstrates something
- Be highly relevant and useful in today's landscape
- Have strong audience demand
- Be understandable by the target audience ({intent.difficulty_level} level)
- Be useful for students, professionals, creators, founders, engineers, or AI enthusiasts
- Have a compelling hook that stops the scroll
- Include at least 3 specific teaching/key points
- Include a clear call-to-action

---

## Virality & Scoring Evaluation
For each day's content assign scores from 1-10:
- viral_potential (how likely to reach beyond followers)
- educational_value (how much the viewer learns)
- shareability (how likely to be shared/reposted)
- saveability (how likely to be bookmarked/saved)
- conversation_potential (how likely to start discussions)
- practicality (how actionable the content is)

Only include content where:
- educational_value >= 8
- practicality >= 8
- viral_potential >= 7

---

## Required Output Format
Return a JSON object with this exact structure:

```json
{{
  "series_title": "Descriptive series title",
  "series_summary": "2-3 sentence overview of what this series teaches",
  "days": [
    {{
      "day_number": 1,
      "title": "Clear, specific topic title for this day",
      "platform": "instagram",
      "content_type": "carousel",
      "hook": "Attention-grabbing opening line that stops the scroll",
      "angle": "The specific angle/perspective for this content",
      "teaching_goal": "What the viewer will learn from this specific post",
      "key_points": [
        "Specific teaching point 1",
        "Specific teaching point 2",
        "Specific teaching point 3",
        "Specific teaching point 4"
      ],
      "talking_points": [
        "Expanded explanation for point 1",
        "Expanded explanation for point 2",
        "Expanded explanation for point 3"
      ],
      "slide_outline": [
        {{
          "slide_number": 1,
          "slide_title": "Cover slide title",
          "slide_content": "Brief content description",
          "visual_cue": "What graphic/screenshot to show"
        }},
        {{
          "slide_number": 2,
          "slide_title": "Problem/Context",
          "slide_content": "Why this matters",
          "visual_cue": "Visual description"
        }}
      ],
      "script": "For reels/videos: complete voiceover script with timestamps",
      "caption": "Full social media caption with spacing and hashtags",
      "cta": "Clear call-to-action (e.g., Save this for later, Share with a friend)",
      "scores": {{
        "viral_potential": 8,
        "educational_value": 9,
        "shareability": 8,
        "saveability": 9,
        "conversation_potential": 7,
        "practicality": 9
      }}
    }}
  ]
}}
```

## Content Format Guidelines

### For Carousel Posts (Instagram/LinkedIn):
- Provide 6-8 slides in the slide_outline array
- Slide 1: Cover with hook
- Slide 2: Problem/Context
- Slides 3-6: Core teaching points (one per slide)
- Slide 7: Summary/key takeaway
- Slide 8: CTA (save, share, follow)

### For Reels/Videos:
- Provide a complete script in the "script" field
- Include timestamps: 0-3s (hook), 3-15s (context), 15-45s (teaching), 45-60s (CTA)
- Keep it 30-60 seconds

### For X/Twitter Threads:
- Structure the key_points as individual tweets
- Each point should be under 260 characters
- First point is the hook tweet

### For LinkedIn Articles:
- Provide detailed talking_points with professional tone
- Include data points and frameworks

---

## CRITICAL RULES
- Every day MUST be educational — it teaches, explains, or demonstrates something
- No pure news items
- No generic motivation
- Each day must have at least 3 specific key_points
- Hooks must be attention-grabbing and platform-appropriate
- The JSON must be valid and parseable
- Return ONLY the JSON object, no other text
- Content should build on previous days (progressive learning)
- The series should feel cohesive, not like random unrelated topics
- Each day should stand alone as a valuable post even if viewed independently

Generate the complete {intent.series_length}-day content series plan now.
"""
    return prompt


def _build_production_prompt(plan: SeriesPlan) -> str:
    """Generate a comprehensive production-ready prompt from an approved plan.

    This prompt, when given to Claude/Gemini/GPT, produces the exact final content
    ready for publishing. Focuses on the user's chosen platform.
    """
    intent = plan.intent
    platform = getattr(intent, "platform", "instagram") or "instagram"
    plat = _PLATFORM_CONTENT_DESCRIPTIONS.get(platform, _PLATFORM_CONTENT_DESCRIPTIONS["instagram"])

    if intent.content_filter == "news" and plan.days:
        day = plan.days[0]
        prompt = f"""# Production Instructions for News Slide Deck in HTML/CSS/JS

After reviewing the news details below, you MUST generate a complete, self-contained HTML/CSS/JS file for a **3-4 slide carousel** presenting this news breakthrough.

## Topic Details
- **News Title**: {day.title}
- **News Hook**: "{day.hook}"
- **News Details & Facts**:
{chr(10).join([f'  - {kp}' for kp in day.key_points])}
- **Implications & Rationale**: {day.angle}
- **News Date**: {day.notes or intent.topic_theme}
- **CTA**: {day.cta}

---

## CRITICAL CODE OUTPUT REQUIREMENTS:
1. **Slide Generation Stack**: Write this slide deck entirely in a **single, unified HTML file** using inline CSS and JS.
2. **Strict Layout Constraint (NO OVERLAPS & PERFECT ALIGNMENT)**:
   - You MUST ensure that no components, text blocks, badges, boxes, or graphic panels overlap each other.
   - Use CSS Flexbox or CSS Grid layouts exclusively.
   - Avoid raw `position: absolute` for key text blocks. Use padding, margins, and gaps to separate elements cleanly.
   - Set fixed height containers for visual diagrams and frames (e.g. IDE frames, metric boxes) to prevent them from growing and colliding with text elements.
   - The visual elements and layout alignment must be absolutely perfect and highly premium.
3. **Slide Dimensions**: Enforce standard vertical dimensions: **1080px wide x 1350px tall** (4:5 aspect ratio).
4. **Export ZIP Script**: Include a sticky control toolbar at the top of the body with a "Download All Slides (ZIP)" button. This button must call a fully functional Javascript `downloadAllJPGs()` script that uses `html2canvas` and `jszip` CDNs (included in the head) to capture all slide elements and pack them into a zip file of JPGs.
5. **Slide Count**: Keep the deck to **exactly 3-4 slides** (Slide 1: Hook, Slide 2: Core News, Slide 3: Implications, Slide 4: CTA).
6. **Strict Emoji Prohibition**: STRICTLY DO NOT use emojis anywhere in the HTML slide deck (including slide titles, subheadings, body text, lists, labels, badges, or buttons). Emojis look unpolished and generic. Avoid characters like 🚀, 💡, ⚡, 📊, etc.
7. **Topic-Themed Aesthetics & Components**: Read the topic/subject of the slides and choose a visual theme (color scheme, typography, custom icons, borders, and layouts) that uniquely fits the topic's brand identity. For example, if the topic is "Anthropic Claude", use Claude's signature warm beige background, dark brown text, soft orange accents, and a clean serif font for the headers/logos. If "Python", use Python yellow/blue. If it's a developer tool, style cards like clean terminals; if business/finance, use dashboard KPI styling. Customize components and layout accents around the logo/handle area specifically to match the topic's visual universe so the deck represents it uniquely.


---

## Premium Visual Component Guidelines:
- **IDE Code Snippet Frame**: If coding or repo-related, display code in a mock macOS window controls box with syntax highlighting.
- **Metric Badges/Cards**: Large high-impact bold metrics (e.g., "10x Faster", "+150% Spec") with small descriptive labels.
- **Alert/Warning Callout Box**: Accent card with warning/alert icon.
- **Swipe Indicators**: Chevron icons at bottom of slides 1-3.
- **Brand Handle**: "@tech_by_pravesh" at top of all slides.

---

## Output instructions:
- Generate the complete HTML file enclosed in a ```html code block.
- Follow the HTML code block with the complete caption block labeled exactly: `### Final Social Media Caption:`
- Ensure the caption is structured with short, double-spaced paragraphs, references the news release date, includes 3-5 relevant hashtags, and ends with the CTA.

Generate the HTML and caption now.
"""
        return prompt

    days_detail = []
    for day in plan.days:
        day_block = f"""
### Day {day.day_number}: {day.title}
- **Format**: {day.content_type.upper()}
- **Hook**: "{day.hook}"
- **Angle**: {day.angle}
- **Teaching Goal**: {day.teaching_goal}
- **Key Points**:
{chr(10).join([f'  - {kp}' for kp in day.key_points])}
- **CTA**: {day.cta}"""

        if day.slide_outline:
            day_block += "\n- **Slide Structure**:"
            for slide in day.slide_outline:
                sn = slide.get("slide_number", "?")
                st = slide.get("slide_title", "")
                sc = slide.get("slide_content", "")
                day_block += f"\n  - Slide {sn}: {st} — {sc}"

        if day.script:
            day_block += f"\n- **Script Framework**: {day.script[:200]}..."

        days_detail.append(day_block)

    days_section = "\n".join(days_detail)
    num_days = str(len(plan.days))
    topic = intent.topic_theme

    # Platform-specific content generation rules
    if platform == "linkedin":
        content_rules = f"""### Content Format: LinkedIn
Write thoughtful, professional long-form posts optimized for LinkedIn's algorithm and audience.

**Post Structure:**
- Spaced lines, short paragraphs (1-2 sentences per paragraph)
- Bold key terms and important concepts
- Hook at the very top with double spacing after
- Actionable list with bold bullet headers for key takeaways
- Discussion-oriented CTA with a thought-provoking question
- Only 2-3 relevant hashtags at the end

**For Document Carousels (PDF-style):**
- Design 8-12 slides in a professional, clean style
- Each slide should have a clear heading and 2-3 bullet points max
- Use consistent branding (fonts, colors) across all slides
- Include data points, frameworks, and professional diagrams
- End with a strong CTA slide

**Visual Theme Consistency:** All {num_days} days must maintain the same professional tone, visual branding, and formatting style. The theme must complement: **'{topic}'**.

**Tone:** Professional but approachable. Use data, frameworks, and case studies. Avoid casual slang."""

    elif platform == "x":
        content_rules = f"""### Content Format: X (Twitter)
Write viral-style educational threads optimized for X's algorithm and engagement patterns.

**Thread Structure:**
- Each tweet under 260 characters
- Tweet 1: Hook tweet — must stop the scroll
- Tweet 2: Background/context — set up the problem
- Tweets 3-6: One teaching point per tweet — numbered for clarity
- Final tweet: Summary & CTA — ask for retweets/follows

**For Short Posts:**
- Single-tweet format under 260 characters
- Strong opinion or hot take that invites replies
- Use 1-2 relevant hashtags only

**For Visual Threads:**
- Include image descriptions for each tweet
- Use code screenshots, diagrams, or comparison images
- Each image should be self-contained and valuable

**Visual Theme Consistency:** All {num_days} days must maintain the same thread style and formatting approach. The theme must complement: **'{topic}'**.

**Tone:** Punchy, direct, conversational. Use numbered lists, hot takes, and clear opinions."""

    else:  # instagram (default)
        content_rules = f"""### Content Format: Instagram Carousels (HTML/CSS/JS Slide Decks)
For each Instagram carousel day, you MUST generate the slides as a single, self-contained HTML/CSS/JS slide deck file. This allows the user to preview all slides in the browser and download them all at once in high-resolution JPG format via a ZIP archive.

**Slide Size & Dimensions:** Enforce standard vertical dimensions (1080px wide x 1350px tall, 4:5 aspect ratio) for maximum screen coverage and visual impact on mobile feeds.

**Visual Theme Consistency Mandate:** Because this content is generated as a unified {num_days}-day series, the visual theme MUST remain absolutely **consistent and cohesive** across all {num_days} days. Keep the same background style, typography hierarchy, logo/handle placement, and color palette (primary and accent colors, dark/light theme style) across all days to maintain a recognizable, high-premium brand identity. The theme must directly complement the overall series topic/theme: **'{topic}'**. Read the topic/subject of the slides and dynamically choose a color palette, fonts, and component stylings that uniquely represent that topic's identity (e.g., Anthropic Claude → warm beige background, dark brown text, soft orange accent, serif font; Python → yellow/blue; developer tool → terminal mock; business → dashboard metrics). Enforce these topic-specific aesthetics consistently around the logo, header, card borders, and tags so each deck represents the topic uniquely.

**Strict Emoji Prohibition:** STRICTLY DO NOT use emojis anywhere in the slide HTML or CSS (headings, body text, tag labels, or custom panels). Emojis are unpolished and generic. Do not output characters like 🚀, 💡, ⚡, etc.


**Premium Visual Component Library:** While the visual theme must be identical across all days, you must use a diverse set of premium components on different slides to keep the reader engaged. Define and specify distinct component styles for:
- **IDE Code Snippet Frames**: A clean IDE code block with mock macOS-style window controls (red/yellow/green buttons) and syntax highlighting for code examples.
- **Metrics/KPI Showcase Cards**: High-impact statistic widgets displaying large numbers (e.g., '+300% Speed', '10x Faster', '0ms Latency') with clean description badges below them.
- **Before/After Comparison Grids**: A side-by-side or top-down grid structure comparing bad/inefficient practices with good/modern practices.
- **Process Timeline/Steps**: A pipeline progression showing chronological or workflow stages with numbered connector badges (e.g., Step 1 -> Step 2 -> Step 3).
- **Alert/Warning Callout Boxes**: Clean boxes with a yellow/red warning accent border and warning icon for common mistakes or warnings.
- **Highlight Badges**: Tiny capsule-shaped labels (e.g., 'Tip', 'Best Practice', 'Avoid') to accent key terms.

**CRITICAL CODE STRUCTURE REQUIREMENTS:**
1. A global sticky control toolbar at the very top of the body containing a styled and visible "Download All Slides (ZIP)" button. Do NOT replace it with comments or placeholders.
2. A vertical stack of slide wrappers (e.g., `<div class="slide-wrapper" id="slide-X">`).
3. Included CDN libraries:
   - html2canvas: `https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js`
   - JSZip: `https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js`
4. A fully functional Javascript script block at the end of the body containing the `downloadAllJPGs()` function, which captures all slides via html2canvas and exports them as a single ZIP file of JPGs. Do NOT omit this script or use placeholders/comments.

Write the complete HTML code block for each carousel post, followed by the caption and hashtags."""

    prompt = f"""# Content Generation Instructions for Downstream LLM (Claude, GPT, Gemini, etc.)

After reviewing the plan below, generate the COMPLETE, PRODUCTION-READY content for ALL {len(plan.days)} days.

**Target Platform: {plat['label']}** — All content is exclusively for {plat['label']}.

The goal is not just to create content.

The goal is to create content that:

* Educates — viewers learn something actionable
* Gets saved — viewers bookmark for later reference
* Gets shared — viewers send to friends/colleagues
* Starts conversations — viewers comment and discuss
* Maximizes watch time — viewers consume the entire post
* Maximizes retention — viewers come back for the next day
* Makes people follow for more — viewers want the whole series

---

## Series Overview
- **Theme**: {intent.topic_theme}
- **Platform**: {plat['label']}
- **Series Length**: {intent.series_length} days
- **Target Audience**: {intent.target_audience}
- **Difficulty Level**: {intent.difficulty_level}

---

## Day-by-Day Plan
{days_section}

---

## Content Generation Rules

{content_rules}

---

## CRITICAL REQUIREMENTS:
- Generate COMPLETE content for ALL {len(plan.days)} days
- ALL content is for **{plat['label']}** — do NOT mix platforms
- Each day's content must be PRODUCTION-READY (no placeholders)
- Use the exact hooks, angles, and teaching goals from the plan
- Content should build progressively across the series
- Each day should also stand alone as valuable content
- Write all captions with proper spacing and formatting
- Include relevant hashtags (2-5 per post, platform-appropriate for {plat['label']})
- Every post must end with a clear CTA

Generate all {len(plan.days)} days of content now. For each day, clearly label:
- Day number and title
- Format type
- The complete content (slides/script/post text)
- Caption
- Hashtags
"""
    return prompt



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
            # Replace comment with whitespace
            tokens.append(('whitespace', ' '))
        else:
            other_text = gd['other']
            # Clean up equal signs where key is not quoted: e.g. =key: -> "key":
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
                        # Yes, we have an accidental equal sign before a quoted key: omit it
                        trailing_whitespace = val[len(val_stripped):]
                        tokens[i] = ('other', val_stripped[:-1] + trailing_whitespace)
        i += 1

    # 4. Rebuild the string while omitting trailing commas
    result_parts = []
    for i, (tok_type, tok_val) in enumerate(tokens):
        if tok_type == 'other' and tok_val.strip() == ',':
            # Look ahead for next non-whitespace token
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
            # Remove trailing commas within the same token: e.g. ", }" -> " }"
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


class PromptInterpreter:
    """OpenAI-powered prompt interpretation and planning for Quick Prompt pipeline.

    Uses the existing LLM Gateway infrastructure (Azure OpenAI) for all LLM calls.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-initialize the OpenAI async client using existing config."""
        if self._client is None:
            from contentforge.core.config_loader import ConfigLoader
            config = ConfigLoader(config_dir="./config")
            provider = config.get_provider_config()
            base_url = provider.get("base_url", "")
            api_key = provider.get("api_key", "")
            default_model = config.get_llm_config().get("default_model", "gpt-5-chat")

            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            self._model = default_model
        return self._client

    async def interpret_prompt(self, user_prompt: str) -> StructuredIntent:
        """Interpret a simple user prompt into a structured intent using OpenAI.

        Args:
            user_prompt: Simple prompt like "7 day series on hidden tricks of Claude"

        Returns:
            StructuredIntent with extracted information
        """
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _INTERPRET_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.7,
        )

        raw_content = response.choices[0].message.content or "{}"

        # Parse JSON from response
        parsed = self._extract_json_object(raw_content)
        if not parsed:
            # Fallback: basic extraction
            parsed = {
                "series_length": 7,
                "topic_theme": user_prompt,
                "target_audience": "AI enthusiasts, developers, tech professionals",
                "platform_preferences": ["instagram", "linkedin", "x"],
                "educational_goals": [f"Learn about {user_prompt}"],
                "difficulty_level": "intermediate",
            }

        return StructuredIntent(
            series_length=parsed.get("series_length", 7),
            topic_theme=parsed.get("topic_theme", user_prompt),
            sub_topics=parsed.get("sub_topics", []),
            target_audience=parsed.get("target_audience", ""),
            platform_preferences=parsed.get("platform_preferences", ["instagram", "linkedin", "x"]),
            content_styles=parsed.get("content_styles", ["carousel", "reel", "thread"]),
            educational_goals=parsed.get("educational_goals", []),
            difficulty_level=parsed.get("difficulty_level", "intermediate"),
            raw_prompt=user_prompt,
        )

    def generate_research_prompt(self, intent: StructuredIntent) -> str:
        """Generate a detailed research prompt the user copies to Claude/Perplexity.

        Incorporates ALL features from the existing _RESEARCH_PROMPT.
        """
        return _build_research_prompt(intent)

    # ── New 6-step pipeline methods ──

    def generate_topic_discovery_prompt(self, series_length: int, content_filter: str, platform: str = "instagram") -> str:
        """Generate a prompt for Perplexity to discover trending topics.

        Step 2 of the revamped pipeline.
        """
        return _build_topic_discovery_prompt(series_length, content_filter, platform)

    def parse_discovered_topics(self, raw_text: str) -> list[DiscoveredTopic] | None:
        """Parse Perplexity topic discovery response into DiscoveredTopic list.

        Step 3 of the revamped pipeline.
        """
        return _parse_discovered_topics(raw_text)

    def generate_deep_research_prompt(self, topic: DiscoveredTopic, series_length: int, content_filter: str, platform: str = "instagram") -> str:
        """Generate a deep research prompt for the selected topic.

        Step 4 of the revamped pipeline.
        """
        return _build_deep_research_prompt(topic, series_length, content_filter, platform)

    def _get_gateway(self):
        """Get the global LLMGateway or initialize a fallback one."""
        try:
            from api.dependencies import get_llm
            return get_llm()
        except (AssertionError, ImportError, KeyError):
            # Fallback for standalone CLI/scripts
            import os
            from contentforge.core.config_loader import ConfigLoader
            from contentforge.core.llm_gateway import LLMGateway
            
            config_dir = "config"
            if not os.path.exists(config_dir) and os.path.exists("./config"):
                config_dir = "./config"
            elif not os.path.exists(config_dir) and os.path.exists("../config"):
                config_dir = "../config"
                
            config = ConfigLoader(config_dir=config_dir)
            return LLMGateway(config=config)

    async def parse_series_research(self, raw_text: str) -> tuple[SeriesPlan | None, str | None]:
        """Parse JSON output from Claude/Perplexity into a structured SeriesPlan.

        Handles various JSON formats including fenced code blocks, wrapped objects,
        and raw arrays. Uses an LLM fallback if standard parsing fails to recover
        malformed or raw conversational text.
        """
        # --- Pass 1: Try standard fast parsing first ---
        plan, fast_error = self._parse_series_research_fast(raw_text)
        if plan:
            return plan, None

        # --- Pass 2: LLM Recovery Fallback ---
        errors = [f"Fast parsing failed: {fast_error}"]
        print(f"[PromptInterpreter] Fast JSON parsing failed: {fast_error}. Invoking LLM recovery fallback...")
        try:
            gateway = self._get_gateway()
            model = gateway.config.get_llm_config().get("default_model", "gpt-5-chat")
            
            system_prompt = """You are an expert JSON recovery assistant.
Your job is to parse and convert the user's pasted research text (which might be raw text, markdown, or malformed JSON) into a clean, valid JSON object following this exact schema:

{
  "series_title": "Descriptive series title",
  "series_summary": "2-3 sentence overview of what this series teaches",
  "days": [
    {
      "day_number": 1,
      "title": "Clear, specific topic title for this day",
      "platform": "instagram/linkedin/x",
      "content_type": "carousel/reel/thread/post",
      "hook": "Attention-grabbing opening line",
      "angle": "Content angle",
      "teaching_goal": "What they learn",
      "key_points": ["point 1", "point 2", ...],
      "talking_points": ["point 1 detail", "point 2 detail", ...],
      "slide_outline": [
        {
          "slide_number": 1,
          "slide_title": "Slide title",
          "slide_content": "Slide content",
          "visual_cue": "Visual cue"
        }
      ],
      "script": "Script voiceover",
      "caption": "Full social media caption",
      "cta": "Call to action",
      "notes": "Any extra notes"
    }
  ]
}

Rules:
1. Ensure the output is strictly valid JSON.
2. If the user input contains multiple days, map each day to an element in the "days" array. If it is only 1 day, "days" must contain exactly 1 element.
3. Extract as much factual information, key points, slides, caption, script, hooks, and CTAs as possible from the source text.
4. Output ONLY the raw JSON block inside ```json and ``` fences. Do not output any explanation, intro, or markdown text outside the code block.
"""

            result = await gateway.call(
                node_name="research_recovery",
                system_prompt=system_prompt,
                user_message=f"User Input:\n{raw_text}",
                model=model,
                temperature=0.1,
                max_tokens=4096,
            )
            
            if not result.success:
                errors.append(f"LLM API Call unsuccessful: {result.error}")
            else:
                recovered_text = result.content
                print(f"[PromptInterpreter] LLM recovery returned response of length {len(recovered_text)}")
                
                # Try parsing the recovered text
                plan, recovery_error = self._parse_series_research_fast(recovered_text)
                if plan:
                    print("[PromptInterpreter] LLM recovery successfully parsed SeriesPlan!")
                    return plan, None
                else:
                    errors.append(f"LLM recovery text parsing failed: {recovery_error}. LLM output preview: {recovered_text[:200]}")
        except Exception as e:
            errors.append(f"LLM Recovery exception: {e}")

        return None, " | ".join(errors)

    def _parse_series_research_fast(self, raw_text: str) -> tuple[SeriesPlan | None, str | None]:
        """Fast synchronous parsing of research text."""
        parsed = self._extract_json_object(raw_text)
        if not parsed:
            # Try as array
            parsed_arr = self._extract_json_array(raw_text)
            if parsed_arr:
                parsed = {"days": parsed_arr}
            else:
                try:
                    # Let's get raw decode error info for debugging
                    json.loads(raw_text)
                except Exception as e:
                    return None, f"JSON Syntax Error: {e}"
                return None, "No JSON object or array could be extracted from input"

        # Extract days
        days_raw = parsed.get("days", [])
        
        # Fallback 1: Search common alternative keys if days is not a list or is empty
        if not isinstance(days_raw, list) or not days_raw:
            alternative_keys = [
                "content_series", "series", "plan", "posts", "schedule", 
                "weekly_plan", "items", "news_breakdown", "news_post", 
                "day", "news", "post", "days_plan", "breakdown", 
                "articles", "carousel", "thread"
            ]
            for key in alternative_keys:
                val = parsed.get(key)
                if isinstance(val, list) and val:
                    days_raw = val
                    break
        
        # Fallback 1.5: Check if the parsed dictionary itself represents a single day (e.g. for 1-day news breakdowns)
        if (not isinstance(days_raw, list) or not days_raw) and isinstance(parsed, dict):
            # If the top level contains day-like fields and a title, treat it as a single-day list
            day_indicators = ["hook", "caption", "cta", "key_points", "talking_points", "day_number"]
            if "title" in parsed and any(k in parsed for k in day_indicators):
                days_raw = [parsed]

        # Fallback 2: Search for any list of dicts at all in the dictionary
        if not isinstance(days_raw, list) or not days_raw:
            for val in parsed.values():
                if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
                    days_raw = val
                    break

        # Fallback 3: If parsed is a dict, and we didn't find any list, check if the values are dicts that represent days
        if not isinstance(days_raw, list) or not days_raw:
            temp_days = []
            for k, val in parsed.items():
                if isinstance(val, dict) and ("title" in val or "hook" in val or "day_number" in val):
                    # Try to parse day number from key (e.g. "day_1" -> 1)
                    if "day_number" not in val:
                        num_match = re.search(r'\d+', str(k))
                        if num_match:
                            val["day_number"] = int(num_match.group(0))
                    temp_days.append(val)
            if temp_days:
                temp_days.sort(key=lambda x: x.get("day_number", 0))
                days_raw = temp_days

        if not isinstance(days_raw, list) or not days_raw:
            return None, f"Found JSON but couldn't locate days list. Keys present: {list(parsed.keys())}"

        def _parse_list_field(val: Any) -> list[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip()]
            if isinstance(val, str):
                lines = []
                for line in val.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Remove leading bullets/numbers: e.g. "- Point" -> "Point", "1. Point" -> "Point"
                    line = re.sub(r'^[-*•\d+\u2022]\.?\s*', '', line).strip()
                    if line:
                        lines.append(line)
                return lines
            return [str(val).strip()]

        days: list[SeriesDay] = []
        for d in days_raw:
            if not isinstance(d, dict):
                continue

            # Safe day number parsing
            raw_day_num = d.get("day_number")
            day_num = len(days) + 1
            if raw_day_num is not None:
                if isinstance(raw_day_num, int):
                    day_num = raw_day_num
                elif isinstance(raw_day_num, float):
                    day_num = int(raw_day_num)
                else:
                    digit_match = re.search(r'\d+', str(raw_day_num))
                    if digit_match:
                        day_num = int(digit_match.group(0))

            # Safe slide outline extraction
            slide_outline_raw = d.get("slide_outline", [])
            slide_outline = []
            if isinstance(slide_outline_raw, list):
                for s_item in slide_outline_raw:
                    if isinstance(s_item, dict):
                        slide_outline.append({
                            "slide_number": int(s_item.get("slide_number", len(slide_outline) + 1)),
                            "slide_title": str(s_item.get("slide_title", s_item.get("title", ""))).strip(),
                            "slide_content": str(s_item.get("slide_content", s_item.get("content", ""))).strip(),
                            "visual_cue": str(s_item.get("visual_cue", s_item.get("visual", ""))).strip(),
                        })
                    elif isinstance(s_item, str):
                        slide_outline.append({
                            "slide_number": len(slide_outline) + 1,
                            "slide_title": f"Slide {len(slide_outline) + 1}",
                            "slide_content": s_item.strip(),
                            "visual_cue": ""
                        })
            elif isinstance(slide_outline_raw, str):
                for idx, line in enumerate(slide_outline_raw.splitlines()):
                    line = line.strip()
                    if line:
                        slide_outline.append({
                            "slide_number": idx + 1,
                            "slide_title": f"Slide {idx + 1}",
                            "slide_content": line,
                            "visual_cue": ""
                        })

            days.append(SeriesDay(
                day_number=day_num,
                title=str(d.get("title", "")).strip(),
                platform=str(d.get("platform", "instagram")).strip().lower(),
                content_type=str(d.get("content_type", d.get("format", "carousel"))).strip().lower(),
                hook=str(d.get("hook", "")).strip(),
                angle=str(d.get("angle", "")).strip(),
                teaching_goal=str(d.get("teaching_goal", "")).strip(),
                key_points=_parse_list_field(d.get("key_points", [])),
                talking_points=_parse_list_field(d.get("talking_points", [])),
                slide_outline=slide_outline,
                script=str(d.get("script", "")).strip(),
                caption=str(d.get("caption", "")).strip(),
                cta=str(d.get("cta", "")).strip(),
                notes=str(d.get("notes", "")).strip(),
            ))

        if not days:
            return None, "All day items failed internal schema mapping"

        # Build intent from series metadata
        intent = StructuredIntent(
            series_length=len(days),
            topic_theme=parsed.get("series_title", ""),
        )

        return SeriesPlan(
            intent=intent,
            days=days,
            status="draft",
        ), None

    async def apply_chat_edit(self, plan: SeriesPlan, user_message: str) -> SeriesPlan:
        """Use OpenAI to interpret and apply user's chat-based edits to the plan.

        The user can say things like:
        - "change day 3 topic to X"
        - "improve the hook for day 2"
        - "make it more educational"
        - "swap day 1 and day 4"
        - "remove day 5"
        - "add more practical examples to all days"

        Returns the modified SeriesPlan.
        """
        client = self._get_client()

        # Serialize current plan to JSON for the LLM
        plan_json = json.dumps(plan.model_dump(), indent=2, default=str)

        user_content = f"""## Current Series Plan (JSON):
```json
{plan_json}
```

## User's Edit Request:
{user_message}

Identify the changes requested and return the modifications in the required JSON format. Return ONLY the JSON object."""

        response = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _CHAT_EDIT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=4096,
            temperature=0.3,
        )

        raw_content = response.choices[0].message.content or "{}"

        parsed = self._extract_json_object(raw_content)
        if not parsed:
            # Try as array
            parsed_arr = self._extract_json_array(raw_content)
            if parsed_arr:
                parsed = {"days": parsed_arr}

        if not parsed:
            print(f"[ERROR] Chat edit parsing failed. Raw response length: {len(raw_content)}")
            print(f"[ERROR] Raw response content: {raw_content}")
            # If parsing failed, return original plan unchanged
            plan.chat_history.append({
                "role": "user",
                "message": user_message,
            })
            plan.chat_history.append({
                "role": "assistant",
                "message": "I couldn't apply that change. Please try rephrasing your request.",
            })
            return plan

        # Extract delta updates
        summary = parsed.get("summary", f"Applied changes: {user_message}")
        modified_days = parsed.get("modified_days", [])
        if not isinstance(modified_days, list):
            # Try finding alternate keys if LLM nesting is wrong
            for key in ["days", "modified", "changes"]:
                val = parsed.get(key)
                if isinstance(val, list):
                    modified_days = val
                    break

        if not isinstance(modified_days, list) or not modified_days:
            # Maybe the LLM returned a raw list directly
            parsed_arr = self._extract_json_array(raw_content)
            if parsed_arr:
                modified_days = parsed_arr
            else:
                print(f"[ERROR] Chat edit: no modifications found in parsed JSON: {parsed}")
                plan.chat_history.append({
                    "role": "user",
                    "message": user_message,
                })
                plan.chat_history.append({
                    "role": "assistant",
                    "message": "No changes were detected in the response. Please try again with a more specific instruction.",
                })
                return plan

        # Merge delta modifications into existing plan
        days_map = {d.day_number: d for d in plan.days}
        deleted_days = set()

        for m in modified_days:
            if not isinstance(m, dict):
                continue
            day_num = m.get("day_number")
            if not day_num:
                continue
            try:
                day_num = int(day_num)
            except ValueError:
                continue

            # Handle deletion
            if m.get("action") == "delete":
                deleted_days.add(day_num)
                continue

            if day_num in days_map:
                existing_day = days_map[day_num]
                
                # Update simple fields if they exist in the delta
                for key in ["title", "platform", "content_type", "hook", "angle", "teaching_goal", "script", "caption", "cta", "notes"]:
                    if key in m:
                        setattr(existing_day, key, str(m[key]).strip())

                # Update list fields
                if "key_points" in m and isinstance(m["key_points"], list):
                    existing_day.key_points = [str(x).strip() for x in m["key_points"] if str(x).strip()]
                if "talking_points" in m and isinstance(m["talking_points"], list):
                    existing_day.talking_points = [str(x).strip() for x in m["talking_points"] if str(x).strip()]
                if "slide_outline" in m and isinstance(m["slide_outline"], list):
                    existing_day.slide_outline = m["slide_outline"]
            else:
                # Create a new day
                new_day = SeriesDay(
                    day_number=day_num,
                    title=str(m.get("title", f"Day {day_num} Topic")).strip(),
                    platform=str(m.get("platform", "instagram")).strip().lower(),
                    content_type=str(m.get("content_type", "carousel")).strip().lower(),
                    hook=str(m.get("hook", "")).strip(),
                    angle=str(m.get("angle", "")).strip(),
                    teaching_goal=str(m.get("teaching_goal", "")).strip(),
                    key_points=[str(x).strip() for x in m.get("key_points", []) if str(x).strip()],
                    talking_points=[str(x).strip() for x in m.get("talking_points", []) if str(x).strip()],
                    slide_outline=m.get("slide_outline", []),
                    script=str(m.get("script", "")).strip(),
                    caption=str(m.get("caption", "")).strip(),
                    cta=str(m.get("cta", "")).strip(),
                    notes=str(m.get("notes", "")).strip(),
                )
                days_map[day_num] = new_day

        # Reconstruct list of days (removing deleted ones)
        new_days_list = [d for num, d in days_map.items() if num not in deleted_days]
        new_days_list.sort(key=lambda x: x.day_number)

        # Re-index if a deletion happened to keep the day numbers contiguous
        if deleted_days:
            for idx, d in enumerate(new_days_list):
                d.day_number = idx + 1

        # Rebuild updated plan
        updated_plan = SeriesPlan(
            intent=plan.intent,
            days=new_days_list,
            status=plan.status,
            chat_history=list(plan.chat_history),
        )

        # Add to chat history
        updated_plan.chat_history.append({
            "role": "user",
            "message": user_message,
        })
        updated_plan.chat_history.append({
            "role": "assistant",
            "message": summary,
        })

        return updated_plan

        return updated_plan

    def generate_production_prompt(self, plan: SeriesPlan) -> str:
        """Generate a comprehensive production-ready prompt from the approved plan.

        This prompt, when given to Claude/Gemini/GPT, produces exact final content.
        """
        return _build_production_prompt(plan)

    # ── JSON extraction helpers ──

    @staticmethod
    def _extract_json_object(text: str) -> dict | None:
        """Extract a JSON object from text (with markdown fence support).

        Strategy:
        1. Try parsing the RAW text first (json.loads) — avoids
           corrupting valid JSON that contains smart quotes inside strings.
        2. Only fall back to _clean_json_string when raw parsing fails.
        """

        def _try_parse_candidates(source: str) -> dict | None:
            """Build candidate substrings from *source* and try parsing."""
            # Fenced code blocks
            fenced = re.findall(
                r"```(?:json)?\s*([\s\S]*?)\s*```", source, flags=re.IGNORECASE
            )
            candidates: list[str] = list(fenced)

            # Raw text without fences
            cleaned = re.sub(
                r"```(?:json)?", "", source, flags=re.IGNORECASE
            ).strip()
            candidates.append(cleaned)

            # Brace-matched substrings
            candidates.extend(_find_json_objects(cleaned))

            # First-{ to last-}
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end > start:
                candidates.append(cleaned[start : end + 1])

            for candidate in candidates:
                candidate = candidate.strip()
                if not candidate:
                    continue

                # Standard JSON
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass

                # Python literal eval fallback
                try:
                    candidate_py = _convert_to_python_literals(candidate)
                    parsed = ast.literal_eval(candidate_py)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass

            return None

        # --- Pass 1: try the raw text as-is ---
        result = _try_parse_candidates(text)
        if result is not None:
            return result

        # --- Pass 2: clean then retry ---
        cleaned_text = _clean_json_string(text)
        return _try_parse_candidates(cleaned_text)

    @staticmethod
    def _extract_json_array(text: str) -> list[dict] | None:
        """Extract a JSON array from text.

        Same two-pass strategy as _extract_json_object: try raw first,
        then cleaned.
        """

        def _try_parse_candidates(source: str) -> list[dict] | None:
            fenced = re.findall(
                r"```(?:json)?\s*([\s\S]*?)\s*```", source, flags=re.IGNORECASE
            )
            candidates: list[str] = list(fenced)

            cleaned = re.sub(
                r"```(?:json)?", "", source, flags=re.IGNORECASE
            ).strip()
            candidates.append(cleaned)

            # Bracket-matched substrings
            candidates.extend(_find_json_arrays(cleaned))

            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end > start:
                candidates.append(cleaned[start : end + 1])

            for candidate in candidates:
                candidate = candidate.strip()
                if not candidate:
                    continue

                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

                try:
                    candidate_py = _convert_to_python_literals(candidate)
                    parsed = ast.literal_eval(candidate_py)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass

            return None

        # --- Pass 1: raw ---
        result = _try_parse_candidates(text)
        if result is not None:
            return result

        # --- Pass 2: cleaned ---
        cleaned_text = _clean_json_string(text)
        return _try_parse_candidates(cleaned_text)
