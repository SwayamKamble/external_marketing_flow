"""Node to parse returned deep research into state."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import DeepResearchItem
from contentforge.nodes._base import BaseNode, NodeContext


class DeepResearchParser(BaseNode):
    """Takes pasted deep research results and structures them.

    Maps the human-provided deep research back to the specific
    topic_ids so it can be passed down to the content creators.
    """

    node_name = "deep_research_parser"
    category = "research"
    description = "Parses pasted deep research data into the structured state."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        # raw_deep_research structure assumption: {"topic_id": "raw text..."}
        raw_deep_research_dict = input_data.get("raw_deep_research", {})
        pending_topic_id = input_data.get("pending_topic_id")

        if not pending_topic_id:
            return {
                "pipeline_status": "deep_research",
                "human_action_required": True,
                "human_action_type": "paste_deep_research",
            }

        if not raw_deep_research_dict:
            if context.logger:
                context.logger.error(self.node_name, "raw_deep_research dictionary is empty.")
            return {
                "pipeline_status": "deep_research",
                "human_action_required": True,
                "human_action_type": "paste_deep_research",
            }

        raw_text = raw_deep_research_dict.get(pending_topic_id)
        if not raw_text:
            if context.logger:
                context.logger.error(self.node_name, f"No deep research provided for pending topic {pending_topic_id}.")
            return {
                "pipeline_status": "deep_research",
                "human_action_required": True,
                "human_action_type": "paste_deep_research",
            }

        system_prompt, config = self.load_prompt(context)
        deep_res_objects = dict(input_data.get("deep_research", {}))

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Topic ID: {pending_topic_id}\n\nRaw Research:\n{raw_text}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.2),
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                deep_res_objects[pending_topic_id] = DeepResearchItem(
                    topic_id=pending_topic_id,
                    prompt="human_pasted",
                    result=parsed.get("structured_research", raw_text),
                )

                self.save_artifact(
                    context=context,
                    phase="04_deep_research",
                    topic_id=pending_topic_id,
                    filename="structured_research.md",
                    content=f"# Structured Research\n\n{parsed.get('structured_research', raw_text)}",
                )
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Failed parsing deep research for {pending_topic_id}: {e}")
        else:
            if context.logger:
                context.logger.error(self.node_name, f"LLM analysis failed for {pending_topic_id}")

        selected_topics = input_data.get("selected_topics", [])
        queue = [tid for tid in selected_topics if tid not in deep_res_objects]
        next_topic = queue[0] if queue else None

        updated_raw = dict(raw_deep_research_dict)
        updated_raw.pop(pending_topic_id, None)

        return {
            "deep_research": deep_res_objects,
            "raw_deep_research": updated_raw,
            "topic_queue": queue,
            "pending_topic_id": next_topic,
            "topic_index": (selected_topics.index(next_topic) + 1) if next_topic and next_topic in selected_topics else len(selected_topics),
            "topic_total": len(selected_topics),
            "pipeline_status": "deep_research" if next_topic else "content_creation",
        }
