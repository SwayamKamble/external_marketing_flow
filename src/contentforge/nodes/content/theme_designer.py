"""Node to apply per-topic visual theme from deep research."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import Theme, enum_value
from contentforge.nodes._base import BaseNode, NodeContext


class ThemeDesigner(BaseNode):
    """Locks theme to deep-research `content_spec.theme` for each topic."""

    node_name = "theme_designer"
    category = "content"
    description = "Applies deep-research theme without fallback replacement."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        content_dict = input_data.get("content", {})
        topic_id = input_data.get("pending_topic_id")
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]
        deep_res = input_data.get("deep_research", {}).get(topic_id)
        deep_theme = {}
        if deep_res:
            if isinstance(deep_res, dict):
                deep_theme = (deep_res.get("content_spec") or {}).get("theme") or {}
            else:
                deep_theme = (getattr(deep_res, "content_spec", None) or {}).get("theme") or {}

        required = ("primary_color", "secondary_color", "accent_color", "background_color", "text_color", "font_heading", "font_body")
        missing = [field for field in required if not str(deep_theme.get(field) or "").strip()]
        if missing:
            if context.logger:
                context.logger.error(
                    self.node_name,
                    f"Missing deep-research theme fields for {topic_id}: {', '.join(missing)}. Keeping theme unchanged.",
                )
            return {}

        tc.theme = Theme(
            primary_color=str(deep_theme.get("primary_color") or "").strip(),
            secondary_color=str(deep_theme.get("secondary_color") or "").strip(),
            accent_color=str(deep_theme.get("accent_color") or "").strip(),
            background_color=str(deep_theme.get("background_color") or "").strip(),
            text_color=str(deep_theme.get("text_color") or "").strip(),
            font_heading=str(deep_theme.get("font_heading") or "").strip(),
            font_body=str(deep_theme.get("font_body") or "").strip(),
            style_notes=str(deep_theme.get("style_notes") or "").strip(),
            mood=str(deep_theme.get("mood") or "").strip(),
        )

        self.save_artifact(
            context=context,
            phase="05_content",
            topic_id=topic_id,
            filename="theme.md",
            content=(
                "# Theme definition\n\n"
                f"Mood: {tc.theme.mood}\n\n"
                "Colors:\n"
                f"- BG: {tc.theme.background_color}\n"
                f"- Text: {tc.theme.text_color}\n"
                f"- Primary: {tc.theme.primary_color}\n"
                f"- Accent: {tc.theme.accent_color}\n\n"
                "Fonts:\n"
                f"- Heading: {tc.theme.font_heading}\n"
                f"- Body: {tc.theme.font_body}\n\n"
                f"Notes: {tc.theme.style_notes}"
            ),
        )
        self.save_artifact(
            context=context,
            phase="05_content",
            topic_id=topic_id,
            filename="theme.json",
            content=json.dumps(tc.theme.model_dump(), indent=2),
        )

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        if context.logger:
            context.logger.event(
                "theme_designer.deep_research_locked",
                {"topic_id": topic_id, "format": enum_value(tc.content_format)},
            )
        return {"content": updated_content}
