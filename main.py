from __future__ import annotations

import asyncio
import sys
import uuid

# Force UTF-8 output on Windows to avoid cp1252 encoding errors with
# box-drawing characters used by Rich.
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── SDK configuration must happen before any agents are imported ──────────────
# Import config first so .env is loaded and env vars are set before the SDK
# reads them during its own module-level initialisation.
import config  # noqa: E402

from agents import (  # noqa: E402
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI  # noqa: E402

# DeepSeek only supports the Chat Completions API, not the Responses API.
set_default_openai_api("chat_completions")
set_default_openai_client(
    AsyncOpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
    ),
    use_for_tracing=False,
)

# Disable tracing entirely — the tracing endpoint is OpenAI-specific and
# unavailable on DeepSeek, which causes noisy timeout errors and a messy
# crash on Ctrl+C when the tracing shutdown thread is still running.
set_tracing_disabled(True)

# ── remaining imports ─────────────────────────────────────────────────────────
import core.audit_log as audit_log  # noqa: E402

from agents.orchestrator import orchestrator  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.text import Text  # noqa: E402

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
            except asyncio.CancelledError:
                # User hit Ctrl+C while the agent was thinking — exit cleanly.
                console.print("\n[dim]Cancelled. Goodbye.[/dim]")
                return
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
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        # Swallow the KeyboardInterrupt that bubbles out of asyncio.run when
        # Ctrl+C is pressed — prevents the ugly traceback on exit.
        pass


if __name__ == "__main__":
    main()
