from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import config
import core.audit_log as audit_log


@pytest.fixture(autouse=True)
def tmp_audit_log(tmp_path: Path) -> None:
    """Redirect audit log to a temp file for each test."""
    with patch.object(config, "AUDIT_LOG_PATH", tmp_path / "test_audit.jsonl"):
        yield


def test_log_tool_call_writes_entry() -> None:
    audit_log.log_tool_call("kill_process", "high", {"pid": 1234}, approved=True)
    entries = audit_log.tail(1)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["event"] == "tool_call"
    assert entry["tool"] == "kill_process"
    assert entry["risk"] == "high"
    assert entry["approved"] is True
    assert entry["arguments"] == {"pid": 1234}


def test_log_tool_result_writes_entry() -> None:
    audit_log.log_tool_result("get_disk_usage", "ok", "C: has 50 GB free")
    entries = audit_log.tail(1)
    assert entries[0]["event"] == "tool_result"
    assert entries[0]["status"] == "ok"


def test_log_session_start() -> None:
    audit_log.log_session_start("abc123")
    entries = audit_log.tail(1)
    assert entries[0]["event"] == "session_start"
    assert entries[0]["session_id"] == "abc123"


def test_tail_returns_empty_when_no_log() -> None:
    # No writes yet — file may not exist
    entries = audit_log.tail(10)
    assert entries == []


def test_tail_respects_n() -> None:
    for i in range(5):
        audit_log.log_session_start(f"session-{i}")
    entries = audit_log.tail(3)
    assert len(entries) == 3


def test_multiple_writes_are_all_lines() -> None:
    audit_log.log_tool_call("a", "low", {}, approved=True)
    audit_log.log_tool_call("b", "medium", {}, approved=False)
    audit_log.log_tool_call("c", "high", {}, approved=True)
    entries = audit_log.tail(10)
    assert len(entries) == 3
    assert [e["tool"] for e in entries] == ["a", "b", "c"]
