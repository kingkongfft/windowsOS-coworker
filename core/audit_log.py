from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

_lock = threading.Lock()


def _write(entry: dict[str, Any]) -> None:
    """Append a single JSON entry to the audit log file (thread-safe).

    Args:
        entry: The dict to serialise and append.
    """
    line = json.dumps(entry, default=str, ensure_ascii=False)
    with _lock:
        with open(config.AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def log_tool_call(
    tool_name: str,
    risk_level: str,
    arguments: dict[str, Any],
    approved: bool,
) -> None:
    """Record that a tool was invoked (or rejected at the approval gate).

    Args:
        tool_name: Name of the tool function called.
        risk_level: 'low', 'medium', or 'high'.
        arguments: The kwargs passed to the tool.
        approved: True if the user approved the action; False if rejected.
    """
    _write(
        {
            "event": "tool_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "risk": risk_level,
            "arguments": arguments,
            "approved": approved,
        }
    )


def log_tool_result(
    tool_name: str,
    status: str,
    message: str,
) -> None:
    """Record the outcome of a tool execution.

    Args:
        tool_name: Name of the tool function that ran.
        status: 'ok' or 'error'.
        message: The result message returned by the tool.
    """
    _write(
        {
            "event": "tool_result",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "status": status,
            "message": message,
        }
    )


def log_session_start(session_id: str) -> None:
    """Record the start of a new agent session.

    Args:
        session_id: Unique identifier for the session.
    """
    _write(
        {
            "event": "session_start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        }
    )


def tail(n: int = 20) -> list[dict[str, Any]]:
    """Return the last *n* audit log entries as a list of dicts.

    Args:
        n: Number of most-recent entries to return.

    Returns:
        A list of parsed log entry dicts, oldest first.
    """
    path = Path(config.AUDIT_LOG_PATH)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-n:] if line.strip()]
