"""chat_area.py — Right-side chat panel: welcome screen + message scroll area."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles import theme
from ui.widgets.input_bar import InputBar
from ui.widgets.message_bubble import MessageBubble
from ui.widgets.thinking_indicator import ThinkingIndicator


class _WelcomeScreen(QWidget):
    """Shown when no messages exist in the current session."""

    chip_clicked = pyqtSignal(str)

    CHIPS: list[tuple[str, str]] = [
        ("📊 Check disk usage", "Check disk usage on all drives"),
        ("🧠 RAM & processes", "Show current RAM usage and top processes"),
        ("🔥 CPU hogs", "List top CPU-consuming processes right now"),
        ("🌐 Network check", "Check network adapters and connectivity"),
        ("🛡 Security status", "Show Windows Defender and firewall status"),
        ("🔧 Failed services", "List any failed Windows services"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(60, 60, 60, 60)

        title = QLabel("有什么我能帮你的吗？")
        title.setObjectName("WelcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("windowsOS-coworker — AI-powered Windows OS operations assistant")
        sub.setObjectName("WelcomeSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        # Chip grid — 3 columns
        chips_widget = QWidget()
        grid = QVBoxLayout(chips_widget)
        grid.setSpacing(10)
        row: list[QPushButton] = []
        for i, (label, prompt) in enumerate(self.CHIPS):
            btn = QPushButton(label)
            btn.setObjectName("QuickChip")
            btn.clicked.connect(lambda checked, p=prompt: self.chip_clicked.emit(p))
            if i % 3 == 0 and i > 0:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setSpacing(10)
                row_layout.setContentsMargins(0, 0, 0, 0)
                for b in row:
                    row_layout.addWidget(b)
                grid.addWidget(row_widget)
                row = []
            row.append(btn)
        if row:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(10)
            row_layout.setContentsMargins(0, 0, 0, 0)
            for b in row:
                row_layout.addWidget(b)
            row_layout.addStretch()
            grid.addWidget(row_widget)

        layout.addWidget(chips_widget)
        layout.addStretch()


class ChatArea(QWidget):
    """The main right-side panel: header + messages + input bar.

    Signals:
        message_submitted(str): Forwarded from InputBar when user sends.
        stop_requested(): Forwarded from InputBar stop button.
    """

    message_submitted = pyqtSignal(str)
    stop_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatArea")
        self._bubbles: list[MessageBubble] = []
        self._current_assistant_bubble: MessageBubble | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_title(self, title: str, subtitle: str = "") -> None:
        """Update the header title and subtitle.

        Args:
            title: Session title shown in the header.
            subtitle: Optional model/session info shown smaller.
        """
        self._title_label.setText(title)
        self._subtitle_label.setText(subtitle)

    def add_user_message(self, text: str) -> None:
        """Add a user message bubble.

        Args:
            text: The user's message text.
        """
        self._hide_welcome()
        ts = datetime.now().strftime("%H:%M")
        bubble = MessageBubble("user", text, timestamp=ts)
        self._msg_layout.addWidget(bubble)
        self._bubbles.append(bubble)
        self._scroll_to_bottom()

    def start_assistant_message(self) -> None:
        """Create an empty assistant bubble and show the thinking indicator."""
        self._hide_welcome()
        self._thinking.start()
        self._msg_layout.addWidget(self._thinking)
        self._scroll_to_bottom()

    def append_assistant_chunk(self, chunk: str) -> None:
        """Stream a text chunk into the current assistant bubble.

        If no assistant bubble exists yet, creates one (hides thinking).

        Args:
            chunk: Text fragment to append.
        """
        if self._current_assistant_bubble is None:
            self._thinking.stop()
            self._msg_layout.removeWidget(self._thinking)
            ts = datetime.now().strftime("%H:%M")
            bubble = MessageBubble("assistant", "", timestamp=ts)
            self._msg_layout.addWidget(bubble)
            self._bubbles.append(bubble)
            self._current_assistant_bubble = bubble
        self._current_assistant_bubble.append_text(chunk)
        self._scroll_to_bottom()

    def finish_assistant_message(self, full_text: str) -> None:
        """Finalise the assistant bubble with the complete response.

        Args:
            full_text: The complete assistant response text.
        """
        self._thinking.stop()
        self._msg_layout.removeWidget(self._thinking)
        self._thinking.setParent(None)  # type: ignore[call-overload]

        if self._current_assistant_bubble is None:
            ts = datetime.now().strftime("%H:%M")
            bubble = MessageBubble("assistant", full_text, timestamp=ts)
            self._msg_layout.addWidget(bubble)
            self._bubbles.append(bubble)
        else:
            # Re-render the bubble with the authoritative final text
            self._current_assistant_bubble.set_text(full_text)
        self._current_assistant_bubble = None

        # Red divider after each turn — inset to align with message content
        self._msg_layout.addWidget(self._make_divider())

        self._scroll_to_bottom()

    def clear_messages(self) -> None:
        """Remove all message bubbles and dividers, then show the welcome screen."""
        # Remove all children from the layout except the welcome screen
        while self._msg_layout.count() > 0:
            item = self._msg_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None and widget is not self._welcome:
                widget.deleteLater()
        self._bubbles.clear()
        self._current_assistant_bubble = None
        self._thinking.stop()
        # Re-add the welcome screen
        self._msg_layout.addWidget(self._welcome)
        self._show_welcome()

    def load_history(self, messages: list[dict[str, str]]) -> None:
        """Populate the chat area from a list of history message dicts.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
        """
        self.clear_messages()
        for m in messages:
            if m["role"] == "user":
                self.add_user_message(m["content"])
            elif m["role"] == "assistant":
                self._hide_welcome()
                ts = m.get("ts", "")[:5] if m.get("ts") else ""
                bubble = MessageBubble("assistant", m["content"], timestamp=ts)
                self._msg_layout.addWidget(bubble)
                self._bubbles.append(bubble)
                self._msg_layout.addWidget(self._make_divider())
        self._scroll_to_bottom()

    def set_busy(self, busy: bool) -> None:
        """Proxy to input bar busy state.

        Args:
            busy: True while agent is running.
        """
        self._input_bar.set_busy(busy)

    def focus_input(self) -> None:
        """Give focus to the input field."""
        self._input_bar.focus()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("ChatHeader")
        header.setMinimumHeight(56)
        header.setMaximumHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        h_layout.setSpacing(12)

        self._title_label = QLabel("新对话")
        self._title_label.setObjectName("ChatTitle")
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        h_layout.addWidget(self._title_label, stretch=1)

        self._subtitle_label = QLabel("")
        self._subtitle_label.setObjectName("ChatSubtitle")
        self._subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._subtitle_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        h_layout.addWidget(self._subtitle_label)
        layout.addWidget(header)

        # Scroll area with message container
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._msg_container = QWidget()
        self._msg_container.setObjectName("ChatArea")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(0, 12, 0, 12)
        self._msg_layout.setSpacing(4)
        self._msg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Welcome screen
        self._welcome = _WelcomeScreen()
        self._welcome.chip_clicked.connect(self.message_submitted.emit)
        self._msg_layout.addWidget(self._welcome)

        # Thinking indicator (hidden initially)
        self._thinking = ThinkingIndicator()
        self._thinking.hide()

        self._scroll.setWidget(self._msg_container)
        layout.addWidget(self._scroll, stretch=1)

        # Input bar
        self._input_bar = InputBar()
        self._input_bar.message_submitted.connect(self.message_submitted.emit)
        self._input_bar.stop_requested.connect(self.stop_requested.emit)
        self._input_bar.quick_action.connect(self._on_quick_action)
        layout.addWidget(self._input_bar)

    def _make_divider(self) -> QWidget:
        """Create an inset red turn-divider widget.

        The left inset (42 px = 32 px avatar + 10 px spacing) aligns the line
        with the start of message text rather than the window edge.
        """
        wrapper = QWidget()
        wrapper.setObjectName("TurnDivider")
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(42, 4, 16, 4)
        row.setSpacing(0)
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color:{theme.DIVIDER_RED};")
        row.addWidget(line)
        return wrapper

    def _hide_welcome(self) -> None:
        self._welcome.hide()

    def _show_welcome(self) -> None:
        self._welcome.show()

    def _scroll_to_bottom(self) -> None:
        # Defer one event loop tick so Qt has time to reflow the new widget
        QTimer.singleShot(
            0,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            ),
        )

    def _on_quick_action(self, prompt: str) -> None:
        self._input_bar._input.setPlainText(prompt)
        self._input_bar.focus()
