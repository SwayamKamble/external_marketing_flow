"""Carousel supervisor node."""

from __future__ import annotations

from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


class CarouselCreator(BaseNode):
    """Supervisor node for the Carousel sub-graph.

    This node triggers the sub-steps needed for a carousel (Slide Writer
    and then React Code Generator) according to the Hierarchical Delegation pattern.
    """

    node_name = "carousel_creator"
    category = "content"
    description = "Supervises the creation of carousel slide content and render code."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Determine what step of the carousel creation we are in."""
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]

        if tc.content_format.value != "carousel":
            return {}
            
        # Logging progress
        if context.logger:
            context.logger.event("carousel.step", {"topic": topic_id, "status": "started"})
        
        # State machine signal to the LangGraph layer (handled in graph.py)
        return {"carousel_status": "generating_slides"}
