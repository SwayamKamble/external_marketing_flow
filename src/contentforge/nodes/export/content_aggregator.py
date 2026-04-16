"""Node to validate and aggregate finalized content."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import ContentStatus
from contentforge.nodes._base import BaseNode, NodeContext


class ContentAggregator(BaseNode):
    """Aggregates all finalized content.

    Pulls together the generated text, prompts, and React code
    for the topic into a single final payload ready for disk packaging
    or API transmission.
    """

    node_name = "content_aggregator"
    category = "export"
    description = "Pulls all finalized content objects into a single export payload."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        if not topic_id or topic_id not in content_dict:
            return {"pipeline_status": "done"}

        tc = content_dict[topic_id]

        # In a real system, we'd maybe do a final validator LLM pass here.
        # For phase 2, we just aggregate the pydantic model.
        export_payload = tc.model_dump()
        
        # Save a master artifact
        self.save_artifact(
            context=context,
            phase="07_output",
            topic_id=topic_id,
            filename="final_payload.json",
            content=json.dumps(export_payload, indent=2, default=str),
        )

        tc.status = ContentStatus.EXPORTED
        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        if context.logger:
            context.logger.event("content.exported", {"topic_id": topic_id})

        return {
            "content": updated_content,
            "final_export": export_payload,
            "pipeline_status": "packaging",
        }
