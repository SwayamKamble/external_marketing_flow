"""Node to route content generation based on desired format."""

from __future__ import annotations

from typing import Any

from contentforge.core.state import ContentStatus, TopicContent
from contentforge.nodes._base import BaseNode, NodeContext


class ContentRouter(BaseNode):
    """Initializes standard content objects and determines routing logic.

    This node implements the Hierarchical Delegation pattern. It reviews
    the weekly plan, ensures TopicContent objects exist for scheduled items,
    and returns routing signals so LangGraph knows which specialist nodes
    (carousel, reel, news) to trigger next.
    """

    node_name = "content_router"
    category = "content"
    description = "Routes content generation tasks to format-specific sub-graphs."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        weekly_plan = input_data.get("weekly_plan", [])
        existing_content = input_data.get("content", {})
        
        if not weekly_plan:
            if context.logger:
                context.logger.error(self.node_name, "No weekly plan available to route.")
            return {"pipeline_status": "content_creation"}

        routes_needed = []
        updated_content = dict(existing_content)

        # Ensure every item in the plan has a TopicContent state object
        for item in weekly_plan:
            topic_id = item.topic_id
            
            # Create a TopicContent tracking object if it doesn't exist
            if topic_id not in updated_content:
                updated_content[topic_id] = TopicContent(
                    topic_id=topic_id,
                    content_format=item.content_format,
                    status=ContentStatus.PENDING
                )
                
            tc = updated_content[topic_id]
            
            # If it's pending, we need to route it for creation
            if tc.status == ContentStatus.PENDING:
                routes_needed.append({
                    "topic_id": topic_id,
                    "format": tc.content_format.value
                })

        # Log routing logic
        if context.logger:
            context.logger.event("content.routing", {
                "routes": routes_needed
            })

        # Set pending_topic_id to the first one that needs work (if sequential)
        # Or this list can be used by LangGraph for parallel fan-out
        next_topic = routes_needed[0]["topic_id"] if routes_needed else None

        return {
            "content": updated_content,
            "routes_needed": routes_needed,
            "pipeline_status": "content_creation",
            "pending_topic_id": next_topic
        }
