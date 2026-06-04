"""Event bus and function registry for ContentForge.

Implements the event-driven architecture from PRD §4.2.
Every node is registered as a callable function that can be
triggered via events, API calls, or CLI.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from rich.console import Console
from rich.table import Table

from contentforge.core.logger import PipelineLogger

console = Console()


@dataclass
class EventResult:
    """Result of an event execution."""
    event_name: str
    success: bool
    results: list[Any] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class NodeRegistration:
    """Registration info for a pipeline node."""
    name: str
    callable: Callable
    description: str = ""
    phase: str = ""
    is_async: bool = True
    input_keys: list[str] = field(default_factory=list)
    output_keys: list[str] = field(default_factory=list)


class EventBus:
    """Event bus for agent-to-agent and trigger-based communication.

    Supports:
    - Event registration and firing
    - Node function registry (call any node independently)
    - Event history tracking

    Usage:
        bus = EventBus(logger=pipeline_logger)

        # Register nodes
        bus.register_node("caption_writer", caption_writer_fn, phase="content")

        # Register event → node mappings
        bus.on("content.create", ["content_router"])
        bus.on("content.edit", ["edit_router"])

        # Fire events
        result = await bus.fire("content.create", {"topic_id": "topic_003"})

        # Call a node directly
        result = await bus.call_node("caption_writer", input_data)
    """

    def __init__(self, logger: PipelineLogger | None = None):
        self.logger = logger
        self._handlers: dict[str, list[str]] = defaultdict(list)  # event → [node_names]
        self._nodes: dict[str, NodeRegistration] = {}
        self._history: list[dict[str, Any]] = []

    def register_node(
        self,
        name: str,
        callable: Callable,
        description: str = "",
        phase: str = "",
        is_async: bool = True,
        input_keys: list[str] | None = None,
        output_keys: list[str] | None = None,
    ) -> None:
        """Register a pipeline node function.

        Args:
            name: Unique node name (e.g., "caption_writer").
            callable: The node function to call.
            description: Human-readable description.
            phase: Pipeline phase (e.g., "research", "content").
            is_async: Whether the function is async.
            input_keys: State keys the node reads.
            output_keys: State keys the node writes.
        """
        self._nodes[name] = NodeRegistration(
            name=name,
            callable=callable,
            description=description,
            phase=phase,
            is_async=is_async,
            input_keys=input_keys or [],
            output_keys=output_keys or [],
        )

        if self.logger:
            self.logger.event("node.register", {"node": name, "phase": phase})

    def on(self, event_name: str, node_names: list[str]) -> None:
        """Map an event to one or more node functions.

        Args:
            event_name: Event name (e.g., "content.create").
            node_names: List of node names to trigger.
        """
        self._handlers[event_name].extend(node_names)

    async def fire(self, event_name: str, payload: dict[str, Any] | None = None) -> EventResult:
        """Fire an event and run all registered handlers.

        Args:
            event_name: The event to fire.
            payload: Data to pass to the handlers.

        Returns:
            EventResult with results and any errors.
        """
        if self.logger:
            self.logger.event(event_name, payload)

        start_time = time.perf_counter()
        node_names = self._handlers.get(event_name, [])

        if not node_names:
            console.print(f"[yellow]WARNING: No handlers registered for event: {event_name}[/yellow]")
            return EventResult(
                event_name=event_name,
                success=False,
                errors=[f"No handlers for event: {event_name}"],
            )

        results = []
        errors = []

        for node_name in node_names:
            try:
                result = await self.call_node(node_name, payload or {})
                results.append(result)
            except Exception as e:
                error_msg = f"Node {node_name} failed: {str(e)}"
                errors.append(error_msg)
                if self.logger:
                    self.logger.error(node_name, str(e))

        duration_ms = (time.perf_counter() - start_time) * 1000

        event_result = EventResult(
            event_name=event_name,
            success=len(errors) == 0,
            results=results,
            errors=errors,
            duration_ms=duration_ms,
        )

        # Record history
        self._history.append({
            "event": event_name,
            "payload": payload,
            "success": event_result.success,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
        })

        return event_result

    async def call_node(self, node_name: str, input_data: dict[str, Any]) -> Any:
        """Call a registered node function directly.

        Args:
            node_name: Name of the registered node.
            input_data: Input data dict for the node.

        Returns:
            The node function's return value.

        Raises:
            KeyError: If node is not registered.
        """
        if node_name not in self._nodes:
            raise KeyError(f"Node not registered: {node_name}")

        node = self._nodes[node_name]

        if self.logger:
            self.logger.node_start(node_name, node.input_keys)

        start_time = time.perf_counter()

        try:
            if node.is_async:
                result = await node.callable(input_data)
            else:
                result = node.callable(input_data)

            duration_ms = (time.perf_counter() - start_time) * 1000

            if self.logger:
                self.logger.node_end(
                    node_name,
                    node.output_keys,
                    duration_ms=duration_ms,
                    status="success",
                )

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            if self.logger:
                self.logger.node_end(
                    node_name,
                    duration_ms=duration_ms,
                    status="failure",
                )
                self.logger.error(node_name, str(e))
            raise

    def list_nodes(self) -> list[dict[str, Any]]:
        """List all registered nodes with their info."""
        return [
            {
                "name": n.name,
                "phase": n.phase,
                "description": n.description,
                "input_keys": n.input_keys,
                "output_keys": n.output_keys,
            }
            for n in sorted(self._nodes.values(), key=lambda x: (x.phase, x.name))
        ]

    def list_events(self) -> dict[str, list[str]]:
        """List all registered events and their handlers."""
        return dict(self._handlers)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent event history."""
        return self._history[-limit:]

    def print_registry(self) -> None:
        """Print a formatted table of all registered nodes and events."""
        # Nodes table
        table = Table(title="Registered Nodes", show_header=True)
        table.add_column("Node", style="cyan")
        table.add_column("Phase", style="green")
        table.add_column("Description")

        for node in sorted(self._nodes.values(), key=lambda x: (x.phase, x.name)):
            table.add_row(node.name, node.phase, node.description)

        console.print(table)

        # Events table
        event_table = Table(title="Event → Node Mappings", show_header=True)
        event_table.add_column("Event", style="yellow")
        event_table.add_column("Triggers", style="cyan")

        for event, nodes in sorted(self._handlers.items()):
            event_table.add_row(event, ", ".join(nodes))

        console.print(event_table)
