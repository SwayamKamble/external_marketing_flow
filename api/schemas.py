"""Pydantic schemas for the FastAPI layer."""

from pydantic import BaseModel, Field
from typing import Any, Optional


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


class FeedbackRequest(BaseModel):
    """Payload to provide human-in-the-loop feedback/approval."""
    action: str = Field(..., description="Action type like 'approve', 'edit', 'supply_raw_research', 'supply_deep_research'")
    feedback: str = Field("", description="Natural language feedback if rejecting/editing.")
    raw_research_data: Optional[str] = Field(None, description="Pasted raw research content for initial research phase.")
    deep_research_data: Optional[dict[str, str]] = Field(None, description="Pasted deep research if handling supply_deep_research action.")


class ArtifactResponse(BaseModel):
    """Response model for a read artifact."""
    week_id: str
    phase: str
    filename: str
    content: str
    metadata: dict[str, Any]
