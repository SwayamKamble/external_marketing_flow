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
        """Generate research prompts instantly without an LLM call."""
        
        brand_dna = input_data.get("brand_context", {}).get("brand_dna", "AI and Tech audience")
        content_pillars = input_data.get("brand_context", {}).get("content_pillars", "AI News, Tutorials, Opinions")

        output_contract = (
            "For each item, output a JSON array where each object has: "
            "\"date\" (YYYY-MM-DD of report), \"title\" (max 8 words), "
            "\"description\" (2-3 specific sentences), \"content_type\" "
            "(choose from: reel, carousel, post, animated_post), "
            "\"platform\": \"instagram\", \"source_url\", and \"why_it_matters\". "
            "CRITICAL RESPONSE RULES: return ONLY a JSON array; do not ask follow-up questions; "
            "do not offer options; do not add explanations. "
            "If live web browsing is unavailable, still return 10 best-effort candidate items in the same JSON schema, "
            "set \"source_url\": \"\", and keep \"why_it_matters\" concrete and useful."
        )

        prompts = [
            (
                "You are an expert AI researcher. Search the web for 10 distinct, high-signal AI "
                f"developments from the last 7 days. Focus on topics relevant to this audience: {brand_dna}. "
                "Cover product launches, model releases, funding/acquisitions, policy changes, open-source "
                "breakthroughs, and creator/developer trends. Do not merge separate stories unless they are "
                f"truly the same event. {output_contract}"
            ),
            (
                "You are an expert AI tools researcher. Search the web for 10 new or meaningfully updated AI "
                f"tools, workflows, libraries, or tutorials from the last 7 days. Focus on these content pillars: {content_pillars}. "
                "Prioritize tools a developer, founder, marketer, freelancer, or AI learner could actually try. "
                f"{output_contract}"
            ),
            (
                "You are an expert AI strategy researcher. Search the web for 10 practical AI tactics, automation "
                "workflows, agentic AI examples, coding workflows, or business use cases from the last 7 days. "
                "Prioritize examples with clear implementation value for Indian builders, startups, and creators. "
                f"{output_contract}"
            ),
            (
                "You are an expert tech discourse researcher. Search the web for 10 trending opinions, debates, "
                "controversies, benchmarks, failures, or contrarian takes in AI/tech from the last 7 days. "
                "Prioritize topics that can become sharp Instagram reels, carousels, or single-image opinion posts. "
                f"{output_contract}"
            ),
        ]

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
