"""app.py — QApplication bootstrap for GUI mode."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui.bridge import init_sdk
from ui.main_window import MainWindow


def _load_stylesheet(app: QApplication) -> None:
    """Load and apply the main QSS stylesheet."""
    qss_path = Path(__file__).parent / "styles" / "main.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def run() -> int:
    """Bootstrap and run the Qt application.

    Returns:
        Exit code from ``QApplication.exec()``.
    """
    # Force UTF-8 console output on Windows
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )

    # SDK must be initialised before any Agent is imported
    init_sdk()

    app = QApplication(sys.argv)
    app.setApplicationName("windowsOS-coworker")
    app.setApplicationVersion("0.1.0")

    # Default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    _load_stylesheet(app)

    window = MainWindow()
    window.show()

    return app.exec()
