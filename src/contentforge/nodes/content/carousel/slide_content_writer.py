"""Slide writing node."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import CarouselSlide
from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


class SlideContentWriter(BaseNode):
    """Generates the text content for each carousel slide.
    
    Transforms deep research into a 4-8 slide deck script containing
    hook, body points, and a CTA slide.
    """

    node_name = "slide_content_writer"
    category = "content"
    description = "Writes the paginated content for a visual carousel."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        tc = content_dict.get(topic_id)
        if not tc or tc.content_format.value != "carousel":
            return {}

        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if _topic_get(t, "id") == topic_id), None)
        deep_res = input_data.get("deep_research", {}).get(topic_id)

        system_prompt, config = self.load_prompt(context)
        
        ctx = f"Title: {_topic_get(topic, 'title', '') if topic else ''}\nAngle: {_topic_get(topic, 'suggested_angle', '') if topic else ''}\n"
        if deep_res:
            ctx += f"\nFacts:\n{deep_res.result}"

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Write the carousel outline for:\n\n{ctx}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.6),
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                slides_data = parsed.get("slides", [])
                
                slides = []
                for s in slides_data:
                    slides.append(CarouselSlide(
                        slide_number=s.get("slide_number", 1),
                        heading=s.get("heading", ""),
                        body_text=s.get("body_text", ""),
                        visual_concept=s.get("visual_concept", "")
                    ))
                
                tc.carousel_slides = slides
                
                # Save artifact
                content = "# Carousel Slides\n\n"
                for slide in slides:
                    content += f"## Slide {slide.slide_number}: {slide.heading}\n"
                    content += f"{slide.body_text}\n"
                    content += f"*(Visual: {slide.visual_concept})*\n\n"
                    
                self.save_artifact(
                   context=context,
                   phase="05_content",
                   topic_id=topic_id,
                   filename="carousel_slides.md",
                   content=content
                )
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Slide parsing failed: {e}")

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        return {"content": updated_content, "carousel_status": "generating_code"}
