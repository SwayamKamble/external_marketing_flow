"""Markdown file utilities for ContentForge.

Handles reading and writing .md files with YAML frontmatter,
content extraction, and formatting helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter


def read_md(file_path: str | Path) -> dict[str, Any]:
    """Read a markdown file with YAML frontmatter.

    Args:
        file_path: Path to the .md file.

    Returns:
        Dict with "content" (str), "metadata" (dict), and "exists" (bool).
    """
    path = Path(file_path)
    if not path.exists():
        return {"content": "", "metadata": {}, "exists": False}

    try:
        post = frontmatter.load(str(path))
        return {
            "content": post.content,
            "metadata": dict(post.metadata),
            "exists": True,
        }
    except Exception:
        # Fallback: read as plain text
        return {
            "content": path.read_text(encoding="utf-8"),
            "metadata": {},
            "exists": True,
        }


def write_md(
    file_path: str | Path,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write a markdown file with YAML frontmatter.

    Args:
        file_path: Path to write the .md file to.
        content: Markdown body content.
        metadata: Optional YAML frontmatter dict.

    Returns:
        Path to the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    post = frontmatter.Post(content)
    if metadata:
        post.metadata.update(metadata)

    with open(path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    return path


def create_artifact_metadata(
    node: str,
    week_id: str = "",
    topic_id: str = "",
    model_used: str = "",
    status: str = "created",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standard metadata dict for an artifact.

    Follows the frontmatter contract from PRD §6.2.
    """
    now = datetime.now(timezone.utc).isoformat()
    meta: dict[str, Any] = {
        "node": node,
        "created_at": now,
        "updated_at": now,
        "version": 1,
        "status": status,
    }

    if week_id:
        meta["week"] = week_id
    if topic_id:
        meta["id"] = topic_id
    if model_used:
        meta["model_used"] = model_used
    if extra:
        meta.update(extra)

    return meta


def extract_content_preview(content: str, max_chars: int = 500) -> str:
    """Extract a plain-text preview from markdown content.

    Strips headers, formatting, and truncates to max_chars.
    """
    lines = content.strip().split("\n")
    preview_lines = []

    for line in lines:
        # Skip empty lines and headers
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("---"):
            continue
        # Remove markdown formatting
        cleaned = stripped.lstrip("*_~`>- ")
        if cleaned:
            preview_lines.append(cleaned)

    preview = " ".join(preview_lines)
    if len(preview) > max_chars:
        preview = preview[:max_chars].rsplit(" ", 1)[0] + "..."

    return preview


def count_tokens_estimate(text: str) -> int:
    """Rough token count estimate (1 token ≈ 4 characters).

    This is a fast approximation, not an exact count.
    """
    return len(text) // 4
