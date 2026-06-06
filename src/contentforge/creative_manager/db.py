"""SQLite/PostgreSQL database for SocialHQ sessions.

Completely separate from the pipeline database (pipeline.db).
Stores sessions, discovered topics, and weekly content plans.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CreativeManagerDB:
    """Standalone SQLite/PostgreSQL database for SocialHQ.

    Supports SQLite locally and PostgreSQL in production via DATABASE_URL.
    """

    def __init__(self, db_path: str | Path = "./data/creative_manager.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self.db_url = os.getenv("DATABASE_URL")
        self.is_postgres = bool(self.db_url)

    def _get_conn(self):
        if self._conn is None:
            if self.is_postgres:
                try:
                    import pg8000
                    import urllib.parse
                    import ssl
                    import socket
                    url = urllib.parse.urlparse(self.db_url)
                    username = url.username
                    password = url.password
                    database = url.path[1:]
                    hostname = url.hostname
                    port = url.port or 5432
                    
                    # Force DNS resolution to IPv4 to prevent Vercel "Cannot assign requested address" IPv6 connection issues
                    try:
                        addr_info = socket.getaddrinfo(hostname, port, socket.AF_INET, socket.SOCK_STREAM)
                        if addr_info:
                            hostname = addr_info[0][4][0]
                    except Exception:
                        pass
                    
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    self._conn = pg8000.connect(
                        user=username,
                        password=password,
                        host=hostname,
                        port=port,
                        database=database,
                        ssl_context=ssl_context,
                        timeout=5
                    )
                except Exception as e:
                    print(f"DATABASE CONNECTION WARNING: Failed to connect to PostgreSQL database: {e}. Falling back to SQLite.")
                    self.is_postgres = False
                    self._conn = None
            
            if not self.is_postgres or self._conn is None:
                self._conn = sqlite3.connect(str(self.db_path))
                self._conn.row_factory = sqlite3.Row
                if os.getenv("VERCEL") == "1":
                    self._conn.execute("PRAGMA journal_mode=delete")
                else:
                    self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _execute(self, sql: str, params: tuple = (), commit: bool = True) -> list[dict]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            formatted_sql = sql
            if self.is_postgres:
                formatted_sql = sql.replace("?", "%s")
            cursor.execute(formatted_sql, params)
        except Exception as e:
            if self.is_postgres:
                try:
                    self.close()
                    conn = self._get_conn()
                    cursor = conn.cursor()
                    formatted_sql = sql.replace("?", "%s")
                    cursor.execute(formatted_sql, params)
                except Exception as retry_err:
                    raise retry_err
            else:
                raise e
                
        results = []
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                # Map columns to values. Supports both SQLite and PostgreSQL output formats.
                results.append(dict(zip(columns, row)))
                
        if commit:
            conn.commit()
            
        return results

    def initialize(self) -> None:
        """Create all tables if they don't exist."""
        # Force connection establishment to determine is_postgres final state early
        try:
            self._get_conn()
        except Exception:
            pass
            
        id_primary_key = "id SERIAL PRIMARY KEY" if self.is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"
        
        schema = f"""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                week_id TEXT NOT NULL,
                niche TEXT DEFAULT 'AI & Tech',
                status TEXT DEFAULT 'input_needed',
                research_prompt TEXT DEFAULT '',
                user_id TEXT DEFAULT '',
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
                news_date TEXT DEFAULT '',
                educational_angle TEXT DEFAULT '',
                why_it_works TEXT DEFAULT '',
                teaching_points TEXT DEFAULT '[]',
                best_platforms TEXT DEFAULT '[]',
                engagement_scores TEXT DEFAULT '{{}}',
                platform_angles TEXT DEFAULT '[]',
                selected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS content_plan (
                {id_primary_key},
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

            CREATE TABLE IF NOT EXISTS quick_prompt_sessions (
                id TEXT PRIMARY KEY,
                user_prompt TEXT NOT NULL,
                structured_intent TEXT DEFAULT '{{}}',
                research_prompt TEXT DEFAULT '',
                series_plan TEXT DEFAULT '{{}}',
                production_prompt TEXT DEFAULT '',
                status TEXT DEFAULT 'prompt_entered',
                user_id TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """
        
        # Split statements and execute individually
        statements = [s.strip() for s in schema.split(";") if s.strip()]
        for stmt in statements:
            try:
                self._execute(stmt)
            except Exception as e:
                print(f"Schema initialization statement failed: {e}")
                
        # Create indexes
        for idx_stmt in [
            "CREATE INDEX IF NOT EXISTS idx_topics_session ON topics(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_plan_session ON content_plan(session_id)"
        ]:
            try:
                self._execute(idx_stmt)
            except Exception:
                pass
                
        # Run safe migrations
        migrations = [
            ("ALTER TABLE sessions ADD COLUMN user_id TEXT DEFAULT ''", "sessions", "user_id"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN user_id TEXT DEFAULT ''", "quick_prompt_sessions", "user_id"),
            ("ALTER TABLE content_plan ADD COLUMN writing_prompt TEXT DEFAULT ''", "content_plan", "writing_prompt"),
            ("ALTER TABLE topics ADD COLUMN news_date TEXT DEFAULT ''", "topics", "news_date"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN content_filter TEXT DEFAULT 'educational'", "quick_prompt_sessions", "content_filter"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN discovery_prompt TEXT DEFAULT ''", "quick_prompt_sessions", "discovery_prompt"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN discovered_topics TEXT DEFAULT '[]'", "quick_prompt_sessions", "discovered_topics"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN selected_topic TEXT DEFAULT '{}'", "quick_prompt_sessions", "selected_topic"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN deep_research_prompt TEXT DEFAULT ''", "quick_prompt_sessions", "deep_research_prompt"),
            ("ALTER TABLE quick_prompt_sessions ADD COLUMN chat_history TEXT DEFAULT '[]'", "quick_prompt_sessions", "chat_history"),
        ]
        
        for alter_sql, table, column in migrations:
            try:
                self._execute(alter_sql)
            except Exception:
                pass

    # ── User and Authentication CRUD ──

    def create_user(self, username: str, password_hash: str) -> str:
        import uuid
        user_id = f"u_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        self._execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, now),
        )
        return user_id

    def get_user_by_username(self, username: str) -> dict | None:
        rows = self._execute("SELECT * FROM users WHERE username = ?", (username,))
        return rows[0] if rows else None

    def create_user_session(self, token: str, user_id: str, expires_at: str) -> None:
        self._execute(
            "INSERT INTO user_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )

    def get_user_id_by_token(self, token: str) -> str | None:
        rows = self._execute("SELECT user_id, expires_at FROM user_sessions WHERE token = ?", (token,))
        if not rows:
            return None
        row = rows[0]
        expires_at_str = row["expires_at"]
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                self.delete_user_session(token)
                return None
        except Exception:
            return None
        return row["user_id"]

    def delete_user_session(self, token: str) -> None:
        self._execute("DELETE FROM user_sessions WHERE token = ?", (token,))

    # ── Session CRUD ──

    def create_session(self, session_id: str, week_id: str, niche: str = "AI & Tech", research_prompt: str = "", user_id: str = "") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        self._execute(
            "INSERT INTO sessions (id, week_id, niche, status, research_prompt, user_id, created_at, updated_at) VALUES (?, ?, ?, 'input_needed', ?, ?, ?, ?)",
            (session_id, week_id, niche, research_prompt, user_id, now, now),
        )
        return {"id": session_id, "week_id": week_id, "niche": niche, "status": "input_needed", "created_at": now, "user_id": user_id}

    def get_session(self, session_id: str, user_id: str = "") -> dict | None:
        if user_id:
            rows = self._execute("SELECT * FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        else:
            rows = self._execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return rows[0] if rows else None

    def update_session_status(self, session_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._execute("UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?", (status, now, session_id))

    def list_sessions(self, user_id: str = "", limit: int = 20) -> list[dict]:
        if user_id:
            rows = self._execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        else:
            rows = self._execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        return rows

    # ── Topics CRUD ──

    def save_topics(self, session_id: str, topics: list[dict]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._execute("DELETE FROM topics WHERE session_id = ?", (session_id,))
        for t in topics:
            self._execute(
                """INSERT INTO topics (id, session_id, title, summary, category, source, news_date,
                   educational_angle, why_it_works, teaching_points, best_platforms,
                   engagement_scores, platform_angles, selected, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t["id"], session_id, t.get("title", ""), t.get("summary", ""),
                    t.get("category", ""), t.get("source", ""), t.get("news_date", ""),
                    t.get("educational_angle", ""), t.get("why_it_works", ""),
                    json.dumps(t.get("teaching_points", [])),
                    json.dumps(t.get("best_platforms", [])),
                    json.dumps(t.get("engagement_scores", {})),
                    json.dumps(t.get("platform_angles", [])),
                    1 if t.get("selected") else 0,
                    now,
                ),
            )

    def get_topics(self, session_id: str) -> list[dict]:
        rows = self._execute("SELECT * FROM topics WHERE session_id = ?", (session_id,))
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
        self._execute("UPDATE topics SET selected = 0 WHERE session_id = ?", (session_id,))
        for tid in topic_ids:
            self._execute("UPDATE topics SET selected = 1 WHERE id = ? AND session_id = ?", (tid, session_id))

    # ── Content Plan CRUD ──

    def save_plan(self, session_id: str, plan: list[dict]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._execute("DELETE FROM content_plan WHERE session_id = ?", (session_id,))
        for p in plan:
            self._execute(
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

    def get_plan(self, session_id: str) -> list[dict]:
        return self._execute("SELECT * FROM content_plan WHERE session_id = ?", (session_id,))

    def update_plan_day(self, plan_id: int, updates: dict) -> None:
        allowed = {"platform", "topic_id", "topic_title", "content_format", "intent", "hook", "angle", "teaching_goal", "reasoning", "writing_prompt"}
        sets = []
        vals = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                vals.append(v)
        if sets:
            vals.append(plan_id)
            self._execute(f"UPDATE content_plan SET {', '.join(sets)} WHERE id = ?", tuple(vals))

    # ── Quick Prompt Session CRUD ──

    def create_quick_session(
        self,
        session_id: str,
        user_prompt: str = "",
        structured_intent: dict | None = None,
        research_prompt: str = "",
        content_filter: str = "educational",
        discovery_prompt: str = "",
        user_id: str = "",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        self._execute(
            """INSERT INTO quick_prompt_sessions
               (id, user_prompt, structured_intent, research_prompt, series_plan,
                production_prompt, status, content_filter, discovery_prompt,
                discovered_topics, selected_topic, deep_research_prompt, chat_history,
                user_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, '{}', '', 'created', ?, ?, '[]', '{}', '', '[]', ?, ?, ?)""",
            (
                session_id,
                user_prompt,
                json.dumps(structured_intent or {}),
                research_prompt,
                content_filter,
                discovery_prompt,
                user_id,
                now, now,
            ),
        )
        return {
            "id": session_id,
            "user_prompt": user_prompt,
            "content_filter": content_filter,
            "status": "created",
            "created_at": now,
            "user_id": user_id,
        }

    def get_quick_session(self, session_id: str, user_id: str = "") -> dict | None:
        if user_id:
            rows = self._execute("SELECT * FROM quick_prompt_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        else:
            rows = self._execute("SELECT * FROM quick_prompt_sessions WHERE id = ?", (session_id,))
        if not rows:
            return None
        d = rows[0]
        d["structured_intent"] = json.loads(d.get("structured_intent") or "{}")
        d["series_plan"] = json.loads(d.get("series_plan") or "{}")
        d["discovered_topics"] = json.loads(d.get("discovered_topics") or "[]")
        d["selected_topic"] = json.loads(d.get("selected_topic") or "{}")
        d["chat_history"] = json.loads(d.get("chat_history") or "[]")
        return d

    def update_quick_session(self, session_id: str, **kwargs) -> None:
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
        self._execute(
            f"UPDATE quick_prompt_sessions SET {', '.join(sets)} WHERE id = ?",
            tuple(vals),
        )

    def list_quick_sessions(self, user_id: str = "", limit: int = 20) -> list[dict]:
        if user_id:
            rows = self._execute(
                """SELECT id, user_prompt, status, content_filter, structured_intent,
                          selected_topic, created_at, updated_at
                   FROM quick_prompt_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit),
            )
        else:
            rows = self._execute(
                """SELECT id, user_prompt, status, content_filter, structured_intent,
                          selected_topic, created_at, updated_at
                   FROM quick_prompt_sessions ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            )
        results = []
        for r in rows:
            d = r
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
