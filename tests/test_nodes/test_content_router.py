import pytest
from unittest.mock import MagicMock

from contentforge.core.state import ContentStatus, PlanItem, TopicContent
from contentforge.nodes._base import NodeContext
from contentforge.nodes.content.content_router import ContentRouter


@pytest.mark.asyncio
async def test_content_router_skips_exported_string_status_and_routes_next_topic():
    node = ContentRouter()
    weekly_plan = [
        PlanItem(
            day="monday",
            date="2026-04-20",
            topic_id="topic_a",
            topic_title="Topic A",
            content_format="carousel",
            content_intent="reach",
        ),
        PlanItem(
            day="tuesday",
            date="2026-04-21",
            topic_id="topic_b",
            topic_title="Topic B",
            content_format="reel",
            content_intent="engagement",
        ),
    ]
    content = {
        "topic_a": TopicContent(
            topic_id="topic_a",
            content_format="carousel",
            status="exported",
        ),
        "topic_b": TopicContent(
            topic_id="topic_b",
            content_format="reel",
            status=ContentStatus.PENDING,
        ),
    }

    result = await node.process(
        {
            "weekly_plan": weekly_plan,
            "selected_topics": ["topic_a", "topic_b"],
            "content": content,
        },
        context=MagicMock(spec=NodeContext),
    )

    assert result["pending_topic_id"] == "topic_b"
    assert result["routes_needed"] == [{"topic_id": "topic_b", "format": "reel", "status": "pending"}]
    assert result["topic_index"] == 2
    assert result["topic_total"] == 2
