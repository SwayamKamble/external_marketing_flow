"""File-based memory manager for ContentForge.

Every artifact is saved as a .md file with YAML frontmatter.
This module handles reading, writing, versioning, and searching
across the file-based memory system.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter
from rich.console import Console

console = Console()


class FileMemory:
    """File-based memory manager for pipeline artifacts.

    All content is stored as markdown files with YAML frontmatter
    in a structured directory layout under data/.

    Usage:
        memory = FileMemory(data_dir="./data")
        memory.write_artifact(
            week_id="2026-W16",
            phase="01_research",
            filename="parsed_topics.md",
            content="# Parsed Topics\\n...",
            metadata={"node": "research_parser", "model_used": "gpt-5-chat"},
        )
        content = memory.read_artifact("2026-W16", "01_research", "parsed_topics.md")
    """

    def __init__(self, data_dir: str | Path = "./data"):
        self.data_dir = Path(data_dir)
        self._ensure_base_dirs()

    def _ensure_base_dirs(self) -> None:
        """Create base directory structure if it doesn't exist."""
        dirs = [
            self.data_dir / "brand",
            self.data_dir / "weeks",
            self.data_dir / "logs",
            self.data_dir / "templates",
            self.data_dir / "templates" / "carousel_react_templates",
            self.data_dir / "templates" / "caption_templates",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def ensure_week_dirs(self, week_id: str) -> Path:
        """Create the full directory structure for a week.

        Args:
            week_id: Week identifier (e.g., "2026-W16").

        Returns:
            Path to the week directory.
        """
        week_dir = self.data_dir / "weeks" / week_id
        subdirs = [
            "01_research",
            "02_scoring",
            "03_plan",
            "04_deep_research",
            "05_content",
            "06_exports",
        ]
        for sub in subdirs:
            (week_dir / sub).mkdir(parents=True, exist_ok=True)

        # Create week metadata file if it doesn't exist
        meta_path = week_dir / "_week_meta.md"
        if not meta_path.exists():
            self.write_artifact(
                week_id=week_id,
                phase="",
                filename="_week_meta.md",
                content=f"# Week {week_id}\n\nStatus: started\n",
                metadata={
                    "week": week_id,
                    "status": "started",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Create log file
        log_path = week_dir / "_week_log.md"
        if not log_path.exists():
            self._write_file(
                log_path,
                f"# Activity Log — {week_id}\n\n",
                metadata={"week": week_id, "type": "log"},
            )

        return week_dir

    def write_artifact(
        self,
        week_id: str,
        phase: str,
        filename: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        topic_id: str | None = None,
    ) -> Path:
        """Write a markdown artifact with YAML frontmatter.

        Args:
            week_id: Week identifier (e.g., "2026-W16").
            phase: Pipeline phase folder (e.g., "01_research", "05_content").
            filename: Name of the .md file.
            content: Markdown content body.
            metadata: YAML frontmatter dict.
            topic_id: Optional topic ID for content-phase files.

        Returns:
            Path to the written file.
        """
        # Build the file path
        if phase:
            base_dir = self.data_dir / "weeks" / week_id / phase
        else:
            base_dir = self.data_dir / "weeks" / week_id

        if topic_id:
            base_dir = base_dir / topic_id

        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / filename

        # Build metadata with defaults
        meta = {
            "week": week_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "version": 1,
        }
        if metadata:
            meta.update(metadata)

        # Check if file exists — increment version
        if file_path.exists():
            existing = self.read_raw(file_path)
            if existing and hasattr(existing, "metadata"):
                old_version = existing.metadata.get("version", 1)
                meta["version"] = old_version + 1
                meta["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._write_file(file_path, content, meta)
        return file_path

    def read_artifact(
        self,
        week_id: str,
        phase: str,
        filename: str,
        topic_id: str | None = None,
    ) -> dict[str, Any]:
        """Read a markdown artifact and return content + metadata.

        Args:
            week_id: Week identifier.
            phase: Pipeline phase folder.
            filename: Name of the .md file.
            topic_id: Optional topic ID.

        Returns:
            Dict with "content" (str) and "metadata" (dict).
        """
        if phase:
            base_dir = self.data_dir / "weeks" / week_id / phase
        else:
            base_dir = self.data_dir / "weeks" / week_id

        if topic_id:
            base_dir = base_dir / topic_id

        file_path = base_dir / filename

        if not file_path.exists():
            return {"content": "", "metadata": {}, "exists": False}

        post = self.read_raw(file_path)
        return {
            "content": post.content if post else "",
            "metadata": dict(post.metadata) if post else {},
            "exists": True,
        }

    def read_context(
        self,
        week_id: str,
        phase: str,
        topic_id: str | None = None,
    ) -> dict[str, Any]:
        """Read ALL .md files for a given phase/topic as context.

        Returns a dict mapping filename → {content, metadata}.
        Used by agents to understand what came before.
        """
        if phase:
            base_dir = self.data_dir / "weeks" / week_id / phase
        else:
            base_dir = self.data_dir / "weeks" / week_id

        if topic_id:
            base_dir = base_dir / topic_id

        if not base_dir.exists():
            return {}

        context = {}
        for file_path in sorted(base_dir.rglob("*.md")):
            rel = file_path.relative_to(base_dir)
            post = self.read_raw(file_path)
            if post:
                context[str(rel)] = {
                    "content": post.content,
                    "metadata": dict(post.metadata),
                }

        return context

    def get_brand_context(self) -> dict[str, Any]:
        """Read all brand/*.md files and return unified brand context.

        Returns:
            Dict mapping filename → content string.
        """
        brand_dir = self.data_dir / "brand"
        context = {}

        if not brand_dir.exists():
            return context

        for file_path in sorted(brand_dir.glob("*.md")):
            post = self.read_raw(file_path)
            if post:
                context[file_path.stem] = post.content

        return context

    def version_artifact(
        self,
        week_id: str,
        phase: str,
        filename: str,
        new_content: str,
        change_reason: str = "",
        topic_id: str | None = None,
    ) -> Path:
        """Create a new version of an existing artifact.

        Increments the version number in frontmatter and logs the change.
        """
        existing = self.read_artifact(week_id, phase, filename, topic_id)
        meta = existing.get("metadata", {})
        old_version = meta.get("version", 1)

        meta["version"] = old_version + 1
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Add to edit history in metadata
        edit_history = meta.get("edit_history", [])
        edit_history.append({
            f"v{old_version + 1}": f"{datetime.now(timezone.utc).isoformat()} ({change_reason})"
        })
        meta["edit_history"] = edit_history

        return self.write_artifact(
            week_id=week_id,
            phase=phase,
            filename=filename,
            content=new_content,
            metadata=meta,
            topic_id=topic_id,
        )

    def get_edit_history(self, week_id: str, topic_id: str) -> str:
        """Read the edit history for a topic."""
        result = self.read_artifact(
            week_id=week_id,
            phase="05_content",
            filename="edit_history.md",
            topic_id=topic_id,
        )
        return result.get("content", "")

    def append_log(self, week_id: str, message: str) -> None:
        """Append a line to the week's activity log."""
        log_path = self.data_dir / "weeks" / week_id / "_week_log.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def list_files(self, week_id: str, phase: str = "") -> list[str]:
        """List all .md files in a week/phase directory."""
        if phase:
            base_dir = self.data_dir / "weeks" / week_id / phase
        else:
            base_dir = self.data_dir / "weeks" / week_id

        if not base_dir.exists():
            return []

        return [
            str(p.relative_to(base_dir))
            for p in sorted(base_dir.rglob("*.md"))
        ]

    def get_file_tree(self, week_id: str) -> dict[str, Any]:
        """Get the full file tree for a week as a nested dict."""
        week_dir = self.data_dir / "weeks" / week_id
        if not week_dir.exists():
            return {}
        return self._build_tree(week_dir)

    # ── Private Methods ──

    def read_raw(self, file_path: Path) -> frontmatter.Post | None:
        """Read a raw frontmatter Post from a file."""
        try:
            return frontmatter.load(str(file_path))
        except Exception as e:
            console.print(f"[red]Error reading {file_path}: {e}[/red]")
            return None

    def _write_file(
        self,
        file_path: Path,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Write content with YAML frontmatter to a file."""
        post = frontmatter.Post(content)
        if metadata:
            post.metadata.update(metadata)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def _build_tree(self, directory: Path) -> dict[str, Any]:
        """Recursively build a file tree dict."""
        tree: dict[str, Any] = {}
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                tree[item.name] = self._build_tree(item)
            else:
                tree[item.name] = {
                    "size_bytes": item.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        item.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
        return tree
