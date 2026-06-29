"""SQLite-backed long-term memory store for windowsOS-coworker.

Three tables
------------
sessions  : one row per chat session (id, started_at, ended_at, summary)
messages  : every conversation turn   (session_id FK, role, content, ts)
facts     : persistent key/value facts the agent learns across sessions

The module is intentionally synchronous (sqlite3 is sync) and thread-safe via
a single module-level lock.  The async chat loop calls the public helpers from
a ``asyncio.get_event_loop().run_in_executor`` wrapper so the DB is never
blocked on the event loop.
"""

from __future__ import annotations

import datetime
import sqlite3
import threading
from pathlib import Path
from typing import Any

import config

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------


def _get_conn() -> sqlite3.Connection:
    """Return (and lazily create) the shared SQLite connection.

    The connection is opened with ``check_same_thread=False`` because the
    module uses its own ``_lock`` for serialisation.

    Returns:
        The open ``sqlite3.Connection``.
    """
    global _conn
    if _conn is None:
        db_path: Path = config.MEMORY_DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")  # concurrent reads while writing
        _conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they do not already exist.

    Args:
        conn: The open database connection to initialise.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            started_at  TEXT NOT NULL,
            ended_at    TEXT,
            summary     TEXT,
            model       TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content     TEXT NOT NULL,
            ts          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id);

        CREATE TABLE IF NOT EXISTS facts (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'general',
            source      TEXT,          -- which session_id introduced this fact
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def create_session(session_id: str, model: str = "") -> None:
    """Persist the start of a new session.

    Args:
        session_id: Unique 8-char session identifier (from ``uuid4()[:8]``).
        model: Model name in use for this session.
    """
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO sessions(id, started_at, model) VALUES(?,?,?)",
            (session_id, now, model),
        )
        conn.commit()


def end_session(session_id: str, summary: str = "") -> None:
    """Mark a session as ended and optionally store a summary.

    Args:
        session_id: The session to close.
        summary: A short natural-language summary of what was done this session.
    """
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "UPDATE sessions SET ended_at=?, summary=? WHERE id=?",
            (now, summary or None, session_id),
        )
        conn.commit()


def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    """Return recent sessions, newest first.

    Args:
        limit: Maximum number of sessions to return.

    Returns:
        List of session dicts with keys: id, started_at, ended_at, summary, model.
    """
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------


def save_message(session_id: str, role: str, content: str) -> None:
    """Append a single conversation turn to the messages table.

    Args:
        session_id: The owning session.
        role: 'user' | 'assistant' | 'system'.
        content: The raw message content string.
    """
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO messages(session_id, role, content, ts) VALUES(?,?,?,?)",
            (session_id, role, content, now),
        )
        conn.commit()


def save_messages(session_id: str, messages: list[dict[str, str]]) -> None:
    """Bulk-save a list of message dicts to the messages table.

    Only messages with ``role`` in ``{'user', 'assistant', 'system'}`` are saved.

    Args:
        session_id: The owning session.
        messages: List of ``{"role": ..., "content": ...}`` dicts.
    """
    now = _now()
    valid_roles = {"user", "assistant", "system"}
    rows = [
        (session_id, m["role"], m["content"], now)
        for m in messages
        if m.get("role") in valid_roles and m.get("content")
    ]
    if not rows:
        return
    with _lock:
        conn = _get_conn()
        conn.executemany(
            "INSERT INTO messages(session_id, role, content, ts) VALUES(?,?,?,?)",
            rows,
        )
        conn.commit()


