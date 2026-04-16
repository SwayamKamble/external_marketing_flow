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
        # raw_deep_research structure assumption: {"topic_id1": "raw text...", "topic_id2": "raw text..."}
        raw_deep_research_dict = input_data.get("raw_deep_research", {})
        
        if not raw_deep_research_dict:
            if context.logger:
                context.logger.error(self.node_name, "raw_deep_research dictionary is empty.")
            return {"deep_research": {}}

        system_prompt, config = self.load_prompt(context)
        deep_res_objects = {}

        for topic_id, raw_text in raw_deep_research_dict.items():
            result = await self.call_llm(
                context=context,
                system_prompt=system_prompt,
                user_message=f"Topic ID: {topic_id}\n\nRaw Research:\n{raw_text}",
                response_format={"type": "json_object"},
                model=config.get("model", "gpt-5-chat"),
                temperature=config.get("temperature", 0.2),
            )

            if result.success:
                try:
                    parsed = json.loads(result.content)
                    deep_res_objects[topic_id] = DeepResearchItem(
                        topic_id=topic_id,
                        prompt="human_pasted",
                        result=parsed.get("structured_research", raw_text)
                    )
                    
                    self.save_artifact(
                        context=context,
                        phase="04_deep_research",
                        topic_id=topic_id,
                        filename="structured_research.md",
                        content=f"# Structured Research\n\n{parsed.get('structured_research', raw_text)}",
                    )
                except Exception as e:
                    if context.logger:
                        context.logger.error(self.node_name, f"Failed parsing deep research for {topic_id}: {e}")
            else:
                 if context.logger:
                     context.logger.error(self.node_name, f"LLM analysis failed for {topic_id}")

        return {"deep_research": deep_res_objects}
