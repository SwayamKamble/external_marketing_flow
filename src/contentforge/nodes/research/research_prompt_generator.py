"""Node to generate prompts for external LLM research."""

from __future__ import annotations

import json
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


class ResearchPromptGenerator(BaseNode):
    """Generates optimal search/LLM prompts for the initial research phase.

    This node takes the brand context and creates 4 specific prompts
    that a human (or automated crawler) can paste into an external LLM
    (like ChatGPT with browsing or Perplexity) to gather raw research.
    """

    node_name = "research_prompt_generator"
    category = "research"
    description = "Generates prompts for gathering initial raw research."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Generate research prompts via LLM."""
        # Load the system prompt
        system_prompt, config = self.load_prompt(context)

        # Call the LLM (formatting output as JSON explicitly via prompt format)
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message="Generate the weekly research prompts based on our brand context.",
            response_format={"type": "json_object"},
            # Use overrides from prompt file if present
            model=config.get("model"),
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens", 4096),
        )

        if not result.success:
            raise RuntimeError(f"LLM call failed: {result.error}")

        # Parse JSON
        try:
            parsed = json.loads(result.content)
            prompts = parsed.get("prompts", [])
            if not isinstance(prompts, list):
                prompts = [str(p) for p in prompts]
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"JSON parse block: {e}")
            raise ValueError(f"Failed to parse LLM output as JSON:\n{result.content}")

        # Save to file memory
        self.save_artifact(
            context=context,
            phase="01_research",
            filename="research_prompts.md",
            content="\n\n---\n\n".join(f"## Prompt {i+1}\n\n{p}" for i, p in enumerate(prompts)),
        )

        # Update state
        return {
            "research_prompts": prompts,
            "pipeline_status": "research",  # Transition state
        }