def load_session_messages(session_id: str) -> list[dict[str, str]]:
    """Load all messages for a session in chronological order.

    Args:
        session_id: The session whose history to load.

    Returns:
        List of ``{"role": ..., "content": ...}`` dicts, oldest first.
    """
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def load_recent_messages(
    limit: int = 50,
    session_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load recent messages across all sessions (or one specific session).

    Args:
        limit: Max number of messages to return.
        session_id: If given, restrict to that session only.

    Returns:
        List of message dicts including ``session_id`` and ``ts``.
    """
    with _lock:
        conn = _get_conn()
        if session_id:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return list(reversed([dict(r) for r in rows]))


# ---------------------------------------------------------------------------
# Facts helpers
# ---------------------------------------------------------------------------


def upsert_fact(
    key: str,
    value: str,
    category: str = "general",
    source: str = "",
) -> None:
    """Insert or update a persistent fact.

    Facts are keyed by ``key`` (case-sensitive).  Calling this with an
    existing key silently updates ``value``, ``category``, ``source``, and
    ``updated_at``.

    Args:
        key: Unique fact identifier, e.g. ``"user.preferred_drive"``.
        value: The fact value, e.g. ``"D:"``.
        category: Grouping label, e.g. ``"preference"``, ``"system"``.
        source: Session ID that introduced or last updated this fact.
    """
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO facts(key, value, category, source, created_at, updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                category=excluded.category,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            (key, value, category, source or None, now, now),
        )
        conn.commit()


def get_fact(key: str) -> str | None:
    """Retrieve a single fact value by key.

    Args:
        key: The fact key to look up.

    Returns:
        The fact value string, or ``None`` if not found.
    """
    with _lock:
        conn = _get_conn()
        row = conn.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def list_facts(category: str | None = None) -> list[dict[str, Any]]:
    """Return all facts, optionally filtered by category.

    Args:
        category: If given, return only facts with this category.

    Returns:
        List of fact dicts with keys: key, value, category, source, created_at, updated_at.
    """
    with _lock:
        conn = _get_conn()
        if category:
            rows = conn.execute(
                "SELECT * FROM facts WHERE category=? ORDER BY key",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM facts ORDER BY category, key").fetchall()
    return [dict(r) for r in rows]


def delete_fact(key: str) -> bool:
    """Delete a fact by key.

    Args:
        key: The fact key to delete.

    Returns:
        True if the key existed and was deleted, False otherwise.
    """
    with _lock:
        conn = _get_conn()
        cur = conn.execute("DELETE FROM facts WHERE key=?", (key,))
        conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Context window helper
# ---------------------------------------------------------------------------


def build_memory_context(
    current_session_id: str,
    max_recent_messages: int = 20,
    include_facts: bool = True,
) -> str:
    """Build a compact memory context string to inject into agent prompts.

    Returns a short markdown-ish block summarising:
    - Persistent facts (all categories)
    - The last ``max_recent_messages`` turns of this session

    This is intentionally small so it does not bloat the context window.

    Args:
        current_session_id: Session ID of the currently running session.
        max_recent_messages: How many recent messages to include.
        include_facts: Whether to include persistent facts section.

    Returns:
        A multi-line string suitable for prepending to an agent system prompt.
    """
    parts: list[str] = []

    if include_facts:
        facts = list_facts()
        if facts:
            lines = ["## Persistent facts about this system / user"]
            for f in facts:
                lines.append(f"- [{f['category']}] {f['key']} = {f['value']}")
            parts.append("\n".join(lines))

    recent = load_recent_messages(
        limit=max_recent_messages, session_id=current_session_id
    )
    if recent:
        lines = [f"## Last {len(recent)} turns this session"]
        for m in recent:
            speaker = "User" if m["role"] == "user" else "Assistant"
            # Truncate very long messages to keep context manageable
            snippet = m["content"][:300] + ("…" if len(m["content"]) > 300 else "")
            lines.append(f"{speaker}: {snippet}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Stats / introspection
# ---------------------------------------------------------------------------


def get_stats() -> dict[str, int]:
    """Return high-level counts for monitoring.

    Returns:
        Dict with keys: total_sessions, total_messages, total_facts.
    """
    with _lock:
        conn = _get_conn()
        sessions_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        messages_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        facts_count = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
    return {
        "total_sessions": sessions_count,
        "total_messages": messages_count,
        "total_facts": facts_count,
    }


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _now() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.datetime.now(datetime.UTC).isoformat()  # noqa: UP017


def close() -> None:
    """Close the shared database connection (call at app shutdown)."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None
