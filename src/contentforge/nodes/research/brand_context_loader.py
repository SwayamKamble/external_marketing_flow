"""Node to load brand context and inject it into the pipeline state."""

from __future__ import annotations

from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


class BrandContextLoader(BaseNode):
    """Loads all brand DNA and style guide files into state.

    This node runs at the very beginning of the pipeline. It reads all
    .md files from data/brand/ and platform_rules.yaml from config/,
    saving them to the state so other nodes don't need to read from disk.
    """

    node_name = "brand_context_loader"
    category = "research"
    description = "Loads brand DNA and style guides into pipeline state."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Load brand context from memory and config.

        Expects empty input (it reads from file memory/config).
        """
        # Load brand markdown files
        brand_context = {}
        if context.memory:
            brand_context = context.memory.get_brand_context()

        # Load platform rules
        platform_rules = {}
        if context.config:
            platform_rules = context.config.get_platform_rules()

        # Log what we found
        if context.logger:
            context.logger.event("brand_context.loaded", {
                "files_found": list(brand_context.keys()),
                "platforms_configured": list(platform_rules.get("platforms", {}).keys()),
            })

        # Return state update
        return {
            "brand_context": brand_context,
            "platform_rules": platform_rules,
        }
