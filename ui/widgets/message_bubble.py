"""message_bubble.py — User and assistant message bubble widgets."""

from __future__ import annotations

import re

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ui.styles import theme


def _md_to_html(text: str) -> str:
    """Convert a subset of Markdown to HTML for display in Qt labels.

    Handles: headings, bold, italic, inline code, fenced code blocks,
    bullet lists, numbered lists, horizontal rules, and line breaks.

    Args:
        text: Raw markdown string.

    Returns:
        HTML string suitable for QLabel / QTextBrowser rich text.
    """
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.util import ClassNotFound

    def escape(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Fenced code blocks (```lang\n...\n```)
    def replace_code_block(m: re.Match[str]) -> str:
        lang = m.group(1).strip() or ""
        code = m.group(2)
        try:
            lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
        except ClassNotFound:
            lexer = get_lexer_by_name("text")
        formatter = HtmlFormatter(
            style="one-dark",
            noclasses=True,
            nowrap=True,
            prestyles=(
                f"background:{theme.BG_CODE_BLOCK};"
                f"color:{theme.TEXT_CODE};"
                "padding:12px 14px;"
                "border-radius:8px;"
                "font-family:Cascadia Code,Consolas,monospace;"
                "font-size:12px;"
                "display:block;"
                "overflow-x:auto;"
                "margin:8px 0;"
            ),
        )
        highlighted = highlight(code, lexer, formatter)
        return f'<pre style="margin:0">{highlighted}</pre>'

    result = re.sub(r"```(\w*)\n(.*?)```", replace_code_block, text, flags=re.DOTALL)

    # Inline code
    result = re.sub(
        r"`([^`]+)`",
        lambda m: (
            f'<code style="background:#2D2D3F;color:#CDD6F4;'
            f"padding:2px 5px;border-radius:4px;"
            f'font-family:Consolas,monospace;font-size:12px;">'
            f"{escape(m.group(1))}</code>"
        ),
        result,
    )

    # Headings
    for lvl, fs in [(1, "18px"), (2, "16px"), (3, "14px")]:
        result = re.sub(
            rf"^{'#' * lvl} (.+)$",
            lambda m, fs=fs: (
                f'<p style="font-size:{fs};font-weight:700;'
                f'margin:10px 0 4px 0;">{m.group(1)}</p>'
            ),
            result,
            flags=re.MULTILINE,
        )

    # Bold + italic
    result = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", result)
    result = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", result)
    result = re.sub(r"\*(.+?)\*", r"<i>\1</i>", result)

    # Horizontal rule
    result = re.sub(
        r"^---+$",
        '<hr style="border:1px solid #E5E7EB;margin:8px 0;">',
        result,
        flags=re.MULTILINE,
    )

    # Bullet lists
    def replace_list(m: re.Match[str]) -> str:
        items = re.findall(r"^[ \t]*[-*] (.+)$", m.group(0), re.MULTILINE)
        lis = "".join(f"<li>{item}</li>" for item in items)
        return f'<ul style="margin:4px 0;padding-left:20px;">{lis}</ul>'

    result = re.sub(
        r"(^[ \t]*[-*] .+$\n?)+",
        replace_list,
        result,
        flags=re.MULTILINE,
    )

    # Numbered lists
    def replace_num_list(m: re.Match[str]) -> str:
        items = re.findall(r"^\d+\. (.+)$", m.group(0), re.MULTILINE)
        lis = "".join(f"<li>{item}</li>" for item in items)
        return f'<ol style="margin:4px 0;padding-left:20px;">{lis}</ol>'

    result = re.sub(
        r"(^\d+\. .+$\n?)+",
        replace_num_list,
        result,
        flags=re.MULTILINE,
    )

    # Newlines → <br> (skip inside <pre> blocks)
    parts = re.split(r"(<pre.*?</pre>)", result, flags=re.DOTALL)
    processed = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = part.replace("\n", "<br>")
        processed.append(part)
    result = "".join(processed)

    return result


class _Avatar(QLabel):
    """Small circular avatar label with initials."""

    def __init__(
        self, initials: str, bg: str, fg: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(initials, parent)
        self.setFixedSize(32, 32)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background-color:{bg};"
            f"color:{fg};"
            "border-radius:16px;"
            "font-size:12px;"
            "font-weight:700;"
        )


class _AutoResizeBrowser(QTextBrowser):
    """QTextBrowser that grows vertically to fit its content.

    Unlike QTextEdit, QTextBrowser:
    - Disables external link opening by default (safe)
    - Properly fires ``documentSizeChanged`` so we can resize after layout

    The height is recomputed whenever the document reflows (e.g. after the
    widget gets a real width from the parent layout).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Refit height whenever document content or width changes
        self.document().documentLayout().documentSizeChanged.connect(
            self._adjust_height
        )

    def _adjust_height(self) -> None:
        h = int(self.document().size().height()) + 8  # small padding
        self.setFixedHeight(min(max(h, 32), 4000))

    def sizeHint(self) -> QSize:
        h = int(self.document().size().height()) + 8
        return QSize(super().sizeHint().width(), min(max(h, 32), 4000))


class MessageBubble(QWidget):
    """A single message bubble (user or assistant).

    Args:
        role: 'user' or 'assistant'.
        content: The message text (Markdown supported for assistant).
        timestamp: Optional timestamp string shown below the bubble.
        parent: Parent widget.
    """

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._role = role
        self._full_text = content
        self._is_user = role == "user"
        self._build_ui(timestamp)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_text(self, chunk: str) -> None:
        """Append text to the bubble (typewriter streaming).

        Args:
            chunk: Text fragment to append.
        """
        self._full_text += chunk
        self._render()

    def set_text(self, text: str) -> None:
        """Replace bubble content with *text* and re-render.

        Used to finalise a streaming bubble with the authoritative full response.

        Args:
            text: The complete message text.
        """
        self._full_text = text
        self._render()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _render(self) -> None:
        """Re-render the bubble body from ``self._full_text``."""
        if self._is_user:
            # QLabel: plain text, word-wrap handles long lines
            self._body.setText(self._full_text)
        else:
            html = (
                '<div style="line-height:1.6;font-size:13px;'
                "font-family:'Segoe UI','Microsoft YaHei UI',Arial,sans-serif;\">"
                f"{_md_to_html(self._full_text)}</div>"
            )
            self._body.setHtml(html)  # type: ignore[union-attr]

    def _build_ui(self, timestamp: str) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 6, 16, 6)
        outer.setSpacing(10)

        if self._is_user:
            self._build_user(outer, timestamp)
        else:
            self._build_assistant(outer, timestamp)

    def _build_user(self, outer: QHBoxLayout, timestamp: str) -> None:
        outer.addStretch()
        col = QVBoxLayout()
        col.setSpacing(4)

        # Use QLabel — it fully honours QSS border-radius / padding / background
        self._body: QLabel = QLabel()  # type: ignore[assignment]
        self._body.setObjectName("UserBubble")
        self._body.setWordWrap(True)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._body.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self._body.setMaximumWidth(theme.BUBBLE_MAX_WIDTH)
        self._body.setText(self._full_text)
        col.addWidget(self._body, alignment=Qt.AlignmentFlag.AlignRight)

        if timestamp:
            ts = QLabel(timestamp)
            ts.setObjectName("MessageTimestamp")
            col.addWidget(ts, alignment=Qt.AlignmentFlag.AlignRight)

        outer.addLayout(col)
        outer.addWidget(_Avatar("You", theme.AVATAR_USER_BG, theme.AVATAR_USER_FG))

    def _build_assistant(self, outer: QHBoxLayout, timestamp: str) -> None:
        outer.addWidget(_Avatar("AI", theme.AVATAR_BOT_BG, theme.AVATAR_BOT_FG))
        col = QVBoxLayout()
        col.setSpacing(4)

        # Use _AutoResizeBrowser — auto-resizes after layout pass, respects HTML
        self._body = _AutoResizeBrowser()  # type: ignore[assignment]
        self._body.setObjectName("AssistantBubble")
        self._body.setMaximumWidth(theme.BUBBLE_MAX_WIDTH)

        html = (
            '<div style="line-height:1.6;font-size:13px;'
            "font-family:'Segoe UI','Microsoft YaHei UI',Arial,sans-serif;\">"
            f"{_md_to_html(self._full_text)}</div>"
        )
        self._body.setHtml(html)
        col.addWidget(self._body)

        # Copy button + timestamp row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        copy_btn = QPushButton("⎘ Copy")
        copy_btn.setObjectName("ToolbarButton")
        copy_btn.setFixedHeight(24)
        copy_btn.clicked.connect(self._copy_text)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()

        if timestamp:
            ts = QLabel(timestamp)
            ts.setObjectName("MessageTimestamp")
            btn_row.addWidget(ts)

        col.addLayout(btn_row)
        outer.addLayout(col)
        outer.addStretch()

    def _copy_text(self) -> None:
        QApplication.clipboard().setText(self._full_text)
