import pytest
from contentforge.nodes.deep_research.deep_research_prompt_generator import DeepResearchPromptGenerator
from contentforge.nodes._base import NodeContext
from contentforge.core.state import Topic

@pytest.mark.asyncio
async def test_deep_research_prompt_generator():
    node = DeepResearchPromptGenerator()
    
    # Mock context
    context = NodeContext(
        week_id="2026-W37",
        logger=None,
        memory=None,
    )
    
    input_data = {
        "selected_topics": ["topic_1"],
        "topic_bank": [
            Topic(
                id="topic_1",
                title="Python 3.13 Features",
                summary="An overview of new features in Python 3.13.",
                suggested_angle="Technical overview",
                key_points=["GIL disablement", "Improved performance"]
            )
        ],
        "deep_research": {},
        "topic_queue": ["topic_1"],
        "pending_topic_id": "topic_1",
        "weekly_plan": [
            {
                "topic_id": "topic_1",
                "content_format": "carousel"
            }
        ]
    }
    
    result = await node.process(input_data, context)
    assert result["pipeline_status"] == "deep_research"
    assert result["human_action_required"] is True
    assert result["human_action_type"] == "paste_deep_research"
    assert "Python 3.13 Features" in result["prompt_content"]
    assert "primary_color" in result["prompt_content"]
