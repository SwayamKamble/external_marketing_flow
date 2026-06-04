"""CLI script to run any pipeline node independently.

Usage:
    uv run python scripts/run_node.py --node caption_writer --input tests/fixtures/sample.json
    uv run python scripts/run_node.py --node research_parser --input data/weeks/2026-W16/01_research/raw_research_news.md
    uv run python scripts/run_node.py --list  # List all available nodes
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
from rich.syntax import Syntax

console = Console()


def get_node_registry() -> dict:
    """Get all registered nodes. Populated as nodes are built."""
    from contentforge.nodes.content.caption_writer import CaptionWriter
    
    return {
        "caption_writer": CaptionWriter
    }


def load_input(input_path: str) -> dict:
    """Load input data from a JSON or markdown file."""
    path = Path(input_path)

    if not path.exists():
        console.print(f"[red]Error: Input file not found: {path}[/red]")
        sys.exit(1)

    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif path.suffix == ".md":
        content = path.read_text(encoding="utf-8")
        return {"content": content, "file_path": str(path)}
    else:
        content = path.read_text(encoding="utf-8")
        return {"content": content}


async def run_node(node_name: str, input_data: dict, week_id: str = "") -> dict:
    """Run a single node with the given input."""
    from contentforge.core.config_loader import ConfigLoader
    from contentforge.core.file_memory import FileMemory
    from contentforge.core.llm_gateway import LLMGateway
    from contentforge.core.logger import PipelineLogger
    from contentforge.core.prompt_loader import PromptLoader
    from contentforge.nodes._base import NodeContext
    from contentforge.utils.platform_helpers import get_week_id

    if not week_id:
        week_id = get_week_id()

    # Initialize infrastructure
    config = ConfigLoader(config_dir="./config")
    memory = FileMemory(data_dir="./data")
    llm = LLMGateway(config=config)
    logger = PipelineLogger(log_dir="./data/logs", week_id=week_id)
    prompts = PromptLoader(prompts_dir="./prompts")

    # Build context
    context = NodeContext(
        week_id=week_id,
        config=config,
        memory=memory,
        llm=llm,
        logger=logger,
        prompts=prompts,
        brand_context=memory.get_brand_context(),
    )

    # Look up the node
    registry = get_node_registry()
    if node_name not in registry:
        console.print(f"[red]Error: Node '{node_name}' not found.[/red]")
        console.print(f"Available nodes: {', '.join(registry.keys()) or '(none yet - implement nodes in Phase 2)'}")
        sys.exit(1)

    node_class = registry[node_name]
    node = node_class()

    console.print(Panel(
        f"[bold]Running node:[/] {node_name}\n"
        f"[bold]Week:[/] {week_id}\n"
        f"[bold]Input keys:[/] {list(input_data.keys())}",
        title="Node Execution",
        border_style="cyan",
    ))

    # Execute
    result = await node.run(input_data, context)

    # Pretty print the result
    result_json = json.dumps(result, indent=2, default=str)
    console.print(Panel(
        Syntax(result_json, "json", theme="monokai"),
        title="Node Output",
        border_style="green",
    ))

    # Show LLM stats
    console.print(f"\n[dim]{llm.get_stats_summary()}[/dim]")

    return result


def main():
    parser = argparse.ArgumentParser(description="Run a ContentForge pipeline node")
    parser.add_argument("--node", "-n", type=str, help="Node name to run")
    parser.add_argument("--input", "-i", type=str, help="Input file (JSON or MD)")
    parser.add_argument("--week", "-w", type=str, default="", help="Week ID (e.g., 2026-W16)")
    parser.add_argument("--list", "-l", action="store_true", help="List all available nodes")

    args = parser.parse_args()

    if args.list:
        registry = get_node_registry()
        if not registry:
            console.print("[yellow]No nodes registered yet. Build nodes in Phase 2.[/yellow]")
        else:
            for name in sorted(registry):
                console.print(f"  [cyan]{name}[/cyan]")
        return

    if not args.node:
        parser.print_help()
        return

    input_data = {}
    if args.input:
        input_data = load_input(args.input)

    asyncio.run(run_node(args.node, input_data, args.week))


if __name__ == "__main__":
    main()
