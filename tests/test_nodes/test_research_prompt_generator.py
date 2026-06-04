from unittest.mock import MagicMock

import pytest

from contentforge.nodes._base import NodeContext
from contentforge.nodes.research.research_prompt_generator import ResearchPromptGenerator


@pytest.mark.asyncio
async def test_research_prompt_generator_requests_broad_topic_batches():
    node = ResearchPromptGenerator()
    context = MagicMock(spec=NodeContext)
    context.week_id = "test_week"
    context.topic_id = ""
    context.memory = MagicMock()

    result = await node.process(
        {
            "brand_context": {
                "brand_dna": "AI builders and Indian founders",
                "content_pillars": "AI news, tools, tutorials, opinions",
            }
        },
        context,
    )

    prompts = result["research_prompts"]
    assert len(prompts) == 4
    assert all("10" in prompt for prompt in prompts)
    assert all("source_url" in prompt for prompt in prompts)
    assert all("why_it_matters" in prompt for prompt in prompts)
    assert "3 most significant" not in prompts[0]
