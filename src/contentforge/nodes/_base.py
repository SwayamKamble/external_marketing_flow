"""Base node class for ContentForge pipeline nodes.

Every pipeline node extends this base class to get:
- Automatic logging (node start/end, timing)
- LLM Gateway access (auto model routing)
- File Memory access (read/write artifacts)
- Prompt loading (auto system prompt loading)
- Error handling with retry awareness
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from contentforge.core.config_loader import ConfigLoader
from contentforge.core.file_memory import FileMemory
from contentforge.core.llm_gateway import LLMGateway, LLMCallResult
from contentforge.core.logger import PipelineLogger
from contentforge.core.prompt_loader import PromptLoader


@dataclass
class NodeContext:
    """Context object passed to every node execution.

    Contains all the dependencies a node needs.
    """
    week_id: str
    topic_id: str = ""
    config: ConfigLoader | None = None
    memory: FileMemory | None = None
    llm: LLMGateway | None = None
    logger: PipelineLogger | None = None
    prompts: PromptLoader | None = None
    brand_context: dict[str, Any] | None = None
    extra: dict[str, Any] | None = None


class BaseNode(ABC):
    """Base class for all pipeline nodes.

    Provides the standard execution contract from PRD §16.1:
    - Takes typed input → returns typed output
    - Can be called independently via CLI or API
    - Reads from / writes to file-based memory
    - Is traced by LangSmith automatically
    - Has its system prompt stored in a dedicated file

    Usage:
        class CaptionWriter(BaseNode):
            node_name = "caption_writer"
            category = "content"

            async def process(self, input_data, context):
                prompt, config = self.load_prompt(context)
                result = await self.call_llm(context, prompt, input_data["topic"])
                return {"caption": result.content}

        # Run it
        writer = CaptionWriter()
        output = await writer.run({"topic": "AI agents"}, context)
    """

    # Override in subclasses
    node_name: str = "base_node"
    category: str = ""  # "research", "scoring", "content", etc.
    description: str = ""

    async def run(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Execute the node with full logging and error handling.

        This is the main entry point. It wraps process() with:
        - Start/end logging
        - Timing
        - Error handling

        Args:
            input_data: Node input data dict.
            context: NodeContext with dependencies.

        Returns:
            Node output data dict.
        """
        logger = context.logger
        start_time = time.perf_counter()

        if logger:
            logger.node_start(self.node_name)

        try:
            result = await self.process(input_data, context)
            duration_ms = (time.perf_counter() - start_time) * 1000

            if logger:
                logger.node_end(
                    self.node_name,
                    duration_ms=duration_ms,
                    status="success",
                )

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            if logger:
                logger.node_end(
                    self.node_name,
                    duration_ms=duration_ms,
                    status="failure",
                )
                logger.error(self.node_name, str(e))

            raise

    @abstractmethod
    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Core processing logic — override in subclasses.

        Args:
            input_data: Node-specific input data.
            context: NodeContext with all dependencies.

        Returns:
            Node-specific output data dict.
        """
        ...

    def load_prompt(
        self,
        context: NodeContext,
        extra_variables: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Load this node's system prompt with brand context.

        Args:
            context: NodeContext with prompt loader and brand context.
            extra_variables: Additional template variables.

        Returns:
            Tuple of (rendered_prompt, config_dict).
        """
        if not context.prompts:
            return "", {}

        return context.prompts.build_prompt(
            node_name=self.node_name,
            category=self.category,
            brand_context=context.brand_context,
            extra_variables=extra_variables,
        )

    async def call_llm(
        self,
        context: NodeContext,
        system_prompt: str,
        user_message: str,
        **kwargs,
    ) -> LLMCallResult:
        """Call the LLM through the gateway with automatic model routing.

        Args:
            context: NodeContext with LLM gateway.
            system_prompt: System prompt for the call.
            user_message: User message / content.
            **kwargs: Additional args passed to LLMGateway.call().

        Returns:
            LLMCallResult with content and metadata.
        """
        if not context.llm:
            raise RuntimeError(f"Node {self.node_name}: LLM Gateway not available")

        result = await context.llm.call(
            node_name=self.node_name,
            system_prompt=system_prompt,
            user_message=user_message,
            **kwargs,
        )

        # Log the LLM call
        if context.logger:
            context.logger.llm_call(
                node=self.node_name,
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
            )

        return result

    def save_artifact(
        self,
        context: NodeContext,
        phase: str,
        filename: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an artifact to file memory.

        Args:
            context: NodeContext with file memory.
            phase: Pipeline phase folder.
            filename: File name for the artifact.
            content: Markdown content to save.
            metadata: Optional additional metadata.
        """
        if not context.memory:
            return

        meta = {"node": self.node_name}
        if metadata:
            meta.update(metadata)

        context.memory.write_artifact(
            week_id=context.week_id,
            phase=phase,
            filename=filename,
            content=content,
            metadata=meta,
            topic_id=context.topic_id or None,
        )

    def read_artifact(
        self,
        context: NodeContext,
        phase: str,
        filename: str,
    ) -> dict[str, Any]:
        """Read an artifact from file memory.

        Args:
            context: NodeContext with file memory.
            phase: Pipeline phase folder.
            filename: File name to read.

        Returns:
            Dict with content and metadata.
        """
        if not context.memory:
            return {"content": "", "metadata": {}, "exists": False}

        return context.memory.read_artifact(
            week_id=context.week_id,
            phase=phase,
            filename=filename,
            topic_id=context.topic_id or None,
        )
