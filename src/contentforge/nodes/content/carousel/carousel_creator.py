"""Carousel supervisor node."""

from __future__ import annotations

from typing import Any

from contentforge.core.state import ContentStatus, enum_value
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
        deep_res = input_data.get("deep_research", {}).get(topic_id)

        if enum_value(tc.content_format) != "carousel":
            return {}
            
        # Logging progress
        if context.logger:
            context.logger.event("carousel.step", {
                "topic": topic_id,
                "has_slides": bool(tc.carousel_slides),
                "has_code": bool(tc.rendered_code),
            })
        
        # If slides already exist (pre-populated from deep_research_parser),
        # mark as done immediately — the frontend renders the themed slides directly.
        deep_spec = {}
        if deep_res:
            deep_spec = deep_res.get("content_spec", {}) if isinstance(deep_res, dict) else (getattr(deep_res, "content_spec", {}) or {})
        deep_slides = deep_spec.get("slides", []) if isinstance(deep_spec, dict) else []
        expected_count = len(deep_slides) if isinstance(deep_slides, list) else 0
        actual_count = len(tc.carousel_slides or [])
        required_count = expected_count if expected_count >= 2 else 2

        if actual_count >= required_count:
            # If we don't have the HTML slides generated yet, go generate them
            if not tc.rendered_code or tc.rendered_code == "FRONTEND_RENDERED" or not tc.rendered_code.strip().startswith("<!DOCTYPE"):
                return {
                    "carousel_status": "generating_code"
                }

            # Mark the content as draft — we have everything we need
            tc.status = ContentStatus.DRAFT
            updated_content = dict(content_dict)
            updated_content[topic_id] = tc
            return {
                "content": updated_content,
                "carousel_status": "done",
            }
        
        # Guard: If carousel_status is already "generating_slides" or "done", the slide_writer
        # has already attempted generation once. Rather than looping again (which
        # would be infinite since slide_writer is not generative), force-mark done.
        current_carousel_status = input_data.get("carousel_status", "")
        if current_carousel_status in ("generating_slides", "done"):
            if context.logger:
                context.logger.event("carousel_supervisor.loop_guard", {
                    "topic": topic_id,
                    "actual_slides": actual_count,
                    "required_slides": required_count,
                    "carousel_status": current_carousel_status,
                    "reason": "breaking potential infinite loop — forcing done",
                })
            tc.status = ContentStatus.DRAFT
            updated_content = dict(content_dict)
            updated_content[topic_id] = tc
            return {
                "content": updated_content,
                "carousel_status": "done",
            }

        # No slides yet — force slide generation for this carousel topic.
        return {"carousel_status": "generating_slides"}
