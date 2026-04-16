"""SQLite database manager for ContentForge.

Provides indexing, state tracking, and full-text search
across the file-based memory system.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DatabaseManager:
    """SQLite database for indexing and state management.

    Maintains an index of all artifacts, pipeline run history,
    and provides full-text search across past weeks' content.

    Usage:
        db = DatabaseManager(db_path="./data/pipeline.db")
        db.initialize()
        db.index_artifact("2026-W16", "01_research", "parsed_topics.md", {...})
        results = db.search("Claude 4 capabilities", limit=5)
    """

    def __init__(self, db_path: str | Path = "./data/pipeline.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def initialize(self) -> None:
        """Create all tables if they don't exist."""
        conn = self._get_conn()

        conn.executescript("""
            -- Artifact index: tracks all .md files
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                filename TEXT NOT NULL,
                topic_id TEXT DEFAULT '',
                node TEXT DEFAULT '',
                model_used TEXT DEFAULT '',
                version INTEGER DEFAULT 1,
                token_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'created',
                file_path TEXT NOT NULL,
                content_preview TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(week_id, phase, filename, topic_id)
            );

            -- Pipeline runs: history of pipeline executions
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                current_node TEXT DEFAULT '',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                state_json TEXT DEFAULT '{}',
                error TEXT DEFAULT ''
            );

            -- Node executions: history of individual node runs
            CREATE TABLE IF NOT EXISTS node_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER REFERENCES pipeline_runs(id),
                week_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                topic_id TEXT DEFAULT '',
                model_used TEXT DEFAULT '',
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                latency_ms REAL DEFAULT 0.0,
                status TEXT DEFAULT 'success',
                error TEXT DEFAULT '',
                started_at TEXT NOT NULL,
                completed_at TEXT
            );

            -- Full-text search index
            CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
                week_id, phase, filename, topic_id, content_preview,
                content='artifacts',
                content_rowid='id'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
                INSERT INTO artifacts_fts(rowid, week_id, phase, filename, topic_id, content_preview)
                VALUES (new.id, new.week_id, new.phase, new.filename, new.topic_id, new.content_preview);
            END;

            CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
                INSERT INTO artifacts_fts(artifacts_fts, rowid, week_id, phase, filename, topic_id, content_preview)
                VALUES('delete', old.id, old.week_id, old.phase, old.filename, old.topic_id, old.content_preview);
            END;

            CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
                INSERT INTO artifacts_fts(artifacts_fts, rowid, week_id, phase, filename, topic_id, content_preview)
                VALUES('delete', old.id, old.week_id, old.phase, old.filename, old.topic_id, old.content_preview);
                INSERT INTO artifacts_fts(rowid, week_id, phase, filename, topic_id, content_preview)
                VALUES (new.id, new.week_id, new.phase, new.filename, new.topic_id, new.content_preview);
            END;

            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_artifacts_week ON artifacts(week_id);
            CREATE INDEX IF NOT EXISTS idx_artifacts_phase ON artifacts(phase);
            CREATE INDEX IF NOT EXISTS idx_artifacts_topic ON artifacts(topic_id);
            CREATE INDEX IF NOT EXISTS idx_node_exec_week ON node_executions(week_id);
            CREATE INDEX IF NOT EXISTS idx_node_exec_node ON node_executions(node_name);
        """)
        conn.commit()

    def index_artifact(
        self,
        week_id: str,
        phase: str,
        filename: str,
        file_path: str,
        topic_id: str = "",
        node: str = "",
        model_used: str = "",
        version: int = 1,
        token_count: int = 0,
        content_preview: str = "",
    ) -> int:
        """Index a file artifact in the database.

        Returns the artifact row ID.
        """
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()

        cursor = conn.execute(
            """
            INSERT INTO artifacts (
                week_id, phase, filename, topic_id, node, model_used,
                version, token_count, file_path, content_preview,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_id, phase, filename, topic_id)
            DO UPDATE SET
                version = excluded.version,
                token_count = excluded.token_count,
                content_preview = excluded.content_preview,
                model_used = excluded.model_used,
                updated_at = excluded.updated_at
            """,
            (
                week_id, phase, filename, topic_id, node, model_used,
                version, token_count, file_path, content_preview[:500],
                now, now,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0

    def log_node_execution(
        self,
        week_id: str,
        node_name: str,
        run_id: int | None = None,
        topic_id: str = "",
        model_used: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        status: str = "success",
        error: str = "",
    ) -> int:
        """Log a node execution to the database."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()

        cursor = conn.execute(
            """
            INSERT INTO node_executions (
                run_id, week_id, node_name, topic_id, model_used,
                input_tokens, output_tokens, latency_ms, status, error,
                started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, week_id, node_name, topic_id, model_used,
                input_tokens, output_tokens, latency_ms, status, error,
                now, now,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0

    def start_pipeline_run(self, week_id: str) -> int:
        """Record the start of a pipeline run. Returns the run ID."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()

        cursor = conn.execute(
            "INSERT INTO pipeline_runs (week_id, status, started_at) VALUES (?, 'running', ?)",
            (week_id, now),
        )
        conn.commit()
        return cursor.lastrowid or 0

    def complete_pipeline_run(
        self,
        run_id: int,
        status: str = "completed",
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        error: str = "",
    ) -> None:
        """Record the completion of a pipeline run."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE pipeline_runs SET
                status = ?, completed_at = ?, total_tokens = ?,
                total_cost_usd = ?, error = ?
            WHERE id = ?
            """,
            (status, now, total_tokens, total_cost_usd, error, run_id),
        )
        conn.commit()

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Full-text search across all indexed artifacts.

        Args:
            query: Search query string.
            limit: Max results to return.

        Returns:
            List of matching artifact dicts.
        """
        conn = self._get_conn()

        rows = conn.execute(
            """
            SELECT a.*, rank
            FROM artifacts_fts fts
            JOIN artifacts a ON a.id = fts.rowid
            WHERE artifacts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

        return [dict(row) for row in rows]

    def get_artifacts_for_week(self, week_id: str) -> list[dict[str, Any]]:
        """Get all artifacts for a specific week."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE week_id = ? ORDER BY phase, filename",
            (week_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_pipeline_runs(self, week_id: str = "") -> list[dict[str, Any]]:
        """Get pipeline run history, optionally filtered by week."""
        conn = self._get_conn()
        if week_id:
            rows = conn.execute(
                "SELECT * FROM pipeline_runs WHERE week_id = ? ORDER BY started_at DESC",
                (week_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 20"
            ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
