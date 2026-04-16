"""CLI script to fire pipeline events.

Usage:
    uv run python scripts/fire_event.py --event content.create --topic-id topic_003
    uv run python scripts/fire_event.py --event pipeline.start
    uv run python scripts/fire_event.py --list  # List all registered events
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel

console = Console()


def build_event_bus():
    """Build the event bus with all registered events.

    This will be fully populated in Phase 2.
    """
    from contentforge.core.events import EventBus
    from contentforge.core.logger import PipelineLogger
    from contentforge.utils.platform_helpers import get_week_id

    logger = PipelineLogger(log_dir="./data/logs", week_id=get_week_id())
    bus = EventBus(logger=logger)

    # Events will be registered here in Phase 2
    # bus.on("pipeline.start", ["brand_context_loader", "research_prompt_generator"])
    # bus.on("research.submit", ["research_parser"])
    # bus.on("content.create", ["content_router"])
    # ...

    return bus


async def fire_event(event_name: str, payload: dict) -> None:
    """Fire an event through the event bus."""
    bus = build_event_bus()

    console.print(Panel(
        f"[bold]Firing event:[/] {event_name}\n"
        f"[bold]Payload:[/] {json.dumps(payload, indent=2)}",
        title="Event Fire",
        border_style="yellow",
    ))

    result = await bus.fire(event_name, payload)

    if result.success:
        console.print(f"[green]✓ Event handled successfully ({result.duration_ms:.0f}ms)[/green]")
        for r in result.results:
            console.print(f"  Result: {json.dumps(r, indent=2, default=str)[:500]}")
    else:
        console.print(f"[red]✗ Event failed[/red]")
        for err in result.errors:
            console.print(f"  [red]Error: {err}[/red]")


def main():
    parser = argparse.ArgumentParser(description="Fire a ContentForge pipeline event")
    parser.add_argument("--event", "-e", type=str, help="Event name to fire")
    parser.add_argument("--topic-id", "-t", type=str, default="", help="Topic ID")
    parser.add_argument("--week", "-w", type=str, default="", help="Week ID")
    parser.add_argument("--data", "-d", type=str, default="", help="JSON payload string")
    parser.add_argument("--list", "-l", action="store_true", help="List all registered events")

    args = parser.parse_args()

    if args.list:
        bus = build_event_bus()
        events = bus.list_events()
        if not events:
            console.print("[yellow]No events registered yet. Wire events in Phase 2.[/yellow]")
        else:
            bus.print_registry()
        return

    if not args.event:
        parser.print_help()
        return

    payload = {}
    if args.topic_id:
        payload["topic_id"] = args.topic_id
    if args.week:
        payload["week_id"] = args.week
    if args.data:
        payload.update(json.loads(args.data))

    asyncio.run(fire_event(args.event, payload))


if __name__ == "__main__":
    main()
