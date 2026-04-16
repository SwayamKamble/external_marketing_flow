"""System prompt loader for ContentForge.

Loads and templates system prompts from the prompts/ folder.
Supports Jinja2 templating for dynamic prompt construction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter
from jinja2 import Template
from rich.console import Console

console = Console()


class PromptLoader:
    """Loads and templates system prompts from the prompts/ directory.

    Every node has its system prompt stored in a dedicated .md file.
    This loader reads those files, extracts config from frontmatter,
    and renders the prompt with Jinja2 templating.

    Usage:
        loader = PromptLoader(prompts_dir="./prompts")
        prompt, config = loader.load(
            "content/caption_writer",
            variables={
                "brand_tone": "Professional yet approachable",
                "platform_name": "Instagram",
                "char_limit": 2200,
            },
        )
    """

    def __init__(self, prompts_dir: str | Path = "./prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, tuple[str, dict[str, Any]]] = {}

        if not self.prompts_dir.exists():
            console.print(
                f"[yellow]⚠ Prompts directory not found: {self.prompts_dir}. "
                f"Creating it...[/yellow]"
            )
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def load(
        self,
        prompt_path: str,
        variables: dict[str, Any] | None = None,
        include_global: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        """Load a system prompt and render it with variables.

        Args:
            prompt_path: Relative path within prompts/ (without .md extension).
                         e.g., "content/caption_writer" or "research/research_parser".
            variables: Dict of template variables to substitute.
            include_global: Whether to prepend _global_context.md.

        Returns:
            Tuple of (rendered_prompt_string, frontmatter_config_dict).
        """
        full_path = self.prompts_dir / f"{prompt_path}.md"

        if not full_path.exists():
            console.print(f"[yellow]⚠ Prompt not found: {full_path}[/yellow]")
            return "", {}

        # Load and parse the prompt file
        post = frontmatter.load(str(full_path))
        raw_content = post.content
        config = dict(post.metadata)

        # Optionally prepend global context
        if include_global:
            global_content = self._load_global_context()
            if global_content:
                raw_content = global_content + "\n\n---\n\n" + raw_content

        # Render with Jinja2 templating
        rendered = raw_content
        if variables:
            try:
                template = Template(raw_content)
                rendered = template.render(**variables)
            except Exception as e:
                console.print(f"[yellow]⚠ Template render error: {e}[/yellow]")
                rendered = raw_content

        return rendered, config

    def load_raw(self, prompt_path: str) -> str:
        """Load a raw prompt without templating.

        Args:
            prompt_path: Relative path within prompts/ (without .md).

        Returns:
            Raw prompt content string.
        """
        full_path = self.prompts_dir / f"{prompt_path}.md"
        if not full_path.exists():
            return ""

        post = frontmatter.load(str(full_path))
        return post.content

    def get_config(self, prompt_path: str) -> dict[str, Any]:
        """Get the frontmatter config for a prompt.

        Returns things like temperature, max_tokens, model override.
        """
        full_path = self.prompts_dir / f"{prompt_path}.md"
        if not full_path.exists():
            return {}

        post = frontmatter.load(str(full_path))
        return dict(post.metadata)

    def build_prompt(
        self,
        node_name: str,
        category: str,
        brand_context: dict[str, Any] | None = None,
        topic_context: dict[str, Any] | None = None,
        extra_variables: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Build a complete prompt for a node using the standard loading pattern.

        Follows the pattern from PRD §7.1:
        1. Load global context
        2. Load brand context
        3. Load node-specific prompt
        4. Merge variables and render

        Args:
            node_name: Name of the node (e.g., "caption_writer").
            category: Category folder (e.g., "content", "research").
            brand_context: Brand DNA and style info.
            topic_context: Topic-specific context from file memory.
            extra_variables: Additional template variables.

        Returns:
            Tuple of (rendered_prompt, config_dict).
        """
        # Merge all variables
        variables: dict[str, Any] = {}
        if brand_context:
            variables.update(brand_context)
            variables["brand_context"] = brand_context
        if topic_context:
            variables.update(topic_context)
        if extra_variables:
            variables.update(extra_variables)

        prompt_path = f"{category}/{node_name}"
        return self.load(prompt_path, variables=variables, include_global=True)

    def list_prompts(self) -> list[str]:
        """List all available prompt files."""
        prompts = []
        for p in self.prompts_dir.rglob("*.md"):
            if p.name != "README.md" and not p.name.startswith("_"):
                rel = p.relative_to(self.prompts_dir)
                prompts.append(str(rel.with_suffix("")))
        return sorted(prompts)

    def _load_global_context(self) -> str:
        """Load the global context that's prepended to all prompts."""
        global_path = self.prompts_dir / "_global_context.md"
        if not global_path.exists():
            return ""

        post = frontmatter.load(str(global_path))
        return post.content
