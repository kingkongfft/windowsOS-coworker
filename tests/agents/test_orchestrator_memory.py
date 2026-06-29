"""Smoke tests for the orchestrator prompt and memory integration.

These tests do NOT call the LLM — they verify:
1. The orchestrator system prompt contains the required self-awareness text
   about the SQLite memory infrastructure.
2. The memory store correctly round-trips a simulated conversation
   (the same path main.py takes on every turn).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import config


# ---------------------------------------------------------------------------
# Orchestrator prompt — self-awareness checks
# ---------------------------------------------------------------------------


def test_prompt_mentions_sqlite_db() -> None:
    """Orchestrator prompt must tell the agent its memory is SQLite-backed."""
    from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

    assert (
        "sqlite" in ORCHESTRATOR_SYSTEM_PROMPT.lower()
        or "memory.db" in ORCHESTRATOR_SYSTEM_PROMPT.lower()
    )


def test_prompt_mentions_sessions_db_path() -> None:
    """Orchestrator prompt must contain the DB file path."""
    from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

    assert "sessions/memory.db" in ORCHESTRATOR_SYSTEM_PROMPT


def test_prompt_mentions_memory_slash_commands() -> None:
    """Orchestrator prompt must list the /memory and /history slash commands."""
    from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

    assert "/memory" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "/history" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "/sessions" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "/stats" in ORCHESTRATOR_SYSTEM_PROMPT


def test_prompt_instructs_accurate_memory_answers() -> None:
    """Prompt must explicitly instruct the agent to answer memory questions accurately."""
    from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

    # Key phrase that tells the agent not to deflect memory questions
    assert "answer accurately" in ORCHESTRATOR_SYSTEM_PROMPT


def test_prompt_describes_three_tables() -> None:
    """Prompt must describe all three DB tables so the agent can explain them."""
    from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

    assert "sessions" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "messages" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "facts" in ORCHESTRATOR_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Memory store integration — simulated conversation round-trip
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect DB to a temp file and reset connection for each test."""
    monkeypatch.setattr(config, "MEMORY_DB_PATH", tmp_path / "smoke_test.db")
    import core.memory_store as ms

    ms.close()
    ms._conn = None  # type: ignore[attr-defined]
    yield
    ms.close()
    ms._conn = None  # type: ignore[attr-defined]


def test_conversation_round_trip() -> None:
    """Simulate what main.py does on every turn and verify it's retrievable."""
    import core.memory_store as ms

    session_id = "test0001"
    ms.create_session(session_id, model="deepseek-chat")

    # Simulate two turns
    ms.save_message(session_id, "user", "where is your memory stored?")
    ms.save_message(
        session_id, "assistant", "Your conversation is saved to sessions/memory.db"
    )
    ms.save_message(session_id, "user", "cool, show me the stats")
    ms.save_message(session_id, "assistant", "Total sessions: 1, messages: 3, facts: 0")

    msgs = ms.load_session_messages(session_id)
    assert len(msgs) == 4
    assert msgs[0]["role"] == "user"
    assert "memory stored" in msgs[0]["content"]
    assert msgs[1]["role"] == "assistant"
    assert "memory.db" in msgs[1]["content"]


def test_session_survives_reconnect() -> None:
    """Data written in one connection is visible after close + reopen."""
    import core.memory_store as ms

    session_id = "persist01"
    ms.create_session(session_id)
    ms.save_message(session_id, "user", "remember this")

    # Simulate app restart — close and reset the connection
    ms.close()
    ms._conn = None  # type: ignore[attr-defined]

    # Reopen — should see the previously written message
    msgs = ms.load_session_messages(session_id)
    assert len(msgs) == 1
    assert msgs[0]["content"] == "remember this"


def test_facts_persist_across_sessions() -> None:
    """Facts stored in session A are visible from session B."""
    import core.memory_store as ms

    ms.create_session("sessA001")
    ms.upsert_fact(
        "user.preferred_drive", "D:", category="preference", source="sessA001"
    )
    ms.end_session("sessA001")

    # New session — facts table is shared
    ms.create_session("sessB001")
    assert ms.get_fact("user.preferred_drive") == "D:"
    facts = ms.list_facts(category="preference")
    assert len(facts) == 1


def test_stats_reflect_real_conversation() -> None:
    """get_stats() returns counts that match what was written."""
    import core.memory_store as ms

    ms.create_session("s1")
    ms.create_session("s2")
    ms.save_message("s1", "user", "hello")
    ms.save_message("s1", "assistant", "hi")
    ms.save_message("s2", "user", "bye")
    ms.upsert_fact("k1", "v1")
    ms.upsert_fact("k2", "v2")

    stats = ms.get_stats()
    assert stats["total_sessions"] == 2
    assert stats["total_messages"] == 3
    assert stats["total_facts"] == 2
