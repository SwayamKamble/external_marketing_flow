"""Node to generate deep research prompts for selected topics.

Optimized: template-based prompt generation without LLM call.
"""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


_PROMPT_TEMPLATE = """You are a research analyst preparing content for a tech-focused social media brand called @tech_by_pravesh.

Research the following topic in depth and return your findings as a JSON object.

## Topic: {title}
**Angle:** {angle}
**Summary:** {summary}
**Content Format:** {content_format}
**Key Points to Investigate:**
{key_points}

## Required Output Format
Return a single JSON object with this exact structure:

```json
{{
  "structured_research": "Full detailed research text with facts, statistics, expert quotes, case studies, and actionable insights...",
  "content_spec": {{
    "theme": {{
      "primary_color": "",
      "secondary_color": "",
      "accent_color": "",
      "background_color": "",
      "text_color": "",

      "font_heading": "",
      "font_body": "",

      "mood": "",

      "visual_design_analysis": {{
        "topic_category": "",
        "content_type": "",
        "best_storytelling_approach": "",
        "recommended_design_style": "",
        "recommended_visual_mood": [],
        "recommended_color_psychology": "",
        "recommended_typography_style": "",
        "recommended_layout_strategy": "",
        "recommended_component_library": [],
        "recommended_image_style": "",
        "recommended_icon_style": "",
        "recommended_data_visualization_style": "",
        "visual_hierarchy_strategy": "",
        "reasoning": ""
      }},

      "theme_discovery": {{
        "theme_name": "",
        "theme_reason": "",
        "design_goal": "",
        "design_philosophy": [],
        "visual_direction": [],
        "brand_feel": [],
        "recommended_slide_flow": []
      }}
    }},
    "slides": [
      {{
        "slide_number": 1,

        "slide_type": "hook",

        "heading": "Attention-grabbing hook title",

        "body_text": "",

        "image_description": "Detailed visual description",

        "image_placement": "background",

        "theme": {{

          "design_goal": "",

          "storytelling_purpose": "",

          "design_style": [],

          "visual_mood": [],

          "layout": {{
            "type": "",
            "headline_position": "",
            "body_position": "",
            "image_position": "",
            "component_positions": {{}}
          }},

          "visual_hierarchy": {{
  "primary_focus": [],
  "secondary_focus": [],
  "dominant_element": "",
  "headline_size": "",
  "headline_weight": "",
  "highlight_words": [],
  "highlight_color": ""
}},

"visual_priority_order": [
  "first thing user notices",
  "second thing user notices",
  "third thing user notices"
],

"theme_reasoning": {{
  "why_this_design_style": "",
  "why_this_layout": "",
  "why_this_visual_hierarchy": "",
  "why_this_component_selection": "",
  "why_this_image_style": ""
}},

"recommended_components": [
  {{
    "component": "",
    "position": "",
    "purpose": "",
    "visual_priority": ""
  }}
],

"image": {{
  "description": "",
  "placement": "",
  "coverage": "",
  "visual_style": "",
  "generation_prompt": ""
}},

"design_constraints": [],

"html_generation_rules": {{
  "preferred_layout_system": "",
  "responsive_behavior": "",
  "animation_style": "",
  "css_recommendations": [],
  "recommended_css_structure": "",
  "preferred_component_hierarchy": []
}}
        }}
      }},

      {{
        "slide_number": 2,

        "slide_type": "content",

        "heading": "Key Point Title",

        "body_text": "Expanded explanation with stats and examples",

        "image_description": "Supporting visual description",

        "image_placement": "right",

        "theme": {{

          "design_goal": "",

          "storytelling_purpose": "",

          "design_style": [],

          "visual_mood": [],

          "layout": {{
            "type": "",
            "headline_position": "",
            "body_position": "",
            "image_position": "",
            "component_positions": {{}}
          }},

          "visual_hierarchy": {{
  "primary_focus": [],
  "secondary_focus": [],
  "dominant_element": "",
  "headline_size": "",
  "headline_weight": "",
  "highlight_words": [],
  "highlight_color": ""
}},

"visual_priority_order": [
  "first thing user notices",
  "second thing user notices",
  "third thing user notices"
],

"theme_reasoning": {{
  "why_this_design_style": "",
  "why_this_layout": "",
  "why_this_visual_hierarchy": "",
  "why_this_component_selection": "",
  "why_this_image_style": "",
  "why_this_color_palette": ""
}},

"recommended_components": [
  {{
    "component": "",
    "position": "",
    "purpose": "",
    "visual_priority": ""
  }}
],

"image": {{
  "description": "",
  "placement": "",
  "coverage": "",
  "visual_style": "",
  "generation_prompt": ""
}},

"design_constraints": [],

"html_generation_rules": {{
  "preferred_layout_system": "",
  "responsive_behavior": "",
  "animation_style": "",
  "css_recommendations": [],
  "recommended_css_structure": "",
  "preferred_component_hierarchy": []
}}
        }}
      }}
    ],
    "reel_script": [
      {{
        "time": "0:00-0:03",
        "visual": "Detailed description of what to show on screen (B-roll, text overlay, graphics)",
        "audio": "Exact words to speak (full narration script, not just topics)"
      }},
      {{
        "time": "0:03-0:08",
        "visual": "Next visual scene description",
        "audio": "Next spoken words"
      }}
    ],
    "caption": {{
      "hook": "Opening hook line that grabs attention",
      "body": "Main caption body with value and insight",
      "cta": "Clear call to action",
      "hashtags": ["relevant", "hashtags", "here"]
    }}
  }}
}}
```

## CRITICAL INSTRUCTIONS:
- Creative Director Process:

  Before generating slide content:

  1. Research the topic.
  2. Determine the topic category.
  3. Determine the optimal storytelling framework.
  4. Determine the optimal visual communication system.
  5. Determine the optimal layout strategy.
  6. Determine the optimal component library.
  7. Determine the optimal image style.
  8. Determine the optimal visual hierarchy.
  9. Generate slide content.

  Do not generate slide content before determining the visual communication system.

  The AI must think like a Creative Director before acting as a Content Writer.
- The pipeline works best when `content_spec.theme` is present and complete. If it is missing, the pipeline will generate a fallback theme so the user can still move forward, but your response should provide the exact topic-specific theme whenever possible.
- `content_spec.theme` is REQUIRED for every topic and must contain real, non-empty values for:
  - `primary_color`
  - `secondary_color`
  - `accent_color`
  - `background_color`
  - `text_color`
  - `font_heading`
  - `font_body`
  For EVERY slide, generate a complete theme object.

The theme object must describe:

- Design goal
- Storytelling purpose
- Visual style
- Layout system
- Visual hierarchy
- Component placement
- Image placement
- Design constraints
- HTML/CSS generation hints

The theme object should be detailed enough that another AI can generate the complete HTML/CSS/JS design for that slide without making any design decisions itself.

The design should emerge naturally from the content and topic.

Different slides may have different layouts, components, and visual styles if that improves communication.
- Use real Google Font family names only. Do not use placeholders like "heading font", "body font", "Google Font", "same as above", or empty strings.
- Use valid hex colors only for all theme colors. Do not use color names like "blue", "dark", or "premium black".
- The theme and font pair must be specific to this topic and visually different from other topics.
- For **{content_format}** format: Make the content optimized for this specific format
- If **{content_format}** is `carousel`, include **6-8 slides** with substantial details per slide.
- If **{content_format}** is `carousel`, Slide 1 must be a **hook-only cover slide**:
  - Keep only a short, high-impact hook headline in `heading`.
  - Keep `body_text` empty, or at most one very short supporting line (no details).
  - Do not include facts, explanation, stats, examples, or context on Slide 1.
  - Start all detailed topic/post content from **Slide 2 onward**.
- If **{content_format}** is `single_image` or `news_post`, include EXACTLY **1 slide** in the `slides` array (since it is a single-card post, any extra slides will be ignored).
- If **{content_format}** is `single_image` or `news_post`, make slide 1 content substantially detailed to fill the card beautifully (never make it a cover-only or hook-only card):
  - `body_text` must be **4-7 complete sentences** containing concrete facts, key statistics, and clear takeaways.
  - Target **80-120 words** in `body_text` for slide 1.
  - Write full, premium prose (no bullet points, no placeholders, no short fragments).
  - Keep sentences self-contained so no awkward wrapping occurs.
  - Assume final card is **4:5 aspect ratio** and reserve lower space for a possible image placeholder; keep text content strong and detailed enough to fill the upper 4:5 card text area naturally.
- Include **6-10 reel_script entries** covering a full 30-60 second video
- The reel_script "audio" field must contain the EXACT words to speak, not just topic descriptions
- The reel_script "visual" field must describe EXACTLY what to show (text overlays, B-roll footage, graphics)
- Font pairing must be intentional and topic-specific:
  - `font_heading` and `font_body` must be different but complementary.
  - Avoid generic repeated pairing like `Inter` + `Inter`.
  - Use visually strong combinations suited to the topic mood (examples: `Space Grotesk` + `DM Sans`, `Outfit` + `Source Sans 3`, `Poppins` + `Lato`, `Sora` + `Inter`).
  - Keep readability high for long body text in 4:5 and 1:1 layouts.
- Theme intelligence:
  - Do NOT use a generic theme.
  - Determine the theme from the topic itself.
  - Determine the best visual storytelling style for the topic.
  - Determine the best layout system.
  - Determine the best component library.
  - Determine the best image style.
  - Determine the best visual hierarchy.
  - Determine the best data visualization style.
  - Different topics should result in different themes.

Examples:

AI Product Launch
→ Product Launch Editorial
→ Benchmark Cards
→ Leaderboards
→ Product Artwork

Finance
→ Bloomberg Dashboard
→ KPI Cards
→ Stock Charts

Startup Story
→ Documentary Timeline
→ Milestones
→ Founder Journey

Programming
→ Developer Terminal
→ Architecture Diagrams
→ Code Blocks

Cybersecurity
→ Security Operations Dashboard
→ Network Maps
→ Threat Visualizations

History
→ Historical Documentary
→ Maps
→ Timelines

Space
→ NASA Editorial
→ Scientific Visualizations

The theme must emerge naturally from the topic.

The goal is to determine the most effective way to visually communicate the topic.
- Theme completeness (must be usable by the renderer):
  - `theme` must include non-empty hex values for `primary_color`, `secondary_color`, `accent_color`, `background_color`, `text_color`.
  - `theme` must include non-empty Google Font names for `font_heading` and `font_body`.
  - Do not leave theme fields blank or generic placeholders.
- Use the color palette that best communicates the topic.

Examples:

Finance
→ Bloomberg-inspired dark dashboards

History
→ Documentary and archival palettes

Space
→ Deep cosmic palettes

AI Product Launch
→ Premium editorial palettes

Healthcare
→ Clean clinical palettes

Sustainability
→ Natural environmental palettes

The color system must emerge naturally from the topic.

Do not force dark themes on every topic.
- Choose **Google Fonts** that match the topic mood (Inter, Outfit, Space Grotesk, etc.)
- Make the first slide HOOK punchy and attention-grabbing (question, bold stat, or provocative statement)
- Ensure carousel slides from Slide 2 onward have non-empty `heading` and non-empty `body_text` with real, specific facts.
- Never output placeholder or fallback text like "Content generation fallback" or "Re-run deep research".
- Include real statistics, data points, and expert insights in the content
- The JSON must be valid and parseable

- Image Generation Quality:

  Every image prompt must be detailed enough for:

  - GPT Image
  - Midjourney
  - Flux
  - Ideogram
  - Stable Diffusion

  Include:

  - Main subject
  - Composition
  - Camera angle
  - Perspective
  - Lighting
  - Mood
  - Color palette
  - Background details
  - Visual focus
  - Rendering style
  - Editorial direction

  Do not generate short image descriptions.
"""



