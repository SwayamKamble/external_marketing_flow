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
        selected_topics = input_data.get("selected_topics", [])
        existing_content = input_data.get("content", {})

        if not weekly_plan:
            if context.logger:
                context.logger.error(self.node_name, "No weekly plan available to route.")
            return {"pipeline_status": "content_creation"}

        if not selected_topics:
            return {
                "pipeline_status": "planning",
                "human_action_required": True,
                "human_action_type": "select_topics",
            }

        routes_needed = []
        updated_content = dict(existing_content)
        plan_by_topic = {item.topic_id: item for item in weekly_plan if item.topic_id}

        # Ensure every selected topic has a TopicContent state object.
        for topic_id in selected_topics:
            item = plan_by_topic.get(topic_id)
            if not item:
                continue
            
            # Create a TopicContent tracking object if it doesn't exist
            if topic_id not in updated_content:
                updated_content[topic_id] = TopicContent(
                    topic_id=topic_id,
                    content_format=item.content_format,
                    status=ContentStatus.PENDING
                )
                
            tc = updated_content[topic_id]
            
            # Route all topics that are not exported yet.
            if tc.status != ContentStatus.EXPORTED:
                routes_needed.append({
                    "topic_id": topic_id,
                    "format": tc.content_format.value
                })

        # Log routing logic
        if context.logger:
            context.logger.event("content.routing", {
                "routes": routes_needed
            })

        # Set pending_topic_id to the first one that still needs work.
        next_topic = routes_needed[0]["topic_id"] if routes_needed else None

        return {
            "content": updated_content,
            "routes_needed": routes_needed,
            "pipeline_status": "content_creation" if next_topic else "done",
            "pending_topic_id": next_topic,
            "topic_index": (selected_topics.index(next_topic) + 1) if next_topic in selected_topics else len(selected_topics),
            "topic_total": len(selected_topics),
        }
