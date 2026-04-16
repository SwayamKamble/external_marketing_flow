import pytest
from unittest.mock import AsyncMock, MagicMock
from contentforge.nodes.research.research_parser import ResearchParser
from contentforge.nodes._base import NodeContext
from contentforge.core.state import Topic, ContentFormat
import json

@pytest.mark.asyncio
async def test_research_parser_success():
    # Setup node and context
    node = ResearchParser()
    
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.topic_id = ""
    context.logger = MagicMock()
    context.memory = MagicMock()
    context.prompts = MagicMock()
    
    # Mock prompt loader
    context.prompts.build_prompt.return_value = ("System prompt", {"model": "mock", "temperature": 0.2})
    
    # Mock LLM API Call
    mock_llm_result = MagicMock()
    mock_llm_result.success = True
    mock_llm_result.content = json.dumps({
        "topics": [
            {
                "title": "Sam Altman's New Project",
                "summary": "Details on the new project...",
                "category": "News",
                "source": "TechCrunch",
                "key_points": ["Point A", "Point B"],
                "tags": ["openai"],
                "suggested_format": "news_post",
                "suggested_angle": "Why you should care"
            }
        ]
    })
    mock_llm_result.model = "mock-model"
    context.llm = AsyncMock()
    context.llm.call = AsyncMock(return_value=mock_llm_result)

    input_data = {"raw_research": ["Raw text about OpenAI's new project..."]}
    
    # Run node process
    result = await node.process(input_data, context)
    
    # Validate result
    assert "topic_bank" in result
    topics = result["topic_bank"]
    assert len(topics) == 1
    assert isinstance(topics[0], Topic)
    assert topics[0].title == "Sam Altman's New Project"
    assert topics[0].suggested_format == ContentFormat.NEWS_POST
    
    # Validate memory artifact was saved
    context.memory.write_artifact.assert_called_once()
    args, kwargs = context.memory.write_artifact.call_args
    assert kwargs["phase"] == "01_research"
    assert kwargs["filename"] == "parsed_topics.md"

@pytest.mark.asyncio
async def test_research_parser_empty_input():
    node = ResearchParser()
    context = MagicMock(spec=NodeContext)
    context.logger = MagicMock()
    
    result = await node.process({"raw_research": []}, context)
    assert result == {"topic_bank": []}
    context.logger.error.assert_called_once_with("research_parser", "No raw research provided to parse.")
