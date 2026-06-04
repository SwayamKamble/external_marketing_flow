import pytest
from unittest.mock import MagicMock

from contentforge.core.state import ContentStatus, TopicContent, CarouselSlide
from contentforge.nodes._base import NodeContext
from contentforge.nodes.content.carousel.carousel_creator import CarouselCreator


@pytest.mark.asyncio
async def test_carousel_creator_starts_generation_when_empty():
    node = CarouselCreator()
    content = {
        "topic_a": TopicContent(
            topic_id="topic_a",
            content_format="carousel",
            status=ContentStatus.PENDING,
            carousel_slides=[],
        )
    }

    result = await node.process(
        {
            "pending_topic_id": "topic_a",
            "content": content,
            "deep_research": {},
            "carousel_status": "",
        },
        context=MagicMock(spec=NodeContext),
    )

    assert result == {"carousel_status": "generating_slides"}


@pytest.mark.asyncio
async def test_carousel_creator_done_when_slides_meet_expected_count():
    node = CarouselCreator()
    slides = [
        CarouselSlide(slide_number=1, heading="Slide 1", body_text="Body 1"),
        CarouselSlide(slide_number=2, heading="Slide 2", body_text="Body 2"),
    ]
    content = {
        "topic_a": TopicContent(
            topic_id="topic_a",
            content_format="carousel",
            status=ContentStatus.PENDING,
            carousel_slides=slides,
            rendered_code="<!DOCTYPE html><html></html>",
        )
    }

    result = await node.process(
        {
            "pending_topic_id": "topic_a",
            "content": content,
            "deep_research": {
                "topic_a": {
                    "content_spec": {
                        "slides": [{"heading": "Slide 1"}, {"heading": "Slide 2"}]
                    }
                }
            },
            "carousel_status": "generating_slides",
        },
        context=MagicMock(spec=NodeContext),
    )

    assert result["carousel_status"] == "done"
    assert content["topic_a"].status == ContentStatus.DRAFT


@pytest.mark.asyncio
async def test_carousel_creator_routes_to_generating_code_when_html_missing():
    node = CarouselCreator()
    slides = [
        CarouselSlide(slide_number=1, heading="Slide 1", body_text="Body 1"),
        CarouselSlide(slide_number=2, heading="Slide 2", body_text="Body 2"),
    ]
    content = {
        "topic_a": TopicContent(
            topic_id="topic_a",
            content_format="carousel",
            status=ContentStatus.PENDING,
            carousel_slides=slides,
            rendered_code="",
        )
    }

    result = await node.process(
        {
            "pending_topic_id": "topic_a",
            "content": content,
            "deep_research": {
                "topic_a": {
                    "content_spec": {
                        "slides": [{"heading": "Slide 1"}, {"heading": "Slide 2"}]
                    }
                }
            },
            "carousel_status": "generating_slides",
        },
        context=MagicMock(spec=NodeContext),
    )

    assert result == {"carousel_status": "generating_code"}


@pytest.mark.asyncio
async def test_carousel_creator_breaks_loop_on_status_done_discrepancy():
    node = CarouselCreator()
    # actual_count is 2 (e.g. some slides were filtered out)
    slides = [
        CarouselSlide(slide_number=1, heading="Slide 1", body_text="Body 1"),
        CarouselSlide(slide_number=2, heading="Slide 2", body_text="Body 2"),
    ]
    content = {
        "topic_a": TopicContent(
            topic_id="topic_a",
            content_format="carousel",
            status=ContentStatus.PENDING,
            carousel_slides=slides,
        )
    }

    # required_count is 3, but carousel_status is "done" (set by slide_writer after it ran once)
    result = await node.process(
        {
            "pending_topic_id": "topic_a",
            "content": content,
            "deep_research": {
                "topic_a": {
                    "content_spec": {
                        "slides": [
                            {"heading": "Slide 1"},
                            {"heading": "Slide 2"},
                            {"heading": "Slide 3"},
                        ]
                    }
                }
            },
            "carousel_status": "done",
        },
        context=MagicMock(spec=NodeContext),
    )

    # It should hit the loop guard, force status DRAFT, and return done
    assert result["carousel_status"] == "done"
    assert content["topic_a"].status == ContentStatus.DRAFT