class DeepResearchPromptGenerator(BaseNode):
    """Generates specific deep-dive prompts for selected topics.

    OPTIMIZED: Uses a template instead of an LLM call to generate the
    prompt. The prompt template includes instructions for the external
    LLM (ChatGPT/Perplexity) to return structured JSON with theme,
    slides, reel_script, and caption data.
    """

    node_name = "deep_research_prompt_generator"
    category = "research"
    description = "Generates targeted deep-research prompts for selected topics."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        selected_topics_ids = input_data.get("selected_topics", [])
        topic_bank = input_data.get("topic_bank", [])

        if not selected_topics_ids:
            if context.logger:
                context.logger.error(self.node_name, "selected_topics is empty â€” skipping to content_creation.")
            return {
                "pipeline_status": "content_creation",
                "human_action_required": False,
            }

        if not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "topic_bank missing.")
            return {"pipeline_status": "deep_research"}

        selected_topics = [t for t in topic_bank if _topic_get(t, "id") in selected_topics_ids]

        if not selected_topics:
            if context.logger:
                context.logger.error(self.node_name, "No topics matched the selected IDs.")
            return {"pipeline_status": "deep_research"}

        deep_research = input_data.get("deep_research", {})
        existing_queue = input_data.get("topic_queue", [])
        pending_topic_id = input_data.get("pending_topic_id")
        remaining_topics = [tid for tid in selected_topics_ids if tid not in deep_research]

        queue = [tid for tid in existing_queue if tid in remaining_topics] or remaining_topics
        if not queue:
            return {
                "pipeline_status": "content_creation",
                "human_action_required": False,
                "human_action_type": None,
            }

        if pending_topic_id not in queue:
            pending_topic_id = queue[0]

        selected_topic = next((t for t in selected_topics if _topic_get(t, "id") == pending_topic_id), None)
        if not selected_topic:
            return {
                "pipeline_status": "deep_research",
                "topic_queue": queue,
                "pending_topic_id": queue[0],
            }

        # Determine content format from the weekly plan
        weekly_plan = input_data.get("weekly_plan", [])
        plan_item = next((p for p in weekly_plan if (p.topic_id if hasattr(p, 'topic_id') else p.get('topic_id')) == pending_topic_id), None)
        content_format = "carousel"
        if plan_item:
            fmt_val = plan_item.content_format if hasattr(plan_item, 'content_format') else plan_item.get('content_format')
            content_format = fmt_val.value if hasattr(fmt_val, 'value') else str(fmt_val)

        # Generate prompt from template (NO LLM call)
        title = _topic_get(selected_topic, "title", "Unknown Topic")
        angle = _topic_get(selected_topic, "suggested_angle", "General analysis")
        summary = _topic_get(selected_topic, "summary", "")
        key_points = _topic_get(selected_topic, "key_points", [])
        kp_text = "\n".join(f"- {kp}" for kp in key_points) if key_points else "- General deep analysis needed"

        prompt_text = _PROMPT_TEMPLATE.format(
            title=title,
            angle=angle,
            summary=summary,
            key_points=kp_text,
            content_format=content_format,
        )

        if context.logger:
            context.logger.event("deep_research_prompt.template", {
                "topic_id": pending_topic_id,
                "title": title,
                "format": content_format,
            })

        # Save artifact
        content = "# Deep Research Request\n\n"
        content += "Copy this prompt into ChatGPT or Perplexity and paste the result back.\n\n"
        content += f"## Topic: {title}\n"
        content += f"**ID:** `{pending_topic_id}` | **Format:** `{content_format}`\n\n"
        content += f"```text\n{prompt_text}\n```\n\n"

        self.save_artifact(
            context=context,
            phase="04_deep_research",
            filename=f"deep_research_prompt_{pending_topic_id}.md",
            content=content,
        )

        return {
            "topic_queue": queue,
            "pending_topic_id": pending_topic_id,
            "topic_index": (selected_topics_ids.index(pending_topic_id) + 1) if pending_topic_id in selected_topics_ids else 0,
            "topic_total": len(selected_topics_ids),
            "pipeline_status": "deep_research",
            "human_action_required": True,
            "human_action_type": "paste_deep_research",
            "prompt_content": prompt_text,
        }