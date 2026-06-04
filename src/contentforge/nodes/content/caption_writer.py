"""Node to write platform-specific captions with the Fan-Out pattern."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from contentforge.core.state import Caption, Platform, ContentStatus, enum_value
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
            ctx_lines.append(f"Format: {enum_value(tc.content_format)}")
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

            if not tc.captions[p.value]:
                title_val = ctx_lines[0].replace('Title: ', '')
                # Define platform specific fallback variants
                fallbacks = []
                if p == Platform.INSTAGRAM:
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v1",
                        caption_text=f"Ever wondered about the real story behind {title_val}? Let's break down what's actually happening under the hood and why it matters.",
                        cta="What's your take on this? Let me know in the comments! 👇",
                        hashtags=["#AI", "#Tech", "#Innovation", "#ArtificialIntelligence", "#MachineLearning", "#TechNews", "#FutureOfTech", "#AITrends", "#TechCommunity", "#SoftwareEngineering"],
                    ))
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v2",
                        caption_text=f"Here is everything you need to know about {title_val}. We cover the quick context, key implications, and your main takeaway.",
                        cta="Save this post for later so you don't forget! 📌",
                        hashtags=["#AI", "#Tech", "#Innovation", "#ArtificialIntelligence", "#MachineLearning", "#TechNews", "#FutureOfTech", "#AITrends", "#TechCommunity", "#SoftwareEngineering"],
                    ))
                elif p == Platform.LINKEDIN:
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v1",
                        caption_text=f"The release of {title_val} marks a significant shift in the landscape. Here is my perspective on how this changes the equation for builders and leaders.",
                        cta="How is your team preparing for this? Let's discuss in the comments.",
                        hashtags=["#AI", "#Technology", "#Innovation", "#Business", "#FutureOfWork"],
                    ))
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v2",
                        caption_text=f"{title_val} is here. Here are the key takeaways you need to know to stay ahead of the curve and adapt your workflow.",
                        cta="Follow for more industry analysis and updates.",
                        hashtags=["#AI", "#TechInnovation", "#FutureOfWork", "#Productivity"],
                    ))
                elif p == Platform.X:
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v1",
                        caption_text=f"Just looked into {title_val}. Here's the narrative that most people are missing, and why it matters for developers and builders.",
                        cta="What do you think? 👇",
                        hashtags=["#AI", "#Tech"],
                    ))
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v2",
                        caption_text=f"Quick breakdown of {title_val}: Context, implications, and what to expect next.",
                        cta="Follow for more quick tech updates.",
                        hashtags=["#AI"],
                    ))
                else:  # Threads / other
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v1",
                        caption_text=f"Alright, let's talk about {title_val}. Here's a casual breakdown of what it actually means for us day-to-day.",
                        cta="Let me know if you agree! Drop a reply.",
                        hashtags=["#AI"],
                    ))
                    fallbacks.append(Caption(
                        platform=p,
                        variant="v2",
                        caption_text=f"{title_val} just dropped. Here's a quick, no-nonsense look at why this is a big deal.",
                        cta="Drop a reply with your thoughts.",
                        hashtags=["#AI"],
                    ))
                
                for fallback in fallbacks:
                    tc.captions[p.value][fallback.variant] = fallback
                    md_content += f"## {p.value.upper()} — Variant: {fallback.variant}\n"
                    md_content += f"{fallback.caption_text}\n\n"
                    if fallback.cta:
                        md_content += f"**CTA:** {fallback.cta}\n\n"
                    if fallback.hashtags:
                        md_content += f"**Hashtags:** {' '.join(fallback.hashtags)}\n\n"
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
