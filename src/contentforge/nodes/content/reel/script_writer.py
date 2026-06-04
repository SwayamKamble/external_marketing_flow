"""Script writing node for short-form video.

OPTIMIZED: Generates reel script from deep research content using a
deterministic template. Falls back to a compact LLM call only if no
deep research is available. This eliminates the 30-60s LLM wait.
"""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext
from contentforge.core.state import enum_value


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


def _generate_script_from_research(topic: Any, deep_res: Any) -> list[dict[str, str]]:
    """Build a deterministic reel script from deep research content.
    
    Creates a 30-60 second script with proper timestamps,
    visual descriptions, and exact spoken dialogue.
    """
    title = _topic_get(topic, "title", "Topic") if topic else "Topic"
    angle = _topic_get(topic, "suggested_angle", "") if topic else ""
    key_points = _topic_get(topic, "key_points", []) if topic else []
    
    # Extract research text
    research_text = ""
    if deep_res:
        if hasattr(deep_res, "result"):
            research_text = deep_res.result or ""
        elif isinstance(deep_res, dict):
            research_text = deep_res.get("result", "")
    
    # Extract key facts from research (split into sentences)
    facts = []
    if research_text:
        sentences = [s.strip() for s in research_text.replace("\n", ". ").split(".") if len(s.strip()) > 20]
        facts = sentences[:8]  # Top 8 facts
    
    # Use key_points as fallback
    if not facts and key_points:
        facts = key_points[:6]
    
    if not facts:
        facts = [f"Key insight about {title}", f"Why {title} matters", f"The impact of {title}"]
    
    # Build script scenes
    script = []
    
    # Scene 1: Hook (0-3s)
    script.append({
        "time": "0:00 - 0:03",
        "visual": f"Bold text overlay on dark background: '{title}' with glitch/zoom effect. Dramatic music starts.",
        "audio": f"Did you know about {title}? Here's what you need to know."
    })
    
    # Scene 2: Context (3-8s)
    script.append({
        "time": "0:03 - 0:08",
        "visual": f"Animated infographic or B-roll footage related to {title}. Text overlay showing the angle: '{angle}'.",
        "audio": facts[0] if facts else f"Let me break down {title} for you."
    })
    
    # Middle scenes: Key points (8-25s)
    mid_facts = facts[1:5] if len(facts) > 1 else [f"Important aspect of {title}"]
    time_marks = ["0:08 - 0:13", "0:13 - 0:18", "0:18 - 0:23", "0:23 - 0:28"]
    visuals = [
        "Split-screen comparison or data chart animation. Key stat highlighted in accent color.",
        "Screen recording or product demo footage. Arrow annotations pointing to key features.",
        "Expert quote card or testimonial overlay. Subtle zoom on text.",
        "Before/after comparison or timeline animation showing progression.",
    ]
    
    for i, fact in enumerate(mid_facts):
        if i >= len(time_marks):
            break
        script.append({
            "time": time_marks[i],
            "visual": visuals[i % len(visuals)],
            "audio": fact
        })
    
    # Scene: Takeaway (25-28s)
    takeaway = facts[5] if len(facts) > 5 else f"The key takeaway about {title} is that it's changing everything."
    script.append({
        "time": "0:28 - 0:33",
        "visual": "Summary card with 3 bullet points. Each bullet animates in. Background shifts to brand colors.",
        "audio": takeaway
    })
    
    # Scene: CTA (33-38s)
    script.append({
        "time": "0:33 - 0:38",
        "visual": "End card: '@tech_by_pravesh' logo centered. 'Follow for more' text animates in. Like + Save icons pulse.",
        "audio": "Follow @tech_by_pravesh for more insights like this. Save this reel!"
    })
    
    return script


class ScriptWriter(BaseNode):
    """Generates a complete 30-60 second video script.
    
    OPTIMIZED: Uses deterministic template generation from deep research
    content instead of LLM. Falls back to LLM only if no deep research.
    """

    node_name = "script_writer"
    category = "content"
    description = "Writes a full A-V script for short-form video content."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        tc = content_dict.get(topic_id)
        if not tc or enum_value(tc.content_format) != "reel":
            return {}

        # FAST PATH 1: video_script already exists from deep research parser
        if tc.video_script and len(tc.video_script) > 0:
            if context.logger:
                context.logger.event("script_writer.skip", {
                    "topic_id": topic_id,
                    "existing_scenes": len(tc.video_script),
                    "reason": "pre-populated from deep_research",
                })
            from contentforge.core.state import ContentStatus
            tc.status = ContentStatus.DRAFT
            updated_content = dict(content_dict)
            updated_content[topic_id] = tc
            return {"content": updated_content, "pipeline_status": "content_creation"}

        # FAST PATH 2: Generate from deep research content (no LLM call)
        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if _topic_get(t, "id") == topic_id), None)
        deep_res = input_data.get("deep_research", {}).get(topic_id)
        
        if topic or deep_res:
            script = _generate_script_from_research(topic, deep_res)
            tc.video_script = script
            
            if context.logger:
                context.logger.event("script_writer.template", {
                    "topic_id": topic_id,
                    "scenes": len(script),
                    "reason": "deterministic template from research",
                })
            
            # Save artifact
            content = "# Video Script\n\n| Time | Visual / B-Roll | Spoken Audio |\n|---|---|---|\n"
            for s in script:
                content += f"| {s.get('time', '0:00')} | {s.get('visual', '')} | {s.get('audio', '')} |\n"
            
            self.save_artifact(
                context=context,
                phase="05_content",
                topic_id=topic_id,
                filename="reel_script.md",
                content=content
            )
            
            from contentforge.core.state import ContentStatus
            tc.status = ContentStatus.DRAFT
            updated_content = dict(content_dict)
            updated_content[topic_id] = tc
            return {"content": updated_content, "pipeline_status": "content_creation"}

        # SLOW FALLBACK: LLM call (only if no topic/research data at all)
        if context.logger:
            context.logger.event("script_writer.llm_fallback", {"topic_id": topic_id})
        
        system_prompt, config = self.load_prompt(context)
        
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Write a 30-second reel script for topic: {topic_id}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.7),
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                script = parsed.get("script", parsed.get("reel_script", []))
                tc.video_script = script
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Script parsing failed: {e}")

        from contentforge.core.state import ContentStatus
        tc.status = ContentStatus.DRAFT
        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        return {"content": updated_content, "pipeline_status": "content_creation"}
