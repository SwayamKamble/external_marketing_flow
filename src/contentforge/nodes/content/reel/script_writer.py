"""Script writing node for short-form video."""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


def _topic_get(topic: Any, key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


class ScriptWriter(BaseNode):
    """Generates a complete 30-60 second video script.
    
    Includes visual B-roll cues, on-screen text (hooks), and
    the spoken dialogue based on deep research.
    """

    node_name = "script_writer"
    category = "content"
    description = "Writes a full A-V script for short-form video content."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        tc = content_dict.get(topic_id)
        if not tc or tc.content_format.value != "reel":
            return {}

        topic_bank = input_data.get("topic_bank", [])
        topic = next((t for t in topic_bank if _topic_get(t, "id") == topic_id), None)
        deep_res = input_data.get("deep_research", {}).get(topic_id)

        system_prompt, config = self.load_prompt(context)
        
        ctx = f"Title: {_topic_get(topic, 'title', '') if topic else ''}\nAngle: {_topic_get(topic, 'suggested_angle', '') if topic else ''}\n"
        if deep_res:
            ctx += f"\nFacts:\n{deep_res.result}"

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Write the reel script for:\n\n{ctx}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.7),
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                script = parsed.get("script", [])
                
                # We'll just store the script array directly on the state 
                tc.video_script = script
                
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
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Script parsing failed: {e}")

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        return {
            "content": updated_content,
            "pipeline_status": "editing" # Done with content creation
        }
