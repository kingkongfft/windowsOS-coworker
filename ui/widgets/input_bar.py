"""input_bar.py — Bottom input bar with text input and toolbar buttons."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.styles import theme


class _InputTextEdit(QTextEdit):
    """QTextEdit that emits ``submit`` on Enter and allows Shift+Enter newline."""

    submit = pyqtSignal()

    def keyPressEvent(self, e: QKeyEvent) -> None:  # type: ignore[override]
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            e.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submit.emit()
            return
        super().keyPressEvent(e)


class InputBar(QWidget):
    """Bottom input bar widget.

    Signals:
        message_submitted(str): Emitted when the user sends a message.
        stop_requested(): Emitted when the user clicks the stop button.
        quick_action(str): Emitted when a quick-action chip is clicked,
            carrying the pre-filled prompt text.
    """

    message_submitted = pyqtSignal(str)
    stop_requested = pyqtSignal()
    quick_action = pyqtSignal(str)

    # Pre-set prompt chips (label, prompt)
    QUICK_ACTIONS: list[tuple[str, str]] = [
        ("⚡ Disk", "Check disk usage on all drives and suggest cleanup if needed."),
        ("⚡ Memory", "Show current RAM usage and top memory-consuming processes."),
        ("⚡ CPU", "Check CPU usage and list the top CPU-consuming processes."),
        ("⚡ Network", "Check network adapter status and test internet connectivity."),
        ("⚡ Services", "List any failed or stopped Windows services."),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("InputContainer")
        self._busy = False
        self._build_ui()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_busy(self, busy: bool) -> None:
        """Switch between send mode and stop mode.

        Args:
            busy: True while agent is running; False when idle.
        """
        self._busy = busy
        self._send_btn.setVisible(not busy)
        self._stop_btn.setVisible(busy)
        self._input.setEnabled(not busy)

    def clear(self) -> None:
        """Clear the input text."""
        self._input.clear()

    def focus(self) -> None:
        """Give keyboard focus to the input field."""
        self._input.setFocus()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 10, 20, 16)
        main.setSpacing(8)

        # ── Input row ────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = _InputTextEdit()
        self._input.setObjectName("InputBox")
        self._input.setPlaceholderText("发消息…  (Enter 发送，Shift+Enter 换行)")
        self._input.setMinimumHeight(theme.INPUT_HEIGHT_MIN)
        self._input.setMaximumHeight(theme.INPUT_HEIGHT_MAX)
        self._input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._input.submit.connect(self._on_submit)
        self._input.document().contentsChanged.connect(self._adjust_height)
        input_row.addWidget(self._input)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.addStretch()

        self._send_btn = QPushButton("↑")
        self._send_btn.setObjectName("SendButton")
        self._send_btn.setToolTip("Send message  (Enter)")
        self._send_btn.clicked.connect(self._on_submit)
        btn_col.addWidget(self._send_btn)

        self._stop_btn = QPushButton("■")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setToolTip("Stop generation")
        self._stop_btn.setVisible(False)
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        btn_col.addWidget(self._stop_btn)

        input_row.addLayout(btn_col)
        main.addLayout(input_row)

        # ── Toolbar row ───────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        for label, prompt in self.QUICK_ACTIONS:
            btn = QPushButton(label)
            btn.setObjectName("ToolbarButton")
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked, p=prompt: self.quick_action.emit(p))
            toolbar.addWidget(btn)

        toolbar.addStretch()
        main.addLayout(toolbar)

    def _on_submit(self) -> None:
        text = self._input.toPlainText().strip()
        if text and not self._busy:
            self.message_submitted.emit(text)
            self._input.clear()

    def _adjust_height(self) -> None:
        doc_h = int(self._input.document().size().height()) + 20
        clamped = max(theme.INPUT_HEIGHT_MIN, min(doc_h, theme.INPUT_HEIGHT_MAX))
        self._input.setFixedHeight(clamped)
