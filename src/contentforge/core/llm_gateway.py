"""Unified LLM Gateway for ContentForge.

Uses OpenAI SDK to talk to Azure OpenAI endpoint.
Supports per-node model routing, retry with backoff, cost tracking,
and automatic LangSmith tracing via environment variables.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI, OpenAI
from rich.console import Console

from contentforge.core.config_loader import ConfigLoader

console = Console()


@dataclass
class LLMCallResult:
    """Result of a single LLM call with metadata."""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class LLMCallStats:
    """Accumulated stats across multiple LLM calls."""
    total_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    calls_by_model: dict[str, int] = field(default_factory=dict)
    calls_by_node: dict[str, int] = field(default_factory=dict)


class LLMGateway:
    """Unified OpenAI SDK wrapper with model routing and cost tracking.

    Usage:
        gateway = LLMGateway(config_loader)
        result = await gateway.call(
            node_name="caption_writer",
            system_prompt="You are a copywriter...",
            user_message="Write a caption about...",
        )
        print(result.content)
    """

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.stats = LLMCallStats()

        # Load provider config
        provider = config.get_provider_config()
        base_url = provider.get("base_url", "")
        api_key = provider.get("api_key", "")

        if not base_url or not api_key or api_key == "${LLM_API_KEY}":
            console.print(
                "[yellow]⚠ LLM Gateway: No API key configured. "
                "Set LLM_API_KEY in .env file.[/yellow]"
            )

        # Initialize OpenAI clients (sync + async)
        self._sync_client = OpenAI(base_url=base_url, api_key=api_key)
        self._async_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

        # Load retry config
        retry_config = config.get_llm_config().get("retry", {})
        self._max_retries = retry_config.get("max_retries", 3)
        self._base_delay = retry_config.get("base_delay_seconds", 1.0)
        self._max_delay = retry_config.get("max_delay_seconds", 30.0)

    async def call(
        self,
        node_name: str,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        **kwargs,
    ) -> LLMCallResult:
        """Make an async LLM call with automatic model routing and retry.

        Args:
            node_name: Name of the calling node (for model routing + logging).
            system_prompt: System prompt for the LLM.
            user_message: User message / input content.
            model: Override model name. If None, uses node_model_mapping.
            temperature: Override temperature. If None, uses default.
            max_tokens: Max tokens for the response.
            response_format: Optional response format (e.g., {"type": "json_object"}).

        Returns:
            LLMCallResult with content and metadata.
        """
        # Resolve model from config if not overridden
        resolved_model = model or self.config.get_model_for_node(node_name)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Build API call kwargs
        call_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if response_format:
            call_kwargs["response_format"] = response_format

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self._max_retries):
            try:
                start_time = time.perf_counter()
                response = await self._async_client.chat.completions.create(**call_kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000

                # Extract usage info
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else 0

                # Build result
                result = LLMCallResult(
                    content=response.choices[0].message.content or "",
                    model=resolved_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    success=True,
                )

                # Update stats
                self._update_stats(node_name, resolved_model, result)

                return result

            except Exception as e:
                last_error = str(e)
                if attempt < self._max_retries - 1:
                    delay = min(
                        self._base_delay * (2 ** attempt),
                        self._max_delay,
                    )
                    console.print(
                        f"[yellow]⚠ LLM call failed (attempt {attempt + 1}/{self._max_retries}): "
                        f"{last_error}. Retrying in {delay:.1f}s...[/yellow]"
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        return LLMCallResult(
            content="",
            model=resolved_model,
            success=False,
            error=f"All {self._max_retries} attempts failed. Last error: {last_error}",
        )

    def call_sync(
        self,
        node_name: str,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMCallResult:
        """Synchronous wrapper for LLM calls (for CLI/testing).

        Same interface as `call()` but blocks until complete.
        """
        resolved_model = model or self.config.get_model_for_node(node_name)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        call_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            call_kwargs["temperature"] = temperature

        last_error = None
        for attempt in range(self._max_retries):
            try:
                start_time = time.perf_counter()
                response = self._sync_client.chat.completions.create(**call_kwargs)
                latency_ms = (time.perf_counter() - start_time) * 1000

                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else 0

                result = LLMCallResult(
                    content=response.choices[0].message.content or "",
                    model=resolved_model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    success=True,
                )

                self._update_stats(node_name, resolved_model, result)
                return result

            except Exception as e:
                last_error = str(e)
                if attempt < self._max_retries - 1:
                    delay = min(self._base_delay * (2 ** attempt), self._max_delay)
                    console.print(
                        f"[yellow]⚠ LLM call failed (attempt {attempt + 1}): "
                        f"{last_error}. Retrying in {delay:.1f}s...[/yellow]"
                    )
                    time.sleep(delay)

        return LLMCallResult(
            content="",
            model=resolved_model,
            success=False,
            error=f"All {self._max_retries} attempts failed. Last error: {last_error}",
        )

    def _update_stats(self, node_name: str, model: str, result: LLMCallResult) -> None:
        """Update accumulated statistics."""
        self.stats.total_calls += 1
        self.stats.total_tokens += result.total_tokens
        self.stats.total_cost_usd += result.cost_usd
        self.stats.total_latency_ms += result.latency_ms

        self.stats.calls_by_model[model] = self.stats.calls_by_model.get(model, 0) + 1
        self.stats.calls_by_node[node_name] = self.stats.calls_by_node.get(node_name, 0) + 1

    def get_stats_summary(self) -> str:
        """Return a formatted summary of LLM usage stats."""
        s = self.stats
        lines = [
            f"Total LLM calls: {s.total_calls}",
            f"Total tokens: {s.total_tokens:,}",
            f"Total latency: {s.total_latency_ms / 1000:.1f}s",
            f"Calls by model: {dict(s.calls_by_model)}",
            f"Calls by node: {dict(s.calls_by_node)}",
        ]
        return "\n".join(lines)
