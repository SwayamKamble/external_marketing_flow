"""LangGraph state schema for ContentForge pipeline.

Defines all Pydantic models used as typed state throughout the pipeline.
Every piece of data that flows between nodes is defined here.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──


class PipelinePhase(str, Enum):
    """Current phase of the pipeline."""
    IDLE = "idle"
    RESEARCH = "research"
    SCORING = "scoring"
    PLANNING = "planning"
    DEEP_RESEARCH = "deep_research"
    CONTENT_CREATION = "content_creation"
    REVIEW = "review"
    EXPORT = "export"


class ContentFormat(str, Enum):
    """Content format types."""
    CAROUSEL = "carousel"
    SINGLE_IMAGE = "single_image"
    REEL = "reel"
    NEWS_POST = "news_post"


class ContentStatus(str, Enum):
    """Status of a piece of content."""
    PENDING = "pending"
    DRAFT = "draft"
    EDITING = "editing"
    APPROVED = "approved"
    EXPORTED = "exported"


class HumanActionType(str, Enum):
    """Types of human actions the pipeline can wait for."""
    PASTE_RESEARCH = "paste_research"
    APPROVE_PLAN = "approve_plan"
    SELECT_TOPICS = "select_topics"
    PASTE_DEEP_RESEARCH = "paste_deep_research"
    REVIEW_CONTENT = "review_content"
    CHAT_EDIT = "chat_edit"


class Platform(str, Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    X = "x"
    THREADS = "threads"


# ── Data Models ──


class Topic(BaseModel):
    """A single topic extracted from research."""
    id: str
    title: str
    summary: str
    category: str = ""
    source: str = ""
    key_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0
    scoring_reasoning: str = ""
    suggested_format: ContentFormat | None = None
    suggested_angle: str = ""


class PlanItem(BaseModel):
    """A single day's plan in the weekly calendar."""
    day: str  # "monday", "tuesday", etc.
    date: str  # "2026-04-21"
    topic_id: str
    topic_title: str
    content_format: ContentFormat
    content_intent: str  # "savable", "shareable", "reach", "timely", "engagement"
    reasoning: str = ""


class Caption(BaseModel):
    """A platform-specific caption."""
    platform: Platform
    variant: str  # "v1" or "v2"
    caption_text: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    char_count: int = 0


class Slide(BaseModel):
    """A single carousel slide."""
    slide_number: int
    slide_type: str = ""  # "cover", "content", "cta"
    title: str = ""
    body: str = ""
    visual_notes: str = ""


class Theme(BaseModel):
    """Visual theme for content."""
    primary_color: str = ""
    secondary_color: str = ""
    accent_color: str = ""
    background_color: str = ""
    text_color: str = ""
    font_heading: str = ""
    font_body: str = ""
    style_notes: str = ""
    mood: str = ""


class ReelScript(BaseModel):
    """Script for a reel/short-form video."""
    hook: str = ""  # First 3 seconds
    full_script: str = ""
    storyboard: list[dict[str, str]] = Field(default_factory=list)
    thumbnail_prompt: str = ""
    music_suggestion: str = ""
    estimated_duration_seconds: int = 30


class ChatMessage(BaseModel):
    """A message in the chat edit conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_triggered: str | None = None  # Which node was re-run


class TopicContent(BaseModel):
    """All content for a single topic."""
    topic_id: str
    content_format: ContentFormat
    theme: Theme = Field(default_factory=Theme)
    slides: list[Slide] = Field(default_factory=list)
    image_prompts: list[str] = Field(default_factory=list)
    react_code: str = ""
    reel_script: ReelScript | None = None
    captions: dict[str, dict[str, Caption]] = Field(default_factory=dict)
    status: ContentStatus = ContentStatus.PENDING
    edit_chat: list[ChatMessage] = Field(default_factory=list)


class DeepResearchItem(BaseModel):
    """Deep research for a single topic."""
    topic_id: str
    prompt: str = ""
    result: str = ""


class PipelineError(BaseModel):
    """An error that occurred during pipeline execution."""
    node: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    retry_count: int = 0


# ── Main Pipeline State ──


class ContentForgeState(BaseModel):
    """Full pipeline state for LangGraph.

    This is the central state object that flows through the entire pipeline.
    Every node reads from and writes to this state.
    """

    # ── Metadata ──
    week_id: str = ""  # "2026-W16"
    pipeline_status: PipelinePhase = PipelinePhase.IDLE
    current_node: str = ""

    # ── Brand (loaded from files) ──
    brand_context: dict[str, Any] = Field(default_factory=dict)
    platform_rules: dict[str, Any] = Field(default_factory=dict)

    # ── Research ──
    research_prompts: list[str] = Field(default_factory=list)
    raw_research: list[str] = Field(default_factory=list)

    # ── Topics ──
    topic_bank: list[Topic] = Field(default_factory=list)

    # ── Plan ──
    weekly_plan: list[PlanItem] = Field(default_factory=list)
    selected_topics: list[str] = Field(default_factory=list)

    # ── Deep Research ──
    deep_research: dict[str, DeepResearchItem] = Field(default_factory=dict)

    # ── Content (per topic) ──
    content: dict[str, TopicContent] = Field(default_factory=dict)

    # ── Control Flow ──
    human_action_required: bool = False
    human_action_type: HumanActionType | None = None
    pending_topic_id: str | None = None
    errors: list[PipelineError] = Field(default_factory=list)

    class Config:
        use_enum_values = True
