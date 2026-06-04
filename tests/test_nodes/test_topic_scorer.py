import pytest
from unittest.mock import MagicMock
from contentforge.nodes.scoring.topic_scorer import TopicScorer
from contentforge.nodes._base import NodeContext
from contentforge.core.state import Topic

@pytest.mark.asyncio
async def test_topic_scorer_success():
    node = TopicScorer()
    
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.logger = MagicMock()
    context.memory = MagicMock()
    # Setup initial topics with different richness so deterministic scoring ranks topic1 first.
    topic1 = Topic(
        id="t1",
        title="Topic 1 with strong practical depth",
        summary="Sum 1",
        key_points=["a", "b", "c", "d"],
        suggested_angle="Specific and actionable framing for creators",
        suggested_format="carousel",
        tags=["ai", "tools", "workflow"],
        category="News",
        source="Source A",
        score=0.0,
    )
    topic2 = Topic(id="t2", title="Topic 2", summary="Sum 2", score=0.0)
    input_data = {"topic_bank": [topic1, topic2]}
    
    # Run process
    result = await node.process(input_data, context)
    
    assert "topic_bank" in result
    updated_topics = result["topic_bank"]
    
    # Should be sorted by score descending
    assert len(updated_topics) == 2
    assert updated_topics[0].id == "t1"
    assert updated_topics[0].score > updated_topics[1].score
    assert "Deterministic score:" in updated_topics[0].scoring_reasoning
    
    assert updated_topics[1].id == "t2"
    assert updated_topics[1].score == 3.0
    
    # Verify artifact written
    context.memory.write_artifact.assert_called_once()
    args, kwargs = context.memory.write_artifact.call_args
    assert kwargs["phase"] == "02_scoring"
    assert "topic_scores.md" == kwargs["filename"]

@pytest.mark.asyncio
async def test_topic_scorer_empty_input():
    node = TopicScorer()
    context = MagicMock(spec=NodeContext)
    context.logger = MagicMock()
    
    result = await node.process({"topic_bank": []}, context)
    assert result == {"topic_bank": []}
    context.logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_topic_scorer_limits_to_top_7_topics():
    node = TopicScorer()
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.logger = MagicMock()
    context.memory = MagicMock()

    # Build 10 valid topics with deterministic score inputs.
    topics = [
        Topic(
            id=f"t{i}",
            title=f"Topic number {i} with practical details",
            summary="Summary",
            key_points=["k1", "k2", "k3", "k4"],
            suggested_angle="A concrete execution angle for creators",
            suggested_format="carousel",
            tags=["ai", "tools", "workflow", "news"],
            category="News",
            source="Example Source",
        )
        for i in range(10)
    ]

    result = await node.process({"topic_bank": topics}, context)
    assert "topic_bank" in result
    assert len(result["topic_bank"]) == 7
