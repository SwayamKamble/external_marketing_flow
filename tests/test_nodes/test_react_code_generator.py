import pytest
from unittest.mock import MagicMock
from pathlib import Path

from contentforge.core.state import ContentStatus, TopicContent, CarouselSlide, Theme
from contentforge.nodes._base import NodeContext
from contentforge.nodes.content.carousel.react_code_generator import ReactCodeGenerator


@pytest.mark.asyncio
async def test_react_code_generator_compiles_html_and_writes_to_disk(tmp_path):
    # Setup test node
    node = ReactCodeGenerator()
    
    # Mock node's save_artifact so it doesn't fail
    node.save_artifact = MagicMock()
    
    # Create topic content
    theme = Theme(
        primary_color="#ff0000",
        secondary_color="#00ff00",
        accent_color="#0000ff",
        background_color="#1a1a1a",
        text_color="#ffffff",
        font_heading="Outfit",
        font_body="Inter",
    )
    slides = [
        CarouselSlide(
            slide_number=1,
            heading="Learn AI in 5 Minutes",
            body_text="First, understand what neural networks are. They are patterned after our brains.",
            visual_concept="A brain connection graphic",
            image_description="brain connection",
            image_placement="right",
            slide_theme={"visual_hierarchy": {"highlight_words": ["AI", "brains"]}},
        ),
        CarouselSlide(
            slide_number=2,
            heading="Deep Learning is Key",
            body_text="Next, train the network on high quality data.",
            visual_concept="Training process illustration",
            image_description="training dataset",
            image_placement="left",
        )
    ]
    
    content = {
        "topic_test": TopicContent(
            topic_id="topic_test",
            content_format="carousel",
            status=ContentStatus.PENDING,
            carousel_slides=slides,
            theme=theme,
        )
    }

    result = await node.process(
        {
            "pending_topic_id": "topic_test",
            "week_id": "week_test",
            "content": content,
        },
        context=MagicMock(spec=NodeContext),
    )

    # 1. Assert result status transitions
    assert result["carousel_status"] == "done"
    assert result["pipeline_status"] == "content_creation"
    
    # 2. Check generated code structure
    generated_code = content["topic_test"].rendered_code
    assert generated_code.startswith("<!DOCTYPE html>")
    assert "Outfit" in generated_code
    assert "Inter" in generated_code
    assert "#ff0000" in generated_code
    assert "Learn" in generated_code
    assert "5 Minutes" in generated_code
    assert "remove-btn" in generated_code

    # 3. Assert save_artifact was called
    node.save_artifact.assert_called_once()
