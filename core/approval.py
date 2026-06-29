from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

import config
from core.risk import Risk

_console = Console()


def request_approval(
    tool_name: str,
    risk_level: Risk,
    description: str,
    arguments: dict[str, Any],
) -> bool:
    """Display an approval prompt for a medium or high-risk action.

    Low-risk tools never reach this function — the orchestrator only calls it
    for MEDIUM and HIGH risk levels.

    For MEDIUM risk: a single Y/N confirmation is shown.
    For HIGH risk:   a detailed impact panel is shown and the user must type
                     the tool name exactly to confirm.

    When ``config.AUTO_APPROVE_MEDIUM`` is True, MEDIUM actions are
    automatically approved without prompting (for automated testing only).

    Args:
        tool_name: The name of the tool about to be called.
        risk_level: The :class:`Risk` level of the action.
        description: A plain-English description of what the action will do.
        arguments: The arguments the tool will be called with.

    Returns:
        True if the user approved the action, False if they rejected it.
    """
    if risk_level == Risk.LOW:
        return True

    if risk_level == Risk.MEDIUM and config.AUTO_APPROVE_MEDIUM:
        return True

    _render_action_panel(tool_name, risk_level, description, arguments)

    if risk_level == Risk.MEDIUM:
        return Confirm.ask(
            f"[yellow]Proceed with[/yellow] [bold]{tool_name}[/bold]?",
            default=False,
            console=_console,
        )

    # HIGH risk — require typing the tool name to confirm
    _console.print(
        Text(
            f'\nType "{tool_name}" to confirm, or anything else to cancel:',
            style="bold red",
        )
    )
    entered = Prompt.ask("Confirm", console=_console)
    return entered.strip() == tool_name


def _render_action_panel(
    tool_name: str,
    risk_level: Risk,
    description: str,
    arguments: dict[str, Any],
) -> None:
    """Render a Rich panel summarising the pending action.

    Args:
        tool_name: Name of the tool.
        risk_level: Risk level of the action.
        description: What the action will do.
        arguments: Arguments the tool will receive.
    """
    colour = "yellow" if risk_level == Risk.MEDIUM else "red"
    badge = f"[bold {colour}][{risk_level.value.upper()} RISK][/bold {colour}]"

    arg_lines = "\n".join(f"  {k}: {v}" for k, v in arguments.items()) or "  (none)"

    body = (
        f"{badge}  [bold]{tool_name}[/bold]\n\n"
        f"[cyan]What will happen:[/cyan]\n  {description}\n\n"
        f"[cyan]Arguments:[/cyan]\n{arg_lines}"
    )

    _console.print(
        Panel(body, title="Action Requires Approval", border_style=colour, expand=False)
    )
