from unittest.mock import MagicMock

import pytest

from contentforge.nodes._base import NodeContext
from contentforge.nodes.deep_research.deep_research_parser import DeepResearchParser


@pytest.mark.asyncio
async def test_deep_research_parser_recovers_plaintext_carousel_into_multi_slides():
    node = DeepResearchParser()
    context = MagicMock(spec=NodeContext)
    context.week_id = "2026-W21"
    context.logger = MagicMock()
    context.memory = MagicMock()

    input_data = {
        "pending_topic_id": "topic_1",
        "raw_deep_research": {
            "topic_1": (
                "OpenAI announced major updates. Benchmark gains were reported across reasoning and coding tasks. "
                "Several companies integrated new APIs this week. Builders can now automate larger workflows. "
                "Analysts expect increased competition in enterprise AI tooling."
            )
        },
        "weekly_plan": [
            {
                "topic_id": "topic_1",
                "content_format": "carousel",
            }
        ],
        "topic_bank": [{"id": "topic_1", "title": "AI Model Updates"}],
        "selected_topics": ["topic_1"],
        "topic_queue": ["topic_1"],
        "deep_research": {},
        "content": {},
    }

    result = await node.process(input_data, context)

    tc = result["content"]["topic_1"]
    assert len(tc.carousel_slides) >= 6
    assert result["pipeline_status"] == "content_creation"
    assert result["pending_topic_id"] is None


@pytest.mark.asyncio
async def test_deep_research_parser_expands_weak_json_carousel_slides():
    node = DeepResearchParser()
    context = MagicMock(spec=NodeContext)
    context.week_id = "2026-W21"
    context.logger = MagicMock()
    context.memory = MagicMock()

    weak_payload = """{
      "structured_research": "Practical AI workflow impact and tool adoption trends.",
      "content_spec": {
        "theme": {"primary_color": "#0f172a"},
        "slides": [
          {"slide_number": 1, "heading": "Only slide", "body_text": "Too short set."}
        ]
      }
    }"""

    input_data = {
        "pending_topic_id": "topic_2",
        "raw_deep_research": {"topic_2": weak_payload},
        "weekly_plan": [{"topic_id": "topic_2", "content_format": "carousel"}],
        "topic_bank": [{"id": "topic_2", "title": "Agent Workflows"}],
        "selected_topics": ["topic_2"],
        "topic_queue": ["topic_2"],
        "deep_research": {},
        "content": {},
    }

    result = await node.process(input_data, context)
    tc = result["content"]["topic_2"]
    assert len(tc.carousel_slides) >= 6
    assert result["pipeline_status"] == "content_creation"


@pytest.mark.asyncio
async def test_deep_research_parser_strips_json_like_slide_text():
    node = DeepResearchParser()
    context = MagicMock(spec=NodeContext)
    context.week_id = "2026-W21"
    context.logger = MagicMock()
    context.memory = MagicMock()

    payload = """{
      "structured_research": "Model launch and benchmark deltas.",
      "content_spec": {
        "theme": {"primary_color": "#0f172a"},
        "slides": [
          {
            "slide_number": 1,
            "heading": "{\\"title\\": \\"AI Launch\\"}",
            "body_text": "{\\"description\\": \\"Benchmark improved by 18% and latency dropped.\\"}"
          },
          {
            "slide_number": 2,
            "heading": "Why it matters",
            "body_text": "Teams can ship faster with fewer regressions."
          }
        ]
      }
    }"""

    input_data = {
        "pending_topic_id": "topic_3",
        "raw_deep_research": {"topic_3": payload},
        "weekly_plan": [{"topic_id": "topic_3", "content_format": "carousel"}],
        "topic_bank": [{"id": "topic_3", "title": "Model Benchmark Update"}],
        "selected_topics": ["topic_3"],
        "topic_queue": ["topic_3"],
        "deep_research": {},
        "content": {},
    }

    result = await node.process(input_data, context)
    tc = result["content"]["topic_3"]
    assert len(tc.carousel_slides) >= 6
    assert not tc.carousel_slides[0].heading.strip().startswith("{")
    assert not tc.carousel_slides[0].body_text.strip().startswith("{")


@pytest.mark.asyncio
async def test_deep_research_parser_handles_trailing_citations():
    node = DeepResearchParser()
    context = MagicMock(spec=NodeContext)
    context.week_id = "2026-W21"
    context.logger = MagicMock()
    context.memory = MagicMock()

    payload_with_citation = """{
      "structured_research": "OpenAI released GPT-5.4 Mini and Nano.", [timesofindia.indiatimes](https://timesofindia.indiatimes.com/technology/tech-news/openai-launches-gpt-5-4-mini-and-nano)
      "content_spec": {
        "theme": {
          "primary_color": "#0b1324",
          "secondary_color": "#101a33",
          "accent_color": "#f59e0b",
          "background_color": "#060b16",
          "text_color": "#f8fafc",
          "font_heading": "Sora",
          "font_body": "Inter",
          "mood": "Sharp, technical"
        },
        "slides": [
          {
            "slide_number": 1,
            "heading": "AI features just got cheaper",
            "body_text": "GPT-5.4 Mini and Nano are smaller-footprint models built for speed.",
            "image_description": "Dark futuristic dashboard.",
            "image_placement": "background"
          }
        ]
      }
    }"""

    input_data = {
        "pending_topic_id": "topic_4",
        "raw_deep_research": {"topic_4": payload_with_citation},
        "weekly_plan": [{"topic_id": "topic_4", "content_format": "single_image"}],
        "topic_bank": [{"id": "topic_4", "title": "AI Features Pricing"}],
        "selected_topics": ["topic_4"],
        "topic_queue": ["topic_4"],
        "deep_research": {},
        "content": {},
    }

    result = await node.process(input_data, context)
    tc = result["content"]["topic_4"]
    assert tc.theme.font_heading == "Sora"
    assert tc.theme.font_body == "Inter"
    assert len(tc.carousel_slides) == 1
    assert tc.carousel_slides[0].heading == "AI features just got cheaper"
