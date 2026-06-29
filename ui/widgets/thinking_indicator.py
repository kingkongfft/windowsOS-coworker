"""thinking_indicator.py — Animated "thinking" widget shown while agent runs."""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ThinkingIndicator(QWidget):
    """Animated dots indicator displayed while the agent is processing.

    Shows "Thinking ●●●" with the dots cycling through 1–3 to simulate
    a pulsing animation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ThinkingWidget")
        self._dot_count = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Thinking ●")
        self._label.setObjectName("ThinkingLabel")
        layout.addWidget(self._label)
        layout.addStretch()

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        """Start the animation and show the widget."""
        self._dot_count = 0
        self._tick()
        self._timer.start()
        self.show()

    def stop(self) -> None:
        """Stop the animation and hide the widget."""
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._dot_count = (self._dot_count % 3) + 1
        dots = "●" * self._dot_count + "○" * (3 - self._dot_count)
        self._label.setText(f"Thinking  {dots}")
