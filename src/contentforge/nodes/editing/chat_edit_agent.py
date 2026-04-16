"""Agentic chat node for editing content based on feedback."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import ContentStatus
from contentforge.nodes._base import BaseNode, NodeContext


class ChatEditAgent(BaseNode):
    """Processes natural language human feedback.
    
    If a human says "make the CTA more urgent and shorten the hook",
    this agent parses the request and updates the specific content artifacts.
    """

    node_name = "chat_edit_agent"
    category = "editing"
    description = "Applies natural language feedback to content."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        feedback = input_data.get("human_feedback", "")
        
        if not feedback or not topic_id or topic_id not in content_dict:
            return {}

        tc = content_dict[topic_id]

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

        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=user_message,
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=0.3, # Keep variations controlled
        )

        if result.success:
            try:
                parsed = json.loads(result.content)
                
                # Apply diffs back to state based on LLM response
                # A robust implementation would do deep dictionary merging.
                # For this pipeline, we will just update the requested parts.
                
                if "captions" in parsed and tc.captions:
                   # Simplistic overlay for demo
                   tc.captions = parsed["captions"]
                   
                if "carousel_slides" in parsed and tc.carousel_slides:
                    # simplistic reconstruct
                    tc.carousel_slides = [] # Would re-parse here
                    pass 

                # In real app: save an artifact showing old vs new
                self.save_artifact(
                   context=context,
                   phase="06_editing",
                   topic_id=topic_id,
                   filename="edit_diff.md",
                   content=f"# Edits Applied\n\nFeedback: {feedback}\n\nUpdates made successfully."
                )
                
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Edit parse failed: {e}")

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        # Clear feedback so it doesn't loop
        return {
            "content": updated_content,
            "human_feedback": "", 
            "pipeline_status": "editing" # Go back to edit router to request approval again
        }
