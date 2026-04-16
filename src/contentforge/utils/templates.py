"""Template rendering utilities for ContentForge.

Uses Jinja2 for rendering string templates with variables.
"""

from __future__ import annotations

from typing import Any

from jinja2 import BaseLoader, Environment, Template


# Shared Jinja2 environment
_jinja_env = Environment(loader=BaseLoader(), autoescape=False)


def render_template(template_str: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template string with variables.

    Args:
        template_str: Template string with {{ variable }} placeholders.
        variables: Dict of variable names → values.

    Returns:
        Rendered string.
    """
    try:
        template = _jinja_env.from_string(template_str)
        return template.render(**variables)
    except Exception:
        # Fallback: simple string replacement for {variable} style
        result = template_str
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"{{{{ {key} }}}}", str(value))
        return result


def build_system_prompt(
    global_context: str,
    brand_context: dict[str, str],
    node_prompt: str,
    topic_context: dict[str, Any] | None = None,
) -> str:
    """Build a complete system prompt by merging context layers.

    Follows the pattern from PRD §7.1:
    1. Global context
    2. Brand context
    3. Node-specific prompt
    4. Topic context

    Args:
        global_context: Content from prompts/_global_context.md
        brand_context: Dict of brand files {filename: content}
        node_prompt: The node-specific prompt content
        topic_context: Optional topic-specific context

    Returns:
        Merged system prompt string.
    """
    parts = []

    # 1. Global context
    if global_context.strip():
        parts.append(global_context.strip())

    # 2. Brand context
    if brand_context:
        brand_section = "# BRAND CONTEXT\n"
        for name, content in brand_context.items():
            brand_section += f"\n## {name.replace('_', ' ').title()}\n{content}\n"
        parts.append(brand_section.strip())

    # 3. Node-specific prompt
    if node_prompt.strip():
        parts.append(node_prompt.strip())

    # 4. Topic context
    if topic_context:
        topic_section = "# CURRENT TOPIC CONTEXT\n"
        for key, value in topic_context.items():
            if isinstance(value, dict):
                topic_section += f"\n## {key}\n"
                for k, v in value.items():
                    topic_section += f"- **{k}**: {v}\n"
            elif isinstance(value, list):
                topic_section += f"\n## {key}\n"
                for item in value:
                    topic_section += f"- {item}\n"
            else:
                topic_section += f"- **{key}**: {value}\n"
        parts.append(topic_section.strip())

    return "\n\n---\n\n".join(parts)


def format_json_output_instruction(fields: dict[str, str]) -> str:
    """Generate a JSON output format instruction for LLM prompts.

    Args:
        fields: Dict of field_name → description.

    Returns:
        Formatted instruction string.
    """
    lines = ["# OUTPUT FORMAT", "Return valid JSON with this structure:", "```json", "{"]

    for i, (field, desc) in enumerate(fields.items()):
        comma = "," if i < len(fields) - 1 else ""
        lines.append(f'  "{field}": "..."{comma}  // {desc}')

    lines.extend(["}", "```"])
    return "\n".join(lines)
