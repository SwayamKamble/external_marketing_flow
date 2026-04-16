"""Node to parse raw research text into structured topic entities."""

from __future__ import annotations

import json
from typing import Any
import uuid

from contentforge.core.state import Topic, ContentFormat
from contentforge.nodes._base import BaseNode, NodeContext


class ResearchParser(BaseNode):
    """Parses raw text research into structured Topic objects.

    This node takes the raw output pasted by the human (from external LLMs like
    ChatGPT/Perplexity), analyzes it, and extracts distinct, coherent topics
    ready for the scoring and planning phases.
    """

    node_name = "research_parser"
    category = "research"
    description = "Parses raw research text into a list of structured Topic objects."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Parse raw research into Topic objects."""
        # Grab raw_research from input or state
        raw_research = input_data.get("raw_research", [])
        if not raw_research:
            if context.logger:
                context.logger.error(self.node_name, "No raw research provided to parse.")
            return {"topic_bank": []}

        # Combine all research strings into one giant text block for parsing
        combined_text = "\n\n=== SOURCE ===\n\n".join(raw_research)

        # Load prompt
        system_prompt, config = self.load_prompt(context)

        # LLM Call
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Here is the raw research gathered:\n\n{combined_text}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.3),  # Lower temp for parsing
            max_tokens=config.get("max_tokens", 4096),
        )

        if not result.success:
            if context.logger:
                context.logger.error(self.node_name, f"Failed to parse research: {result.error}")
            return {"topic_bank": []}

        # Parse the JSON response
        try:
            parsed = json.loads(result.content)
            topics_data = parsed.get("topics", [])
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"Invalid JSON returned: {e}")
            raise ValueError(f"Failed to parse topic JSON:\n{result.content}")

        # Convert to Pydantic objects
        topic_bank = []
        for t_dict in topics_data:
            try:
                # Ensure it has an ID
                topic_id = f"topic_{uuid.uuid4().hex[:8]}"

                # Parse suggested format safely
                format_str = t_dict.get("suggested_format", "").lower()
                try:
                    fmt = ContentFormat(format_str)
                except ValueError:
                    fmt = ContentFormat.SINGLE_IMAGE

                topic = Topic(
                    id=topic_id,
                    title=t_dict.get("title", "Untitled Topic"),
                    summary=t_dict.get("summary", ""),
                    category=t_dict.get("category", "General"),
                    source=t_dict.get("source", "Assorted Web Search"),
                    key_points=t_dict.get("key_points", []),
                    tags=t_dict.get("tags", []),
                    suggested_format=fmt,
                    suggested_angle=t_dict.get("suggested_angle", ""),
                )
                topic_bank.append(topic)
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Could not create Topic object: {e} | data: {t_dict}")
                # Skip invalid ones instead of failing the whole batch
                continue

        # Save artifact for debug/history
        self.save_artifact(
            context=context,
            phase="01_research",
            filename="parsed_topics.md",
            content="\n\n".join(
                f"## {t.title}\n{t.summary}\n- Angle: {t.suggested_angle}\n- Format: {t.suggested_format.value}"
                for t in topic_bank
            ),
            metadata={"parsed_count": len(topic_bank), "model": result.model}
        )

        return {"topic_bank": topic_bank}
