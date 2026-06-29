"""worker.py — QThread worker that runs Runner.run() off the main thread."""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI
from PyQt6.QtCore import QThread, pyqtSignal

import config
from agents import (
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)


def _init_sdk() -> None:
    """Initialise the OpenAI Agents SDK (idempotent)."""
    set_default_openai_api("chat_completions")
    set_default_openai_client(
        AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        ),
        use_for_tracing=False,
    )
    set_tracing_disabled(True)


class AgentWorker(QThread):
    """Background thread that runs a single agent turn.

    Signals:
        response_ready(str): Emitted with the full response text on success.
        error_occurred(str): Emitted with an error message on failure.
        finished_turn(): Emitted when the turn completes (success or error).
    """

    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_turn = pyqtSignal()

    def __init__(self, history: list[dict[str, str]], parent: Any = None) -> None:
        super().__init__(parent)
        self._history = list(history)  # snapshot
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the running turn."""
        self._cancelled = True
        self.requestInterruption()

    def run(self) -> None:
        """Entry point for the worker thread — runs the async event loop."""
        # Import here to avoid circular imports at module level
        from agents.orchestrator import orchestrator  # noqa: PLC0415

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                Runner.run(orchestrator, input=self._history)
            )
            if not self._cancelled:
                self.response_ready.emit(result.final_output or "(no response)")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            if not self._cancelled:
                self.error_occurred.emit(str(exc))
        finally:
            loop.close()
            self.finished_turn.emit()
