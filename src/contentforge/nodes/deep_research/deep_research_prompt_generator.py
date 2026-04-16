"""Node to generate deep research prompts for selected topics."""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


class DeepResearchPromptGenerator(BaseNode):
    """Generates specific deep-dive prompts for selected topics.

    After the user selects topics from the weekly plan, this node generates
    precise external search/LLM prompts (e.g., Perplexity queries) to gather
    the detailed data needed to write the actual content.
    """

    node_name = "deep_research_prompt_generator"
    category = "research"
    description = "Generates targeted deep-research prompts for selected topics."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        selected_topics_ids = input_data.get("selected_topics", [])
        topic_bank = input_data.get("topic_bank", [])

        if not selected_topics_ids:
            return {
                "pipeline_status": "planning",
                "human_action_required": True,
                "human_action_type": "select_topics",
            }

        if not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "topic_bank missing.")
            return {"pipeline_status": "deep_research"}

        # Filter the bank to only the selected topics
        selected_topics = [t for t in topic_bank if _topic_get(t, "id") in selected_topics_ids]

        if not selected_topics:
            if context.logger:
                context.logger.error(self.node_name, "No topics matched the selected IDs.")
            return {"pipeline_status": "deep_research"}

        deep_research = input_data.get("deep_research", {})
        existing_queue = input_data.get("topic_queue", [])
        pending_topic_id = input_data.get("pending_topic_id")
        remaining_topics = [tid for tid in selected_topics_ids if tid not in deep_research]

        queue = [tid for tid in existing_queue if tid in remaining_topics] or remaining_topics
        if not queue:
            return {
                "pipeline_status": "content_creation",
                "human_action_required": False,
                "human_action_type": None,
            }

        if pending_topic_id not in queue:
            pending_topic_id = queue[0]

        selected_topic = next((t for t in selected_topics if _topic_get(t, "id") == pending_topic_id), None)
        if not selected_topic:
            return {
                "pipeline_status": "deep_research",
                "topic_queue": queue,
                "pending_topic_id": queue[0],
            }

        system_prompt, config = self.load_prompt(context)

        payload = [
            {
                "id": _topic_get(selected_topic, "id", ""),
                "title": _topic_get(selected_topic, "title", ""),
                "summary": _topic_get(selected_topic, "summary", ""),
                "key_points": _topic_get(selected_topic, "key_points", []),
                "suggested_angle": _topic_get(selected_topic, "suggested_angle", ""),
            }
        ]

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Please generate deep research prompts for these topics:\n\n{json.dumps(payload, indent=2)}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.5),
        )

        if not result.success:
            raise RuntimeError(f"Deep research prompt generation failed: {result.error}")

        try:
            parsed = json.loads(result.content)
            prompts_data = parsed.get("requests", [])
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"JSON parse block: {e}")
            raise ValueError("Failed to parse output as JSON.")

        # Save artifact for human to copy-paste (single topic per step)
        content = "# Deep Research Request\n\n"
        content += "Please copy this prompt into Perplexity/ChatGPT and paste the result back for this topic.\n\n"

        for item in prompts_data:
            tid = item.get("topic_id")
            title = next((_topic_get(t, "title", "Unknown") for t in selected_topics if _topic_get(t, "id") == tid), "Unknown")
            content += f"## Topic: {title}\n"
            content += f"**ID:** `{tid}`\n\n"
            content += f"```text\n{item.get('prompt')}\n```\n\n"

        self.save_artifact(
            context=context,
            phase="04_deep_research",
            filename=f"deep_research_prompt_{pending_topic_id}.md",
            content=content,
        )

        return {
            "topic_queue": queue,
            "pending_topic_id": pending_topic_id,
            "topic_index": (selected_topics_ids.index(pending_topic_id) + 1) if pending_topic_id in selected_topics_ids else 0,
            "topic_total": len(selected_topics_ids),
            "pipeline_status": "deep_research",
            "human_action_required": True,
            "human_action_type": "paste_deep_research"
        }
