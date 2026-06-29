"""approval_dialog.py — GUI approval dialogs replacing core/approval.py CLI prompts."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.risk import Risk
from ui.styles import theme


class ApprovalDialog(QDialog):
    """Modal dialog asking the user to approve a risky tool call.

    For MEDIUM risk: shows Yes/No buttons.
    For HIGH risk: requires the user to type the tool name exactly to confirm.

    Args:
        tool_name: Name of the tool to be executed.
        risk_level: Risk.MEDIUM or Risk.HIGH.
        description: Human-readable description of what will happen.
        arguments: Dict of tool arguments for display.
        parent: Parent widget.
    """

    def __init__(
        self,
        tool_name: str,
        risk_level: Risk,
        description: str,
        arguments: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tool_name = tool_name
        self._risk = risk_level
        self._approved = False
        self.setObjectName("ApprovalDialog")
        self.setWindowTitle("Action Requires Approval")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui(description, arguments)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def approved(self) -> bool:
        """True if the user confirmed the action."""
        return self._approved

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self, description: str, arguments: dict[str, Any]) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Risk badge + tool name
        header_row = QHBoxLayout()
        badge = QLabel(f"  {self._risk.value.upper()} RISK  ")
        badge.setObjectName(
            "RiskBadgeHigh" if self._risk == Risk.HIGH else "RiskBadgeMedium"
        )
        header_row.addWidget(badge)
        header_row.addSpacing(10)
        tool_lbl = QLabel(self._tool_name)
        tool_lbl.setObjectName("ApprovalTitle")
        header_row.addWidget(tool_lbl)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setObjectName("ApprovalBody")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Arguments box
        if arguments:
            args_text = "\n".join(f"  {k}: {v}" for k, v in arguments.items())
            args_box = QTextEdit()
            args_box.setPlainText(args_text)
            args_box.setReadOnly(True)
            args_box.setMaximumHeight(100)
            args_box.setStyleSheet(
                f"background:{theme.BG_SIDEBAR};border:1px solid {theme.BORDER};"
                f"border-radius:8px;padding:6px;font-family:{theme.FONT_FAMILY_CODE};font-size:12px;"
            )
            layout.addWidget(args_box)

        # HIGH: require typing tool name
        if self._risk == Risk.HIGH:
            confirm_label = QLabel(
                f'Type <b style="font-family:monospace">{self._tool_name}</b> to confirm:'
            )
            confirm_label.setObjectName("ApprovalBody")
            layout.addWidget(confirm_label)
            self._confirm_input = QLineEdit()
            self._confirm_input.setObjectName("ConfirmInput")
            self._confirm_input.setPlaceholderText(self._tool_name)
            layout.addWidget(self._confirm_input)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("DialogBtnCancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        if self._risk == Risk.HIGH:
            confirm_btn = QPushButton("Confirm")
            confirm_btn.setObjectName("DialogBtnDanger")
            confirm_btn.clicked.connect(self._on_high_confirm)
        else:
            confirm_btn = QPushButton("Proceed")
            confirm_btn.setObjectName("DialogBtnPrimary")
            confirm_btn.clicked.connect(self._on_medium_confirm)

        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _on_medium_confirm(self) -> None:
        self._approved = True
        self.accept()

    def _on_high_confirm(self) -> None:
        entered = self._confirm_input.text().strip()
        if entered == self._tool_name:
            self._approved = True
            self.accept()
        else:
            self._confirm_input.setStyleSheet(
                f"border:1.5px solid {theme.RISK_HIGH};border-radius:8px;"
                "padding:8px 12px;"
            )
            self._confirm_input.setPlaceholderText("❌ Incorrect — try again")
            self._confirm_input.clear()
