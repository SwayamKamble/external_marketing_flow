"""Node to generate visual theme and aesthetic guidelines."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import Theme
from contentforge.nodes._base import BaseNode, NodeContext


class ThemeDesigner(BaseNode):
    """Selects colors, fonts, and visual themes for a topic.

    Uses the topic's content format and the overarching brand style guide
    to generate a specific JSON aesthetic theme to be used by React renderers
    or image generation prompts.
    """

    node_name = "theme_designer"
    category = "content"
    description = "Generates specific thematic guidelines for the content output."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        content_dict = input_data.get("content", {})
        topic_id = input_data.get("pending_topic_id")
        
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]
        
        # We only need a theme if we haven't generated one yet or if requested
        if tc.theme and tc.theme.primary_color: # Hacky check for non-empty theme
            return {}

        # Look up the topic info for context
        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if t.id == topic_id), None)
        
        if not topic:
            return {}

        system_prompt, config = self.load_prompt(context)
        
        # Call LLM
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Design a theme for this topic: '{topic.title}'\nType: {tc.content_format.value}\nAngle: {topic.suggested_angle}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.6), # Creative
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                tc.theme = Theme(
                    primary_color=parsed.get("primary_color", ""),
                    secondary_color=parsed.get("secondary_color", ""),
                    accent_color=parsed.get("accent_color", ""),
                    background_color=parsed.get("background_color", ""),
                    text_color=parsed.get("text_color", ""),
                    font_heading=parsed.get("font_heading", ""),
                    font_body=parsed.get("font_body", ""),
                    style_notes=parsed.get("style_notes", ""),
                    mood=parsed.get("mood", "")
                )
                
                # Save artifact
                self.save_artifact(
                   context=context,
                   phase="05_content",
                   topic_id=topic_id,
                   filename="theme.md",
                   content=f"# Theme definition\n\nMood: {tc.theme.mood}\n\nColors:\n- BG: {tc.theme.background_color}\n- Text: {tc.theme.text_color}\n- Primary: {tc.theme.primary_color}\n- Accent: {tc.theme.accent_color}\n\nNotes: {tc.theme.style_notes}"
                )
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Theme parsing failed: {e}")

        # Update the specific topic content mapping
        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        return {"content": updated_content}
