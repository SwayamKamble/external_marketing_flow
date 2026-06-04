import pytest
from contentforge.nodes.editing.chat_edit_agent import ChatEditAgent
from contentforge.core.state import TopicContent, Theme, CarouselSlide, Caption, Platform

def test_fallback_edit_colors_and_headings():
    agent = ChatEditAgent()
    
    tc = TopicContent(
        topic_id="test_topic",
        content_format="carousel",
        theme=Theme(primary_color="blue", background_color="white"),
        carousel_slides=[
            CarouselSlide(slide_number=1, heading="Old Slide 1 Heading", body_text="Old Slide 1 Body"),
            CarouselSlide(slide_number=2, heading="Old Slide 2 Heading", body_text="Old Slide 2 Body")
        ],
        captions={
            "instagram": {
                "v1": Caption(platform=Platform.INSTAGRAM, variant="v1", caption_text="Old Instagram Caption")
            }
        }
    )
    
    # 1. Test color changes
    changed = agent._fallback_edit("change background color to #ff0000 and primary color to black", tc)
    assert changed is True
    assert tc.theme.background_color == "#ff0000"
    assert tc.theme.primary_color == "black"
    
    # 2. Test slide specific edits
    changed2 = agent._fallback_edit("change slide 2 heading to Hello World", tc)
    assert changed2 is True
    assert tc.carousel_slides[1].heading == "Hello World"
    
    # 3. Test slide body edit
    changed3 = agent._fallback_edit("first slide body: New body description", tc)
    assert changed3 is True
    assert tc.carousel_slides[0].body_text == "New body description"
    
    # 4. Test general heading change (for slide 1)
    changed4 = agent._fallback_edit("heading to General Heading", tc)
    assert changed4 is True
    assert tc.carousel_slides[0].heading == "General Heading"
    
    # 5. Test captions update
    changed5 = agent._fallback_edit("instagram caption: New Instagram content", tc)
    assert changed5 is True
    assert tc.captions["instagram"]["v1"].caption_text == "New Instagram content"


def test_fallback_edit_flexible_patterns():
    agent = ChatEditAgent()
    
    # Test flexible slide-specific headings/bodies (e.g. "heading of slide 2 to Hello")
    tc = TopicContent(
        topic_id="test_topic",
        content_format="carousel",
        carousel_slides=[
            CarouselSlide(slide_number=1, heading="Old 1", body_text="Old 1 Body"),
            CarouselSlide(slide_number=2, heading="Old 2", body_text="Old 2 Body")
        ]
    )
    
    # 1. Order: [heading] of [slide X] to [value]
    changed = agent._fallback_edit("change heading of slide 2 to New Heading 2", tc)
    assert changed is True
    assert tc.carousel_slides[1].heading == "New Heading 2"
    
    # 2. Order: [body] of [slide X] to [value]
    changed2 = agent._fallback_edit("change body of slide 1 to New Body 1", tc)
    assert changed2 is True
    assert tc.carousel_slides[0].body_text == "New Body 1"
    
    # 3. Test colon & space separator: "heading of slide 2: Value"
    changed3 = agent._fallback_edit("heading of slide 2: Even Newer Heading 2", tc)
    assert changed3 is True
    assert tc.carousel_slides[1].heading == "Even Newer Heading 2"

    # Test auto-initialization when empty
    tc_empty = TopicContent(
        topic_id="test_topic_empty",
        content_format="single_image",
        carousel_slides=[],
        captions={}
    )
    
    # 4. General heading change on empty slides list -> should initialize slide 1
    changed_empty_h = agent._fallback_edit("change heading to Initial Heading", tc_empty)
    assert changed_empty_h is True
    assert len(tc_empty.carousel_slides) == 1
    assert tc_empty.carousel_slides[0].heading == "Initial Heading"
    
    # 5. General caption change on empty captions dict -> should initialize and set captions
    changed_empty_c = agent._fallback_edit("caption: Initial Caption", tc_empty)
    assert changed_empty_c is True
    assert "instagram" in tc_empty.captions
    assert tc_empty.captions["instagram"]["v1"].caption_text == "Initial Caption"


def test_fallback_edit_word_slide_numbers_and_slide_noun():
    agent = ChatEditAgent()
    
    tc = TopicContent(
        topic_id="test_topic",
        content_format="carousel",
        carousel_slides=[
            CarouselSlide(slide_number=1, heading="Old 1", body_text="Old 1 Body"),
            CarouselSlide(slide_number=2, heading="Old 2", body_text="Old 2 Body")
        ]
    )
    
    # Test word-based slide numbers
    changed = agent._fallback_edit("change heading of slide two to New Heading 2 via word", tc)
    assert changed is True
    assert tc.carousel_slides[1].heading == "New Heading 2 via word"
    
    # Test ordinal-based slide numbers
    changed2 = agent._fallback_edit("change body of first slide to New Body 1 via ordinal", tc)
    assert changed2 is True
    assert tc.carousel_slides[0].body_text == "New Body 1 via ordinal"
    
    # Test general slide noun targeting (updates slide 1)
    changed3 = agent._fallback_edit("change the heading of this slide to Slide Noun Heading", tc)
    assert changed3 is True
    assert tc.carousel_slides[0].heading == "Slide Noun Heading"
    
    changed4 = agent._fallback_edit("change slide body to Slide Noun Body", tc)
    assert changed4 is True
    assert tc.carousel_slides[0].body_text == "Slide Noun Body"

