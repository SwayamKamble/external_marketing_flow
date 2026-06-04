"""Agentic chat node for editing content based on feedback."""

from __future__ import annotations

import json
import re
from typing import Any

from contentforge.core.state import ContentStatus, Caption, Theme, CarouselSlide, Platform
from contentforge.nodes._base import BaseNode, NodeContext


class ChatEditAgent(BaseNode):
    """Processes natural language human feedback.
    
    If a human says "make the CTA more urgent and shorten the hook",
    this agent parses the request and updates the specific content artifacts.
    """

    node_name = "chat_edit_agent"
    category = "editing"
    description = "Applies natural language feedback to content."

    def _fallback_edit(self, feedback: str, tc: Any) -> bool:
        """Applies fallback rule-based edits to TopicContent based on natural language feedback.
        
        Returns True if any changes were made.
        """
        feedback_lower = feedback.lower()
        changes_made = False
        
        # ── Color / Theme parsing ──
        color_names = [
            "red", "blue", "green", "yellow", "black", "white", "purple", "orange", "pink", 
            "grey", "gray", "cyan", "magenta", "navy", "teal", "maroon", "olive", "lime", 
            "indigo", "violet", "brown", "dark blue", "light blue", "gold", "silver"
        ]
        
        def find_color(text: str) -> str | None:
            hex_match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}\b', text)
            if hex_match:
                return hex_match.group(0)
            rgb_match = re.search(r'rgba?\(.*?\)', text)
            if rgb_match:
                return rgb_match.group(0)
            for c in color_names:
                if c in text:
                    return c
            return None

        color_matches = re.finditer(
            r'(primary|secondary|accent|background|bg|text|foreground)\s+(?:color\s+)?(?:to|is|:|=|\s)+\s*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|[a-zA-Z\s]+)',
            feedback_lower
        )
        
        for m in color_matches:
            field = m.group(1)
            raw_val = m.group(2).strip()
            val = find_color(raw_val) or raw_val
            
            if field in ("background", "bg"):
                tc.theme.background_color = val
                changes_made = True
            elif field == "primary":
                tc.theme.primary_color = val
                changes_made = True
            elif field == "secondary":
                tc.theme.secondary_color = val
                changes_made = True
            elif field == "accent":
                tc.theme.accent_color = val
                changes_made = True
            elif field in ("text", "foreground"):
                tc.theme.text_color = val
                changes_made = True

        # Check for theme font overrides
        font_matches = re.finditer(
            r'(heading|title|header|body|text)\s+font\s+(?:to|is|:|=|\s)+\s*([a-zA-Z0-9\s\-]+)',
            feedback_lower
        )
        for m in font_matches:
            field = m.group(1)
            val = m.group(2).strip().title()
            if field in ("heading", "title", "header"):
                tc.theme.font_heading = val
                changes_made = True
            elif field in ("body", "text"):
                tc.theme.font_body = val
                changes_made = True

        # ── Slide content parsing ──
        slide_words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        slide_ordinals = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10}
        
        slide_num = None
        slide_match = re.search(r'slide\s*(\d+)', feedback_lower)
        if slide_match:
            slide_num = int(slide_match.group(1))
        else:
            for word, num in slide_words.items():
                if f"slide {word}" in feedback_lower:
                    slide_num = num
                    break
            if not slide_num:
                for word, num in slide_ordinals.items():
                    if f"{word} slide" in feedback_lower:
                        slide_num = num
                        break

        # Check for slide specific heading/title/body text changes first
        # E.g. "change heading of slide 1 to Hello" or "change slide 1 heading to Hello"
        if slide_num is not None and tc.carousel_slides:
            slide = next((s for s in tc.carousel_slides if s.slide_number == slide_num), None)
            if not slide and 0 <= slide_num - 1 < len(tc.carousel_slides):
                slide = tc.carousel_slides[slide_num - 1]
                
            if slide:
                heading_patterns = [
                    r'(?:change\s+)?(?:the\s+)?(?:heading|title|header)\s+(?:of|for)\s+(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s*(?:to|is|:|=)\s*(.+)$',
                    r'(?:change\s+)?(?:the\s+)?(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s+(?:heading|title|header)\s*(?:to|is|:|=)\s*(.+)$',
                ]
                for pat in heading_patterns:
                    m = re.search(pat, feedback, re.IGNORECASE)
                    if m:
                        slide.heading = m.group(1).strip().strip('"').strip("'")
                        changes_made = True
                        break
                
                body_patterns = [
                    r'(?:change\s+)?(?:the\s+)?(?:body\s+text|body|text|content)\s+(?:of|for)\s+(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s*(?:to|is|:|=)\s*(.+)$',
                    r'(?:change\s+)?(?:the\s+)?(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s+(?:body\s+text|body|text|content)\s*(?:to|is|:|=)\s*(.+)$',
                ]
                for pat in body_patterns:
                    m = re.search(pat, feedback, re.IGNORECASE)
                    if m:
                        slide.body_text = m.group(1).strip().strip('"').strip("'")
                        changes_made = True
                        break

                font_patterns = [
                    r'(?:change\s+)?font\s+(?:of|for)\s+(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s*(?:to|is|:|=)\s*([a-zA-Z0-9\s\-]+)',
                    r'(?:change\s+)?(?:slide\s*(?:\d+|[a-zA-Z]+)|[a-zA-Z]+\s+slide)\s+font\s*(?:to|is|:|=)\s*([a-zA-Z0-9\s\-]+)',
                ]
                for pat in font_patterns:
                    m = re.search(pat, feedback_lower)
                    if m:
                        f_name = m.group(1).strip().title()
                        slide.heading_font = f_name
                        slide.body_font = f_name
                        changes_made = True
                        break

        # ── Non-slide-specific heading/title/body change ──
        # (This also acts as fallback if slide_num was not found, OR we update slide 1 as default)
        if not changes_made:
            # General heading change
            general_heading_patterns = [
                r'(?:change\s+)?(?:the\s+)?(?:heading|title|header)\s+(?:of|for)\s+(?:the\s+|this\s+)?(?:topic|post|image|content|slide)\s*(?:to|is|:|=)\s*(.+)$',
                r'(?:change\s+)?(?:the\s+)?(?:topic|post|image|content|slide)\s+(?:heading|title|header)\s*(?:to|is|:|=)\s*(.+)$',
                r'(?:change\s+)?(?:the\s+)?(?:heading|title|header)\s*(?:to|is|:|=)\s*(.+)$',
            ]
            for pat in general_heading_patterns:
                m = re.search(pat, feedback, re.IGNORECASE)
                if m:
                    new_val = m.group(1).strip().strip('"').strip("'")
                    if not tc.carousel_slides:
                        tc.carousel_slides = [CarouselSlide(slide_number=1, heading="", body_text="")]
                    tc.carousel_slides[0].heading = new_val
                    changes_made = True
                    break
            
            # General body change
            general_body_patterns = [
                r'(?:change\s+)?(?:the\s+)?(?:body|content|body\s+text)\s+(?:of|for)\s+(?:the\s+|this\s+)?(?:topic|post|image|content|slide)\s*(?:to|is|:|=)\s*(.+)$',
                r'(?:change\s+)?(?:the\s+)?(?:topic|post|image|content|slide)\s+(?:body|content|body\s+text)\s*(?:to|is|:|=)\s*(.+)$',
                r'(?:change\s+)?(?:the\s+)?(?:body|content|body\s+text)\s*(?:to|is|:|=)\s*(.+)$',
            ]
            for pat in general_body_patterns:
                m = re.search(pat, feedback, re.IGNORECASE)
                if m:
                    new_val = m.group(1).strip().strip('"').strip("'")
                    if not tc.carousel_slides:
                        tc.carousel_slides = [CarouselSlide(slide_number=1, heading="", body_text="")]
                    tc.carousel_slides[0].body_text = new_val
                    changes_made = True
                    break

        # ── Caption parsing ──
        if "caption" in feedback_lower:
            platform_key = None
            for p in ["instagram", "linkedin", "x", "threads"]:
                if p in feedback_lower:
                    platform_key = p
                    break
            
            caption_match = re.search(r'(?:caption)\s*(?:to|is|:|=)\s*(.+)$', feedback, re.IGNORECASE)
            if caption_match:
                new_caption = caption_match.group(1).strip().strip('"').strip("'")
                if not tc.captions:
                    tc.captions = {
                        "instagram": {"v1": Caption(platform=Platform.INSTAGRAM, variant="v1", caption_text="")},
                        "linkedin": {"v1": Caption(platform=Platform.LINKEDIN, variant="v1", caption_text="")},
                        "x": {"v1": Caption(platform=Platform.X, variant="v1", caption_text="")},
                        "threads": {"v1": Caption(platform=Platform.THREADS, variant="v1", caption_text="")}
                    }
                platforms = [platform_key] if platform_key else list(tc.captions.keys())
                for pk in platforms:
                    if pk in tc.captions:
                        for variant_key in tc.captions[pk].keys():
                            tc.captions[pk][variant_key].caption_text = new_caption
                            tc.captions[pk][variant_key].char_count = len(new_caption)
                            changes_made = True

        return changes_made

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        feedback = input_data.get("human_feedback", "")
        
        if not feedback or not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]

        # ── Try Smart LLM Editor First ──
        system_prompt, config = self.load_prompt(context)
        
        # Serialize current content state for the LLM
        current_state = {
            "captions": tc.captions,
            "theme": tc.theme.model_dump() if tc.theme else None,
            "carousel_slides": [s.model_dump() for s in (tc.carousel_slides or [])],
            "video_script": tc.video_script,
            "image_prompts": tc.image_prompts
        }

        user_message = f"Feedback: {feedback}\n\nCurrent Content:\n{json.dumps(current_state, default=str)}"

        if context.logger:
            context.logger.event("chat_edit_agent.attempt_llm", {
                "topic_id": topic_id,
                "feedback": feedback
            })

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=user_message,
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=0.3, # Keep variations controlled
        )

        llm_success = False
        if result.success:
            try:
                parsed = json.loads(result.content)
                
                # Apply diffs back to state based on LLM response
                # 1. Merge and update captions
                if "captions" in parsed and isinstance(parsed["captions"], dict):
                    for platform_name, variants in parsed["captions"].items():
                        if not isinstance(variants, dict):
                            continue
                        if platform_name not in tc.captions:
                            tc.captions[platform_name] = {}
                        for variant_name, cap_data in variants.items():
                            if not isinstance(cap_data, dict):
                                continue
                            existing_cap = tc.captions[platform_name].get(variant_name)
                            tc.captions[platform_name][variant_name] = Caption(
                                platform=Platform(cap_data.get("platform", existing_cap.platform if existing_cap else platform_name)),
                                variant=cap_data.get("variant", existing_cap.variant if existing_cap else variant_name),
                                caption_text=cap_data.get("caption_text", existing_cap.caption_text if existing_cap else ""),
                                hashtags=cap_data.get("hashtags", existing_cap.hashtags if existing_cap else []),
                                cta=cap_data.get("cta", existing_cap.cta if existing_cap else ""),
                                char_count=len(cap_data.get("caption_text", ""))
                            )

                # 2. Merge and update theme
                if "theme" in parsed:
                    theme_data = parsed["theme"]
                    if theme_data and isinstance(theme_data, dict):
                        tc.theme = Theme(
                            primary_color=theme_data.get("primary_color", tc.theme.primary_color if tc.theme else ""),
                            secondary_color=theme_data.get("secondary_color", tc.theme.secondary_color if tc.theme else ""),
                            accent_color=theme_data.get("accent_color", tc.theme.accent_color if tc.theme else ""),
                            background_color=theme_data.get("background_color", tc.theme.background_color if tc.theme else ""),
                            text_color=theme_data.get("text_color", tc.theme.text_color if tc.theme else ""),
                            font_heading=theme_data.get("font_heading", tc.theme.font_heading if tc.theme else ""),
                            font_body=theme_data.get("font_body", tc.theme.font_body if tc.theme else ""),
                            style_notes=theme_data.get("style_notes", tc.theme.style_notes if tc.theme else ""),
                            mood=theme_data.get("mood", tc.theme.mood if tc.theme else "")
                        )

                # 3. Merge and update carousel slides
                if "carousel_slides" in parsed:
                    slides_list = parsed["carousel_slides"]
                    if isinstance(slides_list, list):
                        new_slides = []
                        for idx, s in enumerate(slides_list):
                            existing_slide = None
                            if tc.carousel_slides and idx < len(tc.carousel_slides):
                                existing_slide = tc.carousel_slides[idx]
                            new_slides.append(CarouselSlide(
                                slide_number=s.get("slide_number", existing_slide.slide_number if existing_slide else idx + 1),
                                slide_type=s.get("slide_type", existing_slide.slide_type if existing_slide else ""),
                                heading=s.get("heading", existing_slide.heading if existing_slide else ""),
                                body_text=s.get("body_text", existing_slide.body_text if existing_slide else ""),
                                visual_concept=s.get("visual_concept", existing_slide.visual_concept if existing_slide else ""),
                                image_description=s.get("image_description", existing_slide.image_description if existing_slide else ""),
                                image_placement=s.get("image_placement", existing_slide.image_placement if existing_slide else ""),
                                heading_font=s.get("heading_font", existing_slide.heading_font if existing_slide else ""),
                                heading_font_weight=s.get("heading_font_weight", existing_slide.heading_font_weight if existing_slide else ""),
                                body_font=s.get("body_font", existing_slide.body_font if existing_slide else ""),
                                body_font_weight=s.get("body_font_weight", existing_slide.body_font_weight if existing_slide else "")
                            ))
                        tc.carousel_slides = new_slides

                # 4. Merge and update video script
                if "video_script" in parsed:
                    video_script_list = parsed["video_script"]
                    if isinstance(video_script_list, list):
                        tc.video_script = video_script_list

                # 5. Merge and update image prompts
                if "image_prompts" in parsed:
                    image_prompts_list = parsed["image_prompts"]
                    if isinstance(image_prompts_list, list):
                        tc.image_prompts = image_prompts_list 

                self.save_artifact(
                   context=context,
                   phase="06_editing",
                   topic_id=topic_id,
                   filename="edit_diff.md",
                   content=f"# Edits Applied (Smart LLM Editor)\n\nFeedback: {feedback}\n\nUpdates made successfully."
                )
                llm_success = True
                
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Edit parse failed: {e}")

        # ── Fallback to Local Rule-Based Parser on Failure ──
        if not llm_success:
            if context.logger:
                context.logger.event("chat_edit_agent.llm_failed", {
                    "topic_id": topic_id,
                    "feedback": feedback,
                    "reason": "LLM call failed or returned invalid JSON. Falling back to local rule-based parser."
                })
            
            if self._fallback_edit(feedback, tc):
                self.save_artifact(
                   context=context,
                   phase="06_editing",
                   topic_id=topic_id,
                   filename="edit_diff.md",
                   content=f"# Edits Applied (Local Fallback Parser)\n\nFeedback: {feedback}\n\nApplied offline regex fallback rules successfully."
                )
            else:
                self.save_artifact(
                   context=context,
                   phase="06_editing",
                   topic_id=topic_id,
                   filename="edit_diff.md",
                   content=f"# No Edits Applied\n\nFeedback: {feedback}\n\nLLM failed and offline regex rules did not match."
                )

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        # Clear feedback so it doesn't loop
        return {
            "content": updated_content,
            "human_feedback": "", 
            "pipeline_status": "review" # Go back to edit router to request approval again
        }
