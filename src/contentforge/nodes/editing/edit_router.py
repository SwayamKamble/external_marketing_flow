"""Node to handle edit routing and review."""

from __future__ import annotations

from typing import Any

from contentforge.core.state import ContentStatus, status_is
from contentforge.nodes._base import BaseNode, NodeContext


class EditRouter(BaseNode):
    """Routes content to human review or back to generation.

    Checks if content has been explicitly approved. If not, it requests
    human feedback. If the human provides feedback, it routes to the Chat Edit Agent.
    """

    node_name = "edit_router"
    category = "editing"
    description = "Routes content review states."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]

        if status_is(tc.status, ContentStatus.APPROVED):
            return {"pipeline_status": "export"}

        # If not approved yet, we stay in the review phase
        return {
            "pipeline_status": "review",
        }
