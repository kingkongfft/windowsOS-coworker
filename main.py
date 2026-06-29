from __future__ import annotations

import asyncio
import sys
import uuid

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

import config
import core.audit_log as audit_log
from agents import Runner
from agents.orchestrator import orchestrator

console = Console()

BANNER = """
╔══════════════════════════════════════════════════╗
║        windowsOS-coworker  v0.1.0               ║
║   AI-powered Windows OS operations assistant    ║
║   Type 'exit' or 'quit' to stop                 ║
╚══════════════════════════════════════════════════╝
"""


def _check_api_key() -> None:
    """Verify the OpenAI API key is set before starting."""
    if not config.OPENAI_API_KEY:
        console.print(
            "[bold red]ERROR:[/bold red] OPENAI_API_KEY environment variable is not set.\n"
            "Run:  set OPENAI_API_KEY=sk-..."
        )
        sys.exit(1)


async def chat_loop() -> None:
    """Run the main interactive CLI chat loop."""
    _check_api_key()

    session_id = str(uuid.uuid4())[:8]
    audit_log.log_session_start(session_id)

    console.print(Text(BANNER, style="bold cyan"))
    console.print(
        f"[dim]Session ID: {session_id}  |  Model: {config.AGENT_MODEL}[/dim]\n"
    )

    history: list[dict[str, str]] = []

    while True:
        try:
            raw = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not raw:
            continue

        if raw.lower() in {"exit", "quit", "bye"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        # Special commands
        if raw.lower() == "/audit":
            entries = audit_log.tail(20)
            if not entries:
                console.print("[dim]Audit log is empty.[/dim]")
            else:
                import json

                console.print_json(json.dumps(entries, default=str, indent=2))
            continue

        if raw.lower() == "/clear":
            history.clear()
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        if raw.lower() == "/help":
            console.print(
                Panel(
                    "/audit  — show last 20 audit log entries\n"
                    "/clear  — clear conversation history\n"
                    "/help   — show this help message\n"
                    "exit    — quit the app",
                    title="Commands",
                    border_style="dim",
                )
            )
            continue

        # Build message list for the agent
        history.append({"role": "user", "content": raw})

        console.print()
        with console.status("[bold yellow]Thinking...[/bold yellow]", spinner="dots"):
            try:
                result = await Runner.run(
                    orchestrator,
                    input=history,
                )
            except Exception as exc:
                console.print(f"[bold red]Error:[/bold red] {exc}")
                history.pop()  # remove failed user message
                continue

        # Extract assistant response
        response_text = result.final_output or "(no response)"
        history.append({"role": "assistant", "content": response_text})

        console.print("[bold blue]Assistant:[/bold blue]")
        try:
            console.print(Markdown(response_text))
        except Exception:
            console.print(response_text)
        console.print()


def main() -> None:
    """Entry point for windowsOS-coworker."""
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
