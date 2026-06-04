"""Pydantic models for the Creative Manager system.

All data structures for topic discovery, engagement scoring,
and weekly content planning across X, LinkedIn, and Instagram.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EngagementScores(BaseModel):
    """Per-topic engagement potential ratings (0-10 scale)."""
    shareability: float = 0.0    # Would people share/repost this?
    saveability: float = 0.0     # Would people bookmark/save this?
    likeability: float = 0.0     # Would people like/heart this?
    conversation: float = 0.0   # Would this start a discussion?
    virality: float = 0.0       # Could this reach beyond followers?
    educational_value: float = 0.0  # Does this teach something actionable?
    overall: float = 0.0        # Weighted composite score


class PlatformAngle(BaseModel):
    """Platform-specific content angle for a topic."""
    platform: str               # "instagram", "x", "linkedin"
    hook: str = ""              # Opening hook for this platform
    angle: str = ""             # Content angle/approach
    format: str = ""            # "carousel", "thread", "single_image", "reel"
    teaching_approach: str = "" # How to educate on this platform
    estimated_engagement: str = ""  # "high", "medium", "low"


class TopicIdea(BaseModel):
    """A discovered educational content topic."""
    id: str
    title: str
    summary: str
    category: str = ""          # "AI", "programming", "startup", etc.
    source: str = ""
    educational_angle: str = "" # What the viewer will LEARN
    why_it_works: str = ""      # Why this topic would get engagement
    teaching_points: list[str] = Field(default_factory=list)  # Key things to teach
    best_platforms: list[str] = Field(default_factory=list)
    engagement_scores: EngagementScores = Field(default_factory=EngagementScores)
    platform_angles: list[PlatformAngle] = Field(default_factory=list)
    selected: bool = False


class DayPlan(BaseModel):
    """A single day's content plan in the weekly calendar."""
    day: str                    # "monday", "tuesday", etc.
    date: str = ""              # "2026-06-02"
    platform: str               # Primary platform
    topic_id: str
    topic_title: str
    content_format: str         # "carousel", "thread", "single_image", "reel"
    intent: str                 # "educate", "teach", "explain", "demonstrate"
    hook: str = ""              # Opening hook
    angle: str = ""             # Content angle
    teaching_goal: str = ""     # What the viewer should learn
    reasoning: str = ""         # Why this topic on this day
    writing_prompt: str = ""    # Custom copywriting prompt for another LLM


class CreativeSession(BaseModel):
    """A complete Creative Manager planning session."""
    id: str
    week_id: str
    status: str = "input_needed"  # input_needed, topics_ready, planned, complete
    niche: str = "AI & Tech"
    topics: list[TopicIdea] = Field(default_factory=list)
    weekly_plan: list[DayPlan] = Field(default_factory=list)
    research_prompt: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─────────────────────────────────────────────────────────
# Quick Prompt Pipeline Models
# ─────────────────────────────────────────────────────────

class StructuredIntent(BaseModel):
    """Interpreted user prompt – extracted by OpenAI from a simple input."""
    series_length: int = 7
    content_filter: str = "educational"  # "educational", "news", "trending_ai"
    platform: str = "instagram"  # "instagram", "linkedin", "x"
    topic_theme: str = ""
    sub_topics: list[str] = Field(default_factory=list)
    target_audience: str = ""
    platform_preferences: list[str] = Field(default_factory=list)
    content_styles: list[str] = Field(default_factory=list)
    educational_goals: list[str] = Field(default_factory=list)
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    raw_prompt: str = ""


class DiscoveredTopic(BaseModel):
    """A trending topic returned from Perplexity topic discovery."""
    id: str = ""
    title: str = ""
    summary: str = ""
    why_trending: str = ""
    relevance_score: float = 0.0
    suggested_angles: list[str] = Field(default_factory=list)
    target_audience: str = ""
    category: str = ""  # mirrors content_filter


class SeriesDay(BaseModel):
    """A single day in the content series."""
    day_number: int
    title: str = ""
    platform: str = ""
    content_type: str = ""           # carousel, reel, thread, single_image, article
    hook: str = ""
    angle: str = ""
    teaching_goal: str = ""
    key_points: list[str] = Field(default_factory=list)
    talking_points: list[str] = Field(default_factory=list)
    slide_outline: list[dict] = Field(default_factory=list)   # For carousels
    script: str = ""                 # For reels/videos
    caption: str = ""
    cta: str = ""
    notes: str = ""


class SeriesPlan(BaseModel):
    """Complete series plan from user prompt."""
    intent: StructuredIntent = Field(default_factory=StructuredIntent)
    days: list[SeriesDay] = Field(default_factory=list)
    status: str = "draft"            # draft, reviewed, approved, finalized
    chat_history: list[dict] = Field(default_factory=list)


class QuickPromptSession(BaseModel):
    """Session tracking for Quick Prompt workflow."""
    id: str
    user_prompt: str
    structured_intent: StructuredIntent | None = None
    research_prompt: str = ""
    series_plan: SeriesPlan | None = None
    production_prompt: str = ""
    status: str = "prompt_entered"
    # Statuses: prompt_entered → intent_ready → research_prompt_ready →
    #           research_submitted → plan_reviewed → approved → finalized
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
