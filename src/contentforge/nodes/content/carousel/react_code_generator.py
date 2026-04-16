"""React UI Code generator node."""

from __future__ import annotations

from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


class ReactCodeGenerator(BaseNode):
    """Translates slide content and theme into React code.
    
    Generates a full React functional component that renders the carousel,
    so it can be screenshotted by a headless browser later.
    """

    node_name = "react_code_generator"
    category = "content"
    description = "Generates React/Tailwind code to render the carousel visually."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        tc = content_dict.get(topic_id)
        if not tc or not tc.carousel_slides or not tc.theme:
            return {}

        system_prompt, config = self.load_prompt(context)
        
        theme_str = f"Colors: BG={tc.theme.background_color}, Text={tc.theme.text_color}, Primary={tc.theme.primary_color}, Accent={tc.theme.accent_color}\nFonts: {tc.theme.font_heading}, {tc.theme.font_body}"
        slides_str = str([{"slide": s.slide_number, "heading": s.heading, "body": s.body_text} for s in tc.carousel_slides])
        
        user_msg = f"Theme:\n{theme_str}\n\nSlides Data:\n{slides_str}"

        # No JSON forcing here, we want raw code
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=user_msg,
            model=config.get("model", "gpt-5-chat"),
            temperature=0.1,
            max_tokens=4000
        )

        if result.success:
            # Simple markdown extraction
            code = result.content
            if "```tsx" in code:
                code = code.split("```tsx")[1].split("```")[0].strip()
            elif "```jsx" in code:
                code = code.split("```jsx")[1].split("```")[0].strip()
            
            tc.rendered_code = code
            
            self.save_artifact(
                context=context,
                phase="05_content",
                topic_id=topic_id,
                filename="Carousel.tsx",
                content=f"// Generated React Carousel for {topic_id}\n\n{code}"
            )

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        
        return {
            "content": updated_content, 
            "carousel_status": "done",
            "pipeline_status": "editing" # Moves to formatting/editing phase
        }
