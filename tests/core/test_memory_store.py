"""Unit tests for core/memory_store.py.

All tests use tmp_path to redirect MEMORY_DB_PATH so they never touch the
real sessions/memory.db file.  The module-level ``_conn`` is reset between
tests via a fixture that patches config and re-imports the module state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import config


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Redirect MEMORY_DB_PATH to a fresh temp file and reset the connection."""
    monkeypatch.setattr(config, "MEMORY_DB_PATH", tmp_path / "test_memory.db")

    # Reset the module-level connection so each test gets a clean DB
    import core.memory_store as ms

    ms.close()
    ms._conn = None  # type: ignore[attr-defined]
    yield
    ms.close()
    ms._conn = None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Schema / initialisation
# ---------------------------------------------------------------------------


def test_schema_created_on_first_use() -> None:
    """Accessing the DB creates the three tables automatically."""
    import core.memory_store as ms

    stats = ms.get_stats()
    assert stats == {"total_sessions": 0, "total_messages": 0, "total_facts": 0}


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


def test_create_session_persists() -> None:
    """create_session stores a row; list_sessions returns it."""
    import core.memory_store as ms

    ms.create_session("abc12345", model="gpt-4o")
    sessions = ms.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == "abc12345"
    assert sessions[0]["model"] == "gpt-4o"
    assert sessions[0]["ended_at"] is None


def test_create_session_idempotent() -> None:
    """Calling create_session twice with the same ID does not raise."""
    import core.memory_store as ms

    ms.create_session("dup00001")
    ms.create_session("dup00001")  # INSERT OR IGNORE — should be silent
    assert len(ms.list_sessions()) == 1


def test_end_session_updates_ended_at() -> None:
    """end_session sets ended_at and optionally stores a summary."""
    import core.memory_store as ms

    ms.create_session("sess0001")
    ms.end_session("sess0001", summary="Did some disk work")
    sess = ms.list_sessions()[0]
    assert sess["ended_at"] is not None
    assert sess["summary"] == "Did some disk work"


def test_list_sessions_newest_first() -> None:
    """list_sessions returns rows in descending started_at order."""
    import time

    import core.memory_store as ms

    ms.create_session("old00001")
    time.sleep(0.01)
    ms.create_session("new00002")
    ids = [s["id"] for s in ms.list_sessions()]
    assert ids == ["new00002", "old00001"]


# ---------------------------------------------------------------------------
# Message CRUD
# ---------------------------------------------------------------------------


def test_save_and_load_messages() -> None:
    """Messages saved individually can be retrieved in order."""
    import core.memory_store as ms

    ms.create_session("msg00001")
    ms.save_message("msg00001", "user", "Hello")
    ms.save_message("msg00001", "assistant", "Hi there!")
    msgs = ms.load_session_messages("msg00001")
    assert len(msgs) == 2
    assert msgs[0] == {"role": "user", "content": "Hello"}
    assert msgs[1] == {"role": "assistant", "content": "Hi there!"}


def test_save_messages_bulk() -> None:
    """save_messages bulk-inserts a list of dicts."""
    import core.memory_store as ms

    ms.create_session("bulk0001")
    ms.save_messages(
        "bulk0001",
        [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
        ],
    )
    msgs = ms.load_session_messages("bulk0001")
    assert len(msgs) == 3
    assert msgs[2]["content"] == "Q2"


def test_save_messages_skips_invalid_roles() -> None:
    """save_messages silently ignores entries with unrecognised roles."""
    import core.memory_store as ms

    ms.create_session("inv00001")
    ms.save_messages(
        "inv00001",
        [
            {"role": "user", "content": "Valid"},
            {"role": "unknown", "content": "Invalid"},
        ],
    )
    msgs = ms.load_session_messages("inv00001")
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Valid"


def test_load_recent_messages_limit() -> None:
    """load_recent_messages respects the limit parameter."""
    import core.memory_store as ms

    ms.create_session("lim00001")
    for i in range(10):
        ms.save_message("lim00001", "user", f"msg {i}")
    recent = ms.load_recent_messages(limit=3, session_id="lim00001")
    assert len(recent) == 3
    # Should be the last 3 (oldest-first after reversal in helper)
    assert recent[-1]["content"] == "msg 9"


def test_load_session_messages_empty() -> None:
    """Loading messages for a session with no messages returns empty list."""
    import core.memory_store as ms

    ms.create_session("empty001")
    assert ms.load_session_messages("empty001") == []


# ---------------------------------------------------------------------------
# Facts CRUD
# ---------------------------------------------------------------------------


def test_upsert_and_get_fact() -> None:
    """upsert_fact stores a key; get_fact retrieves it."""
    import core.memory_store as ms

    ms.upsert_fact("user.drive", "D:", category="preference")
    assert ms.get_fact("user.drive") == "D:"


def test_upsert_fact_updates_existing() -> None:
    """Upserting the same key updates the value."""
    import core.memory_store as ms

    ms.upsert_fact("key1", "value_old")
    ms.upsert_fact("key1", "value_new")
    assert ms.get_fact("key1") == "value_new"


def test_get_fact_missing_returns_none() -> None:
    """get_fact returns None for a non-existent key."""
    import core.memory_store as ms

    assert ms.get_fact("nonexistent.key") is None


def test_list_facts_all() -> None:
    """list_facts returns all stored facts."""
    import core.memory_store as ms

    ms.upsert_fact("a", "1", category="cat_a")
    ms.upsert_fact("b", "2", category="cat_b")
    facts = ms.list_facts()
    assert len(facts) == 2
    keys = {f["key"] for f in facts}
    assert keys == {"a", "b"}


def test_list_facts_by_category() -> None:
    """list_facts(category=...) filters correctly."""
    import core.memory_store as ms

    ms.upsert_fact("p1", "v1", category="pref")
    ms.upsert_fact("s1", "v2", category="system")
    pref_facts = ms.list_facts(category="pref")
    assert len(pref_facts) == 1
    assert pref_facts[0]["key"] == "p1"


def test_delete_fact() -> None:
    """delete_fact removes the key and returns True; False for missing key."""
    import core.memory_store as ms

    ms.upsert_fact("del_me", "value")
    assert ms.delete_fact("del_me") is True
    assert ms.get_fact("del_me") is None
    assert ms.delete_fact("del_me") is False


# ---------------------------------------------------------------------------
# build_memory_context
# ---------------------------------------------------------------------------


def test_build_memory_context_empty() -> None:
    """build_memory_context returns empty string when nothing is stored."""
    import core.memory_store as ms

    ms.create_session("ctx00001")
    ctx = ms.build_memory_context("ctx00001")
    assert ctx == ""


def test_build_memory_context_with_data() -> None:
    """build_memory_context includes facts and recent messages."""
    import core.memory_store as ms

    ms.create_session("ctx00002")
    ms.upsert_fact("user.drive", "C:", category="preference")
    ms.save_message("ctx00002", "user", "What is the disk usage?")
    ms.save_message("ctx00002", "assistant", "C: drive is 80% full.")

    ctx = ms.build_memory_context("ctx00002", max_recent_messages=10)
    assert "user.drive" in ctx
    assert "C:" in ctx
    assert "disk usage" in ctx


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def test_get_stats_counts() -> None:
    """get_stats returns correct counts after inserting data."""
    import core.memory_store as ms

    ms.create_session("stat0001")
    ms.save_message("stat0001", "user", "hello")
    ms.upsert_fact("k", "v")
    stats = ms.get_stats()
    assert stats["total_sessions"] == 1
    assert stats["total_messages"] == 1
    assert stats["total_facts"] == 1
