"""bridge.py — Shared helpers: SDK init, approval gate override for GUI.

At startup (called from ui/app.py) ``init_sdk()`` initialises the OpenAI
Agents SDK and monkey-patches ``core.approval.request_approval`` so that any
tool that calls the approval gate gets a GUI dialog instead of a CLI prompt.
"""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

import config
import core.approval as _approval_module
from agents import (
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from core.risk import Risk


def init_sdk() -> None:
    """Initialise the OpenAI Agents SDK for GUI mode and install the GUI
    approval gate (call once at startup, before any Agent is imported).
    """
    set_default_openai_api("chat_completions")
    set_default_openai_client(
        AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        ),
        use_for_tracing=False,
    )
    set_tracing_disabled(True)

    # Patch the module-level function so all callers (orchestrator, skills)
    # transparently get the GUI dialog instead of a Rich CLI prompt.
    _approval_module.request_approval = _gui_request_approval  # type: ignore[assignment]


def _gui_request_approval(
    tool_name: str,
    risk_level: Risk,
    description: str,
    arguments: dict[str, Any],
) -> bool:
    """Show the GUI approval dialog instead of the CLI prompt.

    This replaces ``core.approval.request_approval`` when running in GUI mode.
    Signature matches the original so it is a drop-in replacement.

    Args:
        tool_name: Name of the tool to execute.
        risk_level: Risk.LOW / MEDIUM / HIGH.
        description: What the tool will do.
        arguments: Tool arguments for display.

    Returns:
        True if the user approved, False otherwise.
    """
    if risk_level == Risk.LOW:
        return True
    if risk_level == Risk.MEDIUM and config.AUTO_APPROVE_MEDIUM:
        return True

    # Import lazily to avoid pulling in PyQt6 in non-GUI contexts
    from ui.widgets.approval_dialog import ApprovalDialog  # noqa: PLC0415

    dlg = ApprovalDialog(tool_name, risk_level, description, arguments)
    dlg.exec()
    return dlg.approved


# Keep the old name as an alias for any code that imported it directly
gui_request_approval = _gui_request_approval
