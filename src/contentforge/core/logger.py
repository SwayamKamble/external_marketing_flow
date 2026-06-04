"""Multi-level structured logging system for ContentForge.

Implements 4 log levels from PRD §8:
  Level 1: Pipeline Events (pipeline_events.log)
  Level 2: LLM Calls (llm_calls.log)
  Level 3: Node Executions (node_executions.log)
  Level 4: Errors (errors.log)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

console = Console()


class PipelineLogger:
    """Structured multi-level logger for ContentForge pipeline.

    Creates separate log files for events, LLM calls, node executions,
    and errors. Also logs to console with Rich formatting.

    Usage:
        logger = PipelineLogger(log_dir="./data/logs", week_id="2026-W16")
        logger.event("pipeline.start", {"week": "2026-W16"})
        logger.llm_call("caption_writer", "gpt-5-chat", 1200, 800, 2.1)
        logger.node_start("caption_writer", ["topic_context", "theme"])
        logger.node_end("caption_writer", ["caption_v1", "caption_v2"], 4200, "success")
        logger.error("caption_writer", "Caption exceeded 2200 chars")
    """

    def __init__(
        self,
        log_dir: str | Path = "./data/logs",
        week_id: str = "",
        log_level: str = "DEBUG",
        log_to_console: bool = True,
        log_to_file: bool = True,
    ):
        self.log_dir = Path(log_dir)
        self.week_id = week_id
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file

        # Set up week-specific log directory
        if week_id:
            self.week_log_dir = self.log_dir / week_id
        else:
            self.week_log_dir = self.log_dir

        self.week_log_dir.mkdir(parents=True, exist_ok=True)

        # Create Python logger for console output
        self._logger = logging.getLogger("contentforge")
        self._logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

        if log_to_console and not self._logger.handlers:
            handler = RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                markup=True,
            )
            handler.setLevel(logging.DEBUG)
            self._logger.addHandler(handler)

    def _now(self) -> str:
        """Get current UTC timestamp string."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _append_log(self, filename: str, data: dict[str, Any]) -> None:
        """Append a JSON line to a log file."""
        if not self.log_to_file:
            return

        log_path = self.week_log_dir / filename
        data["timestamp"] = self._now()

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")

    # ── Level 1: Pipeline Events ──

    def event(self, event_name: str, details: dict[str, Any] | None = None) -> None:
        """Log a pipeline event (Level 1).

        Args:
            event_name: Event name (e.g., "pipeline.start", "human.interrupt").
            details: Optional dict of event details.
        """
        data = {"level": "EVENT", "event": event_name}
        if details:
            data["details"] = details

        self._append_log("pipeline_events.log", data)
        self._logger.info(f"[bold cyan]EVENT[/] {event_name} {details or ''}")

    # ── Level 2: LLM Calls ──

    def llm_call(
        self,
        node: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost_usd: float = 0.0,
        input_file: str = "",
        output_file: str = "",
        langsmith_trace_id: str = "",
    ) -> None:
        """Log an LLM API call (Level 2).

        Args:
            node: Node that made the call.
            model: Model used.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            latency_ms: Call latency in milliseconds.
            cost_usd: Estimated cost in USD.
            input_file: Source file read for input.
            output_file: File written with output.
            langsmith_trace_id: LangSmith trace ID if available.
        """
        data = {
            "level": "LLM_CALL",
            "node": node,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": round(latency_ms, 1),
            "cost_usd": round(cost_usd, 6),
        }
        if input_file:
            data["input_file"] = input_file
        if output_file:
            data["output_file"] = output_file
        if langsmith_trace_id:
            data["langsmith_trace_id"] = langsmith_trace_id

        self._append_log("llm_calls.log", data)
        self._logger.info(
            f"[bold magenta]LLM[/] {node} -> {model} "
            f"({input_tokens}+{output_tokens} tokens, {latency_ms:.0f}ms)"
        )

    # ── Level 3: Node Executions ──

    def node_start(
        self,
        node: str,
        input_state_keys: list[str] | None = None,
        files_read: list[str] | None = None,
    ) -> None:
        """Log the start of a node execution (Level 3).

        Args:
            node: Node name.
            input_state_keys: State keys the node reads from.
            files_read: Files read by the node.
        """
        data = {
            "level": "NODE_START",
            "node": node,
        }
        if input_state_keys:
            data["input_state_keys"] = input_state_keys
        if files_read:
            data["files_read"] = files_read

        self._append_log("node_executions.log", data)
        self._logger.info(f"[bold green]NODE START[/] {node}")

    def node_end(
        self,
        node: str,
        output_state_keys: list[str] | None = None,
        files_written: list[str] | None = None,
        duration_ms: float = 0.0,
        status: str = "success",
    ) -> None:
        """Log the end of a node execution (Level 3).

        Args:
            node: Node name.
            output_state_keys: State keys the node wrote to.
            files_written: Files written by the node.
            duration_ms: Total execution time in milliseconds.
            status: "success" or "failure".
        """
        data = {
            "level": "NODE_END",
            "node": node,
            "duration_ms": round(duration_ms, 1),
            "status": status,
        }
        if output_state_keys:
            data["output_state_keys"] = output_state_keys
        if files_written:
            data["files_written"] = files_written

        self._append_log("node_executions.log", data)

        status_color = "green" if status == "success" else "red"
        self._logger.info(
            f"[bold {status_color}]NODE END[/] {node} - {status} ({duration_ms:.0f}ms)"
        )

    # ── Level 4: Errors ──

    def error(
        self,
        node: str,
        error_message: str,
        action: str = "",
        retry_count: int = 0,
        resolved: bool = False,
    ) -> None:
        """Log an error (Level 4).

        Args:
            node: Node where the error occurred.
            error_message: Description of the error.
            action: Action taken (e.g., "Auto-retry with truncation instruction").
            retry_count: Number of retries attempted.
            resolved: Whether the error was resolved.
        """
        data = {
            "level": "ERROR",
            "node": node,
            "error": error_message,
            "action": action,
            "retry_count": retry_count,
            "resolved": resolved,
        }

        self._append_log("errors.log", data)
        self._logger.error(
            f"[bold red]ERROR[/] {node}: {error_message}"
            + (f" -> {action}" if action else "")
        )

    # ── Utility ──

    def read_log(self, log_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """Read entries from a log file.

        Args:
            log_type: Log file name (e.g., "pipeline_events", "llm_calls").
            limit: Max entries to return (newest first).

        Returns:
            List of log entry dicts.
        """
        log_path = self.week_log_dir / f"{log_type}.log"
        if not log_path.exists():
            return []

        entries = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return entries[-limit:]

    def get_cost_summary(self) -> dict[str, Any]:
        """Calculate cost summary from LLM call logs."""
        llm_entries = self.read_log("llm_calls", limit=10000)

        total_cost = sum(e.get("cost_usd", 0) for e in llm_entries)
        total_tokens = sum(e.get("total_tokens", 0) for e in llm_entries)
        total_calls = len(llm_entries)

        by_model: dict[str, dict[str, Any]] = {}
        for entry in llm_entries:
            model = entry.get("model", "unknown")
            if model not in by_model:
                by_model[model] = {"calls": 0, "tokens": 0, "cost": 0.0}
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += entry.get("total_tokens", 0)
            by_model[model]["cost"] += entry.get("cost_usd", 0)

        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_model": by_model,
        }
