"""gui.py — Entry point for the windowsOS-coworker desktop GUI.

Usage:
    python gui.py
"""

from __future__ import annotations

import sys


def main() -> None:
    """Launch the PyQt6 desktop GUI."""
    # Validate API key before opening window
    import config  # noqa: PLC0415

    if not config.OPENAI_API_KEY:
        print(
            "ERROR: OPENAI_API_KEY is not set.\n"
            "Add it to your .env file:\n"
            "  OPENAI_API_KEY=sk-..."
        )
        sys.exit(1)

    from ui.app import run  # noqa: PLC0415

    sys.exit(run())


if __name__ == "__main__":
    main()
