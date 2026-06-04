"""Pydantic schemas for the FastAPI layer."""

from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


class StartPipelineRequest(BaseModel):
    """Request payload to start a new weekly pipeline."""
    week_id: str = Field(..., description="Unique ID for this week's content run.")


class PipelineStatusResponse(BaseModel):
    """Response containing the current pipeline state."""
    week_id: str
    status: str
    pending_topic_id: Optional[str] = None
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    state: dict[str, Any]
    prompt_content: Optional[str] = None  # Embedded prompt content for research phases


class FeedbackRequest(BaseModel):
    """Payload to provide human-in-the-loop feedback/approval."""
    action: Literal[
        "approve",
        "approve_plan",
        "approve_content",
        "edit",
        "select_topics",
        "supply_raw_research",
        "supply_deep_research",
    ] = Field(..., description="Action type controlling how the pipeline resumes.")
    feedback: str = Field("", description="Natural language feedback if rejecting/editing.")
    raw_research_data: Optional[str] = Field(None, description="Pasted raw research content for initial research phase.")
    deep_research_data: Optional[dict[str, str]] = Field(None, description="Optional map {topic_id: research_text} for deep research input.")
    deep_research_text: Optional[str] = Field(None, description="Deep research text for a single topic.")
    topic_id: Optional[str] = Field(None, description="Topic ID for topic-scoped actions.")
    selected_topics: Optional[list[str]] = Field(None, description="Explicitly selected topics to continue after planning.")


class ArtifactResponse(BaseModel):
    """Response model for a read artifact."""
    week_id: str
    phase: str
    filename: str
    content: str
    metadata: dict[str, Any]


class CarouselImage(BaseModel):
    """Single rendered carousel image payload."""
    filename: str
    data_url: str


class CarouselRenderRequest(BaseModel):
    """Payload to render carousel from updated/custom HTML."""
    html_content: Optional[str] = Field(None, description="Optional custom HTML content to render.")


class CarouselRenderResponse(BaseModel):
    """Rendered carousel preview response."""
    week_id: str
    topic_id: str
    count: int
    images: list[CarouselImage]
