"""Node to engineer image generation prompts."""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


class ImagePromptEngineer(BaseNode):
    """Generates precise image prompts (e.g., Midjourney).

    If a topic is meant to be a single_image or requires specific
    non-UI visuals, this node creates highly structured prompts for external
    AI image generators based on the aesthetic and topic.
    """

    node_name = "image_prompt_engineer"
    category = "content"
    description = "Writes targeted Midjourney/DALL-E prompts for the visual components."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]
        
        # Only needed if there is no pre-existing visual and the style demands it.
        # Skip if format is carousel (we render in React) unless they explicitly want a cover graphic.
        if tc.content_format.value not in ["single_image", "news_post", "carousel"]:
             return {}

        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if _topic_get(t, "id") == topic_id), None)
        if not topic:
             return {}

        system_prompt, config = self.load_prompt(context)
        
        theme_mood = tc.theme.mood if tc.theme else "Abstract, professional, tech"
        
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Write prompts for: {_topic_get(topic, 'title', '')}\nMood/Aesthetic: {theme_mood}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.7),
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                prompts = parsed.get("prompts", [])
                
                tc.image_prompts = prompts
                
                # Save artifact
                content = "# Image Generation Prompts\n\n"
                for i, p in enumerate(prompts):
                    content += f"## Option {i+1}\n```text\n{p}\n```\n\n"
                    
                self.save_artifact(
                   context=context,
                   phase="05_content",
                   topic_id=topic_id,
                   filename="image_prompts.md",
                   content=content
                )
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Image prompt parsing failed: {e}")

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        return {"content": updated_content}
