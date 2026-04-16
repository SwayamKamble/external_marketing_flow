"""Node to generate deep research prompts for selected topics."""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


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
        
        if not selected_topics_ids or not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "selected_topics or topic_bank missing.")
            return {"pipeline_status": "deep_research"}

        # Filter the bank to only the selected topics
        selected_topics = [t for t in topic_bank if t.id in selected_topics_ids]

        if not selected_topics:
            if context.logger:
                context.logger.error(self.node_name, "No topics matched the selected IDs.")
            return {"pipeline_status": "deep_research"}

        system_prompt, config = self.load_prompt(context)
        
        payload = [
            {
                "id": t.id,
                "title": t.title,
                "summary": t.summary,
                "key_points": t.key_points,
                "suggested_angle": t.suggested_angle
            }
            for t in selected_topics
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

        # Save artifact for human to copy-paste
        content = "# Deep Research Requests\n\n"
        content += "Please copy these prompts into Perplexity/ChatGPT and paste the results back.\n\n"
        
        for item in prompts_data:
            tid = item.get("topic_id")
            title = next((t.title for t in selected_topics if t.id == tid), "Unknown")
            content += f"## Topic: {title}\n"
            content += f"**ID:** `{tid}`\n\n"
            content += f"```text\n{item.get('prompt')}\n```\n\n"

        self.save_artifact(
            context=context,
            phase="04_deep_research",
            filename="deep_research_prompts.md",
            content=content,
        )

        return {
            "pipeline_status": "deep_research",
            "human_action_required": True,
            "human_action_type": "paste_deep_research"
        }
