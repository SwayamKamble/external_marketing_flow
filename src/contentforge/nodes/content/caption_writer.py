"""Node to write platform-specific captions with the Fan-Out pattern."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from contentforge.core.state import Caption, Platform, ContentStatus
from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


class CaptionWriter(BaseNode):
    """Generates captions across all platforms in parallel.

    Uses a fan-out pattern to concurrently generate captions for Instagram,
    LinkedIn, X, and Threads. It requests 2 variants (e.g. story vs. logic)
    per platform.
    """

    node_name = "caption_writer"
    category = "content"
    description = "Writes captions with variants for all target platforms in parallel."

    async def _write_for_platform(
        self, platform: Platform, topic_context: str, context: NodeContext
    ) -> list[Caption]:
        system_prompt, config = self.load_prompt(
            context,
            extra_variables={"target_platform": platform.value}
        )

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Please write the 2 caption variants for {platform.value}.\nTopic Context:\n{topic_context}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.7),
        )

        if not result.success:
            if context.logger:
                context.logger.error(self.node_name, f"Caption generation failed for {platform.value}: {result.error}")
            return []

        try:
            parsed = json.loads(result.content)
            variants_data = parsed.get("variants", [])
            
            captions = []
            for v in variants_data:
                captions.append(Caption(
                    platform=platform,
                    variant=v.get("variant", "v1"),
                    caption_text=v.get("caption_text", ""),
                    hashtags=v.get("hashtags", []),
                    cta=v.get("cta", ""),
                    char_count=len(v.get("caption_text", ""))
                ))
            return captions
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"Failed parsing JSON for {platform.value}: {e}")
            return []

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        if not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]
        
        # Build strict context string for the prompts
        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if _topic_get(t, "id") == topic_id), None)
        
        deep_res = input_data.get("deep_research", {}).get(topic_id)
        
        ctx_lines = [f"Title: {_topic_get(topic, 'title', 'Unknown')}" if topic else "Title: Unknown"]
        if topic:
            ctx_lines.append(f"Format: {tc.content_format.value}")
            ctx_lines.append(f"Angle: {_topic_get(topic, 'suggested_angle', '')}")
        if deep_res:
            ctx_lines.append(f"Facts/Details:\n{deep_res.result}")
            
        context_str = "\n".join(ctx_lines)

        # Fan-out execution (all platforms concurrently)
        platforms_to_write = [Platform.INSTAGRAM, Platform.LINKEDIN, Platform.X, Platform.THREADS]
        
        tasks = [
            self._write_for_platform(p, context_str, context)
            for p in platforms_to_write
        ]
        
        # Fan-in
        results = await asyncio.gather(*tasks)
        
        # Merge back into the TopicContent state object
        tc.captions = {}
        md_content = f"# Captions for Topic {topic_id}\n\n"
        
        for p, captions in zip(platforms_to_write, results):
            tc.captions[p.value] = {}
            for cap in captions:
                tc.captions[p.value][cap.variant] = cap
                
                md_content += f"## {p.value.upper()} — Variant: {cap.variant}\n"
                md_content += f"{cap.caption_text}\n\n"
                if cap.cta:
                    md_content += f"**CTA:** {cap.cta}\n\n"
                if cap.hashtags:
                    md_content += f"**Hashtags:** {' '.join(cap.hashtags)}\n\n"
                md_content += "---\n\n"

        # Save artifact for human review
        self.save_artifact(
            context=context,
            phase="05_content",
            topic_id=topic_id,
            filename="captions.md",
            content=md_content,
        )

        tc.status = ContentStatus.DRAFT

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc

        return {"content": updated_content}
