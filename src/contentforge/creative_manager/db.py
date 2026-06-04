"""SQLite database for Creative Manager sessions.

Completely separate from the pipeline database (pipeline.db).
Stores sessions, discovered topics, and weekly content plans.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CreativeManagerDB:
    """Standalone SQLite database for Creative Manager.

    Database file: data/creative_manager.db
    Fully independent from pipeline.db.
    """

    def __init__(self, db_path: str | Path = "./data/creative_manager.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def initialize(self) -> None:
        """Create all tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                week_id TEXT NOT NULL,
                niche TEXT DEFAULT 'AI & Tech',
                status TEXT DEFAULT 'input_needed',
                research_prompt TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                category TEXT DEFAULT '',
                source TEXT DEFAULT '',
                educational_angle TEXT DEFAULT '',
                why_it_works TEXT DEFAULT '',
                teaching_points TEXT DEFAULT '[]',
                best_platforms TEXT DEFAULT '[]',
                engagement_scores TEXT DEFAULT '{}',
                platform_angles TEXT DEFAULT '[]',
                selected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS content_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                day TEXT NOT NULL,
                date TEXT DEFAULT '',
                platform TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                topic_title TEXT DEFAULT '',
                content_format TEXT DEFAULT 'carousel',
                intent TEXT DEFAULT 'educate',
                hook TEXT DEFAULT '',
                angle TEXT DEFAULT '',
                teaching_goal TEXT DEFAULT '',
                reasoning TEXT DEFAULT '',
                writing_prompt TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            );

            CREATE INDEX IF NOT EXISTS idx_topics_session ON topics(session_id);
            CREATE INDEX IF NOT EXISTS idx_plan_session ON content_plan(session_id);

            CREATE TABLE IF NOT EXISTS quick_prompt_sessions (
                id TEXT PRIMARY KEY,
                user_prompt TEXT NOT NULL,
                structured_intent TEXT DEFAULT '{}',
                research_prompt TEXT DEFAULT '',
                series_plan TEXT DEFAULT '{}',
                production_prompt TEXT DEFAULT '',
                status TEXT DEFAULT 'prompt_entered',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        # Safe migration for writing_prompt column
        try:
            conn.execute("ALTER TABLE content_plan ADD COLUMN writing_prompt TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        # Safe migrations for new quick prompt pipeline columns
        for col, default in [
            ("content_filter", "'educational'"),
            ("discovery_prompt", "''"),
            ("discovered_topics", "'[]'"),
            ("selected_topic", "'{}'"),
            ("deep_research_prompt", "''"),
            ("chat_history", "'[]'"),
        ]:
            try:
                conn.execute(f"ALTER TABLE quick_prompt_sessions ADD COLUMN {col} TEXT DEFAULT {default}")
            except sqlite3.OperationalError:
                pass
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Session CRUD ──

    def create_session(self, session_id: str, week_id: str, niche: str = "AI & Tech", research_prompt: str = "") -> dict:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, week_id, niche, status, research_prompt, created_at, updated_at) VALUES (?, ?, ?, 'input_needed', ?, ?, ?)",
            (session_id, week_id, niche, research_prompt, now, now),
        )
        conn.commit()
        return {"id": session_id, "week_id": week_id, "niche": niche, "status": "input_needed", "created_at": now}

    def get_session(self, session_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def update_session_status(self, session_id: str, status: str) -> None:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?", (status, now, session_id))
        conn.commit()

    def list_sessions(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ── Topics CRUD ──

    def save_topics(self, session_id: str, topics: list[dict]) -> None:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        # Clear existing topics for this session
        conn.execute("DELETE FROM topics WHERE session_id = ?", (session_id,))
        for t in topics:
            conn.execute(
                """INSERT INTO topics (id, session_id, title, summary, category, source,
                   educational_angle, why_it_works, teaching_points, best_platforms,
                   engagement_scores, platform_angles, selected, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t["id"], session_id, t.get("title", ""), t.get("summary", ""),
                    t.get("category", ""), t.get("source", ""),
                    t.get("educational_angle", ""), t.get("why_it_works", ""),
                    json.dumps(t.get("teaching_points", [])),
                    json.dumps(t.get("best_platforms", [])),
                    json.dumps(t.get("engagement_scores", {})),
                    json.dumps(t.get("platform_angles", [])),
                    1 if t.get("selected") else 0,
                    now,
                ),
            )
        conn.commit()

    def get_topics(self, session_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM topics WHERE session_id = ? ORDER BY rowid", (session_id,)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["teaching_points"] = json.loads(d.get("teaching_points") or "[]")
            d["best_platforms"] = json.loads(d.get("best_platforms") or "[]")
            d["engagement_scores"] = json.loads(d.get("engagement_scores") or "{}")
            d["platform_angles"] = json.loads(d.get("platform_angles") or "[]")
            d["selected"] = bool(d.get("selected"))
            results.append(d)
        return results

    def select_topics(self, session_id: str, topic_ids: list[str]) -> None:
        conn = self._get_conn()
        conn.execute("UPDATE topics SET selected = 0 WHERE session_id = ?", (session_id,))
        for tid in topic_ids:
            conn.execute("UPDATE topics SET selected = 1 WHERE id = ? AND session_id = ?", (tid, session_id))
        conn.commit()

    # ── Content Plan CRUD ──

    def save_plan(self, session_id: str, plan: list[dict]) -> None:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("DELETE FROM content_plan WHERE session_id = ?", (session_id,))
        for p in plan:
            conn.execute(
                """INSERT INTO content_plan (session_id, day, date, platform, topic_id, topic_title,
                   content_format, intent, hook, angle, teaching_goal, reasoning, writing_prompt, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id, p.get("day", ""), p.get("date", ""),
                    p.get("platform", ""), p.get("topic_id", ""), p.get("topic_title", ""),
                    p.get("content_format", "carousel"), p.get("intent", "educate"),
                    p.get("hook", ""), p.get("angle", ""), p.get("teaching_goal", ""),
                    p.get("reasoning", ""), p.get("writing_prompt", ""), now,
                ),
            )
        conn.commit()

    def get_plan(self, session_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM content_plan WHERE session_id = ? ORDER BY rowid", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    def update_plan_day(self, plan_id: int, updates: dict) -> None:
        conn = self._get_conn()
        allowed = {"platform", "topic_id", "topic_title", "content_format", "intent", "hook", "angle", "teaching_goal", "reasoning", "writing_prompt"}
        sets = []
        vals = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            vals.append(plan_id)
            conn.execute(f"UPDATE content_plan SET {', '.join(sets)} WHERE id = ?", vals)
            conn.commit()

    # ── Quick Prompt Session CRUD ──

    def create_quick_session(
        self,
        session_id: str,
        user_prompt: str = "",
        structured_intent: dict | None = None,
        research_prompt: str = "",
        content_filter: str = "educational",
        discovery_prompt: str = "",
    ) -> dict:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO quick_prompt_sessions
               (id, user_prompt, structured_intent, research_prompt, series_plan,
                production_prompt, status, content_filter, discovery_prompt,
                discovered_topics, selected_topic, deep_research_prompt, chat_history,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, '{}', '', 'created', ?, ?, '[]', '{}', '', '[]', ?, ?)""",
            (
                session_id,
                user_prompt,
                json.dumps(structured_intent or {}),
                research_prompt,
                content_filter,
                discovery_prompt,
                now, now,
            ),
        )
        conn.commit()
        return {
            "id": session_id,
            "user_prompt": user_prompt,
            "content_filter": content_filter,
            "status": "created",
            "created_at": now,
        }

    def get_quick_session(self, session_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM quick_prompt_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["structured_intent"] = json.loads(d.get("structured_intent") or "{}")
        d["series_plan"] = json.loads(d.get("series_plan") or "{}")
        d["discovered_topics"] = json.loads(d.get("discovered_topics") or "[]")
        d["selected_topic"] = json.loads(d.get("selected_topic") or "{}")
        d["chat_history"] = json.loads(d.get("chat_history") or "[]")
        return d

    def update_quick_session(self, session_id: str, **kwargs) -> None:
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        allowed = {
            "user_prompt", "structured_intent", "research_prompt",
            "series_plan", "production_prompt", "status",
            "content_filter", "discovery_prompt", "discovered_topics",
            "selected_topic", "deep_research_prompt", "chat_history",
        }
        json_fields = {"structured_intent", "series_plan", "discovered_topics", "selected_topic", "chat_history"}
        sets = ["updated_at = ?"]
        vals: list[Any] = [now]

        for k, v in kwargs.items():
            if k not in allowed:
                continue
            if k in json_fields:
                sets.append(f"{k} = ?")
                vals.append(json.dumps(v) if not isinstance(v, str) else v)
            else:
                sets.append(f"{k} = ?")
                vals.append(v)

        vals.append(session_id)
        conn.execute(
            f"UPDATE quick_prompt_sessions SET {', '.join(sets)} WHERE id = ?",
            vals,
        )
        conn.commit()

    def list_quick_sessions(self, limit: int = 20) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, user_prompt, status, content_filter, structured_intent,
                      selected_topic, created_at, updated_at
               FROM quick_prompt_sessions ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            si = json.loads(d.get("structured_intent") or "{}")
            d["series_length"] = si.get("series_length", 7)
            d["topic_theme"] = si.get("topic_theme", "")
            d["platform"] = si.get("platform", "instagram")
            # Extract selected topic title
            st = json.loads(d.get("selected_topic") or "{}")
            d["selected_topic_title"] = st.get("title", "") if isinstance(st, dict) else ""
            # Don't include bulky fields in list view
            del d["structured_intent"]
            del d["selected_topic"]
            results.append(d)
        return results
