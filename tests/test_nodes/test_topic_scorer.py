import pytest
from unittest.mock import AsyncMock, MagicMock
from contentforge.nodes.scoring.topic_scorer import TopicScorer
from contentforge.nodes._base import NodeContext
from contentforge.core.state import Topic
import json

@pytest.mark.asyncio
async def test_topic_scorer_success():
    node = TopicScorer()
    
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.logger = MagicMock()
    context.memory = MagicMock()
    context.prompts = MagicMock()
    
    # Mock prompt loader
    context.prompts.build_prompt.return_value = ("System prompt", {"model": "mock", "temperature": 0.3})
    
    # Setup initial topics
    topic1 = Topic(id="t1", title="Topic 1", summary="Sum 1", score=0.0)
    topic2 = Topic(id="t2", title="Topic 2", summary="Sum 2", score=0.0)
    input_data = {"topic_bank": [topic1, topic2]}
    
    # Mock LLM API Call
    mock_llm_result = MagicMock()
    mock_llm_result.success = True
    mock_llm_result.content = json.dumps({
        "scores": [
            {"id": "t1", "score": 8.5, "reasoning": "Great topic"},
            {"id": "t2", "score": 6.0, "reasoning": "Okay topic"}
        ]
    })
    
    context.llm = AsyncMock()
    context.llm.call = AsyncMock(return_value=mock_llm_result)
    
    # Run process
    result = await node.process(input_data, context)
    
    assert "topic_bank" in result
    updated_topics = result["topic_bank"]
    
    # Should be sorted by score descending
    assert len(updated_topics) == 2
    assert updated_topics[0].id == "t1"
    assert updated_topics[0].score == 8.5
    assert updated_topics[0].scoring_reasoning == "Great topic"
    
    assert updated_topics[1].id == "t2"
    assert updated_topics[1].score == 6.0
    
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
