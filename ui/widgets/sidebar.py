"""sidebar.py — Left sidebar: search, new chat button, session history list."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import core.memory_store as memory_store
from ui.styles import theme


class _SessionItem(QPushButton):
    """A single clickable session entry in the sidebar list."""

    def __init__(
        self, session_id: str, title: str, subtitle: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.session_id = session_id
        self._title_text = title.lower()  # stored for search filtering
        self.setObjectName("SessionItem")
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(1)

        title_lbl = QLabel(title[:40] + ("…" if len(title) > 40 else ""))
        title_lbl.setStyleSheet(
            f"font-size:13px;color:{theme.TEXT_PRIMARY};font-weight:500;background:transparent;"
        )
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(
                f"font-size:11px;color:{theme.TEXT_SECONDARY};background:transparent;"
            )
            layout.addWidget(sub_lbl)

    def set_active(self, active: bool) -> None:
        """Highlight this item as the currently selected session."""
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """Left sidebar with search, new-chat button, and session list.

    Signals:
        new_chat_requested(): User clicked "New Chat".
        session_selected(str): User clicked a session; carries the session_id.
    """

    new_chat_requested = pyqtSignal()
    session_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(theme.SIDEBAR_WIDTH)
        self._items: list[_SessionItem] = []
        self._active_id: str | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def refresh_sessions(self) -> None:
        """Reload sessions from the DB and repopulate the list."""
        sessions = memory_store.list_sessions(limit=50)

        # Clear existing items
        for item in self._items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

        for s in sessions:
            sid = s["id"]
            # Use first user message as title
            msgs = memory_store.load_session_messages(sid)
            first_user = next((m["content"] for m in msgs if m["role"] == "user"), "")
            title = first_user[:40] if first_user else f"Session {sid}"
            started = (s.get("started_at") or "")[:16].replace("T", "  ")
            item = _SessionItem(sid, title, started)
            item.clicked.connect(lambda checked, i=item: self._on_item_clicked(i))
            self._list_layout.addWidget(item)
            self._items.append(item)
            if sid == self._active_id:
                item.set_active(True)

        self._list_layout.addStretch()
        self._filter_list(self._search.text())

    def set_active_session(self, session_id: str) -> None:
        """Mark the given session as active in the sidebar.

        Args:
            session_id: The session to highlight.
        """
        self._active_id = session_id
        for item in self._items:
            item.set_active(item.session_id == session_id)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(8)

        # App title
        title = QLabel("windowsOS-coworker")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        # Search box
        self._search = QLineEdit()
        self._search.setObjectName("SearchBox")
        self._search.setPlaceholderText("搜索历史对话…")
        self._search.textChanged.connect(self._filter_list)
        layout.addWidget(self._search)

        # New chat button
        new_btn = QPushButton("＋  新对话")
        new_btn.setObjectName("NewChatButton")
        new_btn.clicked.connect(self.new_chat_requested.emit)
        layout.addWidget(new_btn)

        # Section label
        section = QLabel("历史对话")
        section.setObjectName("SidebarSection")
        layout.addWidget(section)

        # Scrollable session list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent;border:none;")

        list_widget = QWidget()
        list_widget.setStyleSheet("background:transparent;")
        self._list_layout = QVBoxLayout(list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(2)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(list_widget)
        layout.addWidget(scroll, stretch=1)

        # Footer buttons
        layout.addWidget(self._footer_button("⚙  设置", lambda: None))
        layout.addWidget(self._footer_button("📋  审计日志", lambda: None))

    def _footer_button(self, label: str, slot: object) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("SidebarFooterBtn")
        btn.clicked.connect(slot)  # type: ignore[arg-type]
        return btn

    def _on_item_clicked(self, item: _SessionItem) -> None:
        self.set_active_session(item.session_id)
        self.session_selected.emit(item.session_id)

    def _filter_list(self, query: str) -> None:
        q = query.strip().lower()
        for item in self._items:
            if q:
                item.setVisible(q in item.session_id.lower() or q in item._title_text)
            else:
                item.setVisible(True)
