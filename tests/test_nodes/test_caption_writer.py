import pytest
from unittest.mock import AsyncMock, MagicMock
from contentforge.nodes.content.caption_writer import CaptionWriter
from contentforge.nodes._base import NodeContext
from contentforge.core.state import TopicContent, ContentFormat, ContentStatus, Platform, Topic
import json

@pytest.mark.asyncio
async def test_caption_writer_success():
    node = CaptionWriter()
    
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.logger = MagicMock()
    context.memory = MagicMock()
    context.prompts = MagicMock()
    
    # Mock system prompt
    context.prompts.build_prompt.return_value = ("System prompt", {"model": "mock", "temperature": 0.7})
    
    # Setup inputs
    topic_id = "t1"
    topic1 = Topic(id="t1", title="Test", summary="sum", suggested_angle="x")
    tc = TopicContent(topic_id=topic_id, content_format=ContentFormat.CAROUSEL, status=ContentStatus.PENDING)
    
    input_data = {
        "pending_topic_id": topic_id,
        "content": {topic_id: tc},
        "topic_bank": [topic1],
        "deep_research": {}
    }
    
    # Mock LLM
    mock_llm_result = MagicMock()
    mock_llm_result.success = True
    mock_llm_result.content = json.dumps({
        "variants": [
            {"variant": "v1", "caption_text": "Text 1", "cta": "Click here", "hashtags": ["#ai"]},
            {"variant": "v2", "caption_text": "Text 2", "cta": "Save this", "hashtags": ["#tech"]}
        ]
    })
    
    context.llm = AsyncMock()
    context.llm.call = AsyncMock(return_value=mock_llm_result)
    
    # Run the fan-out
    result = await node.process(input_data, context)
    
    # Assertions
    assert "content" in result
    updated_tc = result["content"][topic_id]
    
    # It must have written captions for all 4 platforms
    assert Platform.INSTAGRAM.value in updated_tc.captions
    assert Platform.LINKEDIN.value in updated_tc.captions
    assert Platform.X.value in updated_tc.captions
    assert Platform.THREADS.value in updated_tc.captions
    
    # Each platform should have v1 and v2
    insta = updated_tc.captions[Platform.INSTAGRAM.value]
    assert "v1" in insta
    assert insta["v1"].caption_text == "Text 1"
    assert insta["v1"].platform == Platform.INSTAGRAM
    
    # Wait for the artifact
    context.memory.write_artifact.assert_called_once()
