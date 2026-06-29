"""main_window.py — QMainWindow: left sidebar + right chat area."""

from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QSplitter

import config
import core.audit_log as audit_log
import core.memory_store as memory_store
from ui.styles import theme
from ui.widgets.chat_area import ChatArea
from ui.widgets.sidebar import Sidebar
from ui.worker import AgentWorker


class MainWindow(QMainWindow):
    """The application's main window.

    Layout: fixed-width Sidebar (left) + stretching ChatArea (right),
    separated by a QSplitter so the user can drag to resize.
    """

    def __init__(self) -> None:
        super().__init__()
        self._worker: AgentWorker | None = None
        self._history: list[dict[str, str]] = []
        self._session_id: str = ""
        self._build_ui()
        self._start_new_session()

    # ------------------------------------------------------------------
    # Private — setup
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle("windowsOS-coworker")
        self.setMinimumSize(theme.WINDOW_MIN_W, theme.WINDOW_MIN_H)
        self.resize(theme.WINDOW_DEFAULT_W, theme.WINDOW_DEFAULT_H)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #E5E7EB; }")

        self._sidebar = Sidebar()
        self._sidebar.new_chat_requested.connect(self._start_new_session)
        self._sidebar.session_selected.connect(self._load_session)
        splitter.addWidget(self._sidebar)

        self._chat = ChatArea()
        self._chat.message_submitted.connect(self._on_user_message)
        self._chat.stop_requested.connect(self._on_stop)
        splitter.addWidget(self._chat)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    # ------------------------------------------------------------------
    # Private — session management
    # ------------------------------------------------------------------

    def _start_new_session(self) -> None:
        """Create a fresh session and reset UI state."""
        if self._session_id:
            memory_store.end_session(self._session_id)

        self._session_id = str(uuid.uuid4())[:8]
        self._history = []
        memory_store.create_session(self._session_id, model=config.AGENT_MODEL)
        audit_log.log_session_start(self._session_id)

        self._chat.clear_messages()
        self._chat.set_title(
            "新对话",
            f"Session {self._session_id}  ·  {config.AGENT_MODEL}",
        )
        self._sidebar.refresh_sessions()
        self._sidebar.set_active_session(self._session_id)
        self._chat.focus_input()

    def _load_session(self, session_id: str) -> None:
        """Load an existing session from the DB into the chat area.

        Args:
            session_id: The session to restore.
        """
        if session_id == self._session_id:
            return

        # Save current session
        if self._session_id:
            memory_store.end_session(self._session_id)

        self._session_id = session_id
        msgs = memory_store.load_session_messages(session_id)
        self._history = [{"role": m["role"], "content": m["content"]} for m in msgs]

        sessions = memory_store.list_sessions(limit=50)
        model = next(
            (s.get("model", "") for s in sessions if s["id"] == session_id), ""
        )
        first_user = next(
            (m["content"][:60] for m in msgs if m["role"] == "user"), "Session"
        )
        self._chat.set_title(first_user, f"Session {session_id}  ·  {model}")
        self._chat.load_history(
            [
                {"role": m["role"], "content": m["content"], "ts": m.get("ts", "")}
                for m in msgs
            ]
        )
        self._sidebar.set_active_session(session_id)
        self._chat.focus_input()

    # ------------------------------------------------------------------
    # Private — message flow
    # ------------------------------------------------------------------

    def _on_user_message(self, text: str) -> None:
        """Handle a new user message: update UI, persist, start worker."""
        if self._worker and self._worker.isRunning():
            return

        self._history.append({"role": "user", "content": text})
        memory_store.save_message(self._session_id, "user", text)

        self._chat.add_user_message(text)
        self._chat.start_assistant_message()
        self._chat.set_busy(True)

        # Update sidebar title if this is the first message
        self._sidebar.refresh_sessions()
        self._sidebar.set_active_session(self._session_id)

        self._worker = AgentWorker(self._history, parent=self)
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished_turn.connect(self._on_turn_finished)
        self._worker.start()

    def _on_response(self, text: str) -> None:
        """Handle successful agent response."""
        self._history.append({"role": "assistant", "content": text})
        memory_store.save_message(self._session_id, "assistant", text)
        self._chat.finish_assistant_message(text)

    def _on_error(self, msg: str) -> None:
        """Handle agent error — show in chat and remove failed user message."""
        if self._history and self._history[-1]["role"] == "user":
            self._history.pop()
        error_text = (
            f"**Error:** {msg}\n\nPlease try again or check your API key/connection."
        )
        self._chat.finish_assistant_message(error_text)

    def _on_turn_finished(self) -> None:
        """Called when worker thread completes (success or error)."""
        self._chat.set_busy(False)
        self._chat.focus_input()
        self._worker = None

    def _on_stop(self) -> None:
        """Cancel the running worker thread."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
            self._worker = None
        self._chat.set_busy(False)
        self._chat.finish_assistant_message("_(Generation stopped)_")
        self._chat.focus_input()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event: object) -> None:  # type: ignore[override]
        """Ensure DB is closed and worker is stopped on window close."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        if self._session_id:
            memory_store.end_session(self._session_id)
        memory_store.close()
        super().closeEvent(event)  # type: ignore[arg-type]
