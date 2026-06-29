from __future__ import annotations

import asyncio
import contextlib
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
import config  # noqa: E402,I001

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
import core.audit_log as audit_log  # noqa: E402,I001
import core.memory_store as memory_store  # noqa: E402

from agents.orchestrator import orchestrator  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
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


# ---------------------------------------------------------------------------
# Slash-command handlers
# ---------------------------------------------------------------------------


def _cmd_audit() -> None:
    """Show the last 20 entries from the audit log."""
    import json

    entries = audit_log.tail(20)
    if not entries:
        console.print("[dim]Audit log is empty.[/dim]")
    else:
        console.print_json(json.dumps(entries, default=str, indent=2))


def _cmd_clear(history: list[dict[str, str]]) -> None:
    """Clear in-memory conversation history (does not erase DB records)."""
    history.clear()
    console.print("[dim]Conversation history cleared (DB records preserved).[/dim]")


def _cmd_help() -> None:
    """Print command reference."""
    console.print(
        Panel(
            "/audit        — show last 20 audit log entries\n"
            "/clear        — clear in-memory conversation history\n"
            "/history [n]  — show last n messages from this session (default 10)\n"
            "/memory       — show all persistent facts\n"
            "/sessions     — list recent sessions\n"
            "/stats        — show memory DB statistics\n"
            "/help         — show this help message\n"
            "exit          — quit the app",
            title="Commands",
            border_style="dim",
        )
    )


def _cmd_history(session_id: str, arg: str) -> None:
    """Print recent conversation messages for the current session.

    Args:
        session_id: The current session ID.
        arg: Optional numeric argument for the number of messages to show.
    """
    try:
        limit = int(arg) if arg.strip() else 10
    except ValueError:
        limit = 10

    msgs = memory_store.load_recent_messages(limit=limit, session_id=session_id)
    if not msgs:
        console.print("[dim]No messages stored yet for this session.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Role", style="cyan", width=12)
    table.add_column("Content", no_wrap=False)
    table.add_column("Time", style="dim", width=22)
    for m in msgs:
        role_style = "bold green" if m["role"] == "user" else "bold blue"
        table.add_row(
            Text(m["role"], style=role_style),
            m["content"][:200] + ("…" if len(m["content"]) > 200 else ""),
            m.get("ts", ""),
        )
    console.print(table)


def _cmd_memory() -> None:
    """Display all persistent facts stored in the memory DB."""
    facts = memory_store.list_facts()
    if not facts:
        console.print("[dim]No persistent facts stored yet.[/dim]")
        return

    table = Table(title="Persistent Facts", show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Category", style="yellow")
    table.add_column("Updated", style="dim")
    for f in facts:
        table.add_row(
            f["key"],
            f["value"],
            f["category"],
            f.get("updated_at", "")[:19],
        )
    console.print(table)


def _cmd_sessions() -> None:
    """Print the 10 most recent sessions."""
    sessions = memory_store.list_sessions(limit=10)
    if not sessions:
        console.print("[dim]No sessions recorded yet.[/dim]")
        return

    table = Table(title="Recent Sessions", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Started", style="dim")
    table.add_column("Ended", style="dim")
    table.add_column("Model")
    table.add_column("Summary")
    for s in sessions:
        table.add_row(
            s["id"],
            (s.get("started_at") or "")[:19],
            (s.get("ended_at") or "—")[:19],
            s.get("model") or "",
            (s.get("summary") or "")[:60],
        )
    console.print(table)


def _cmd_stats() -> None:
    """Print memory DB statistics."""
    stats = memory_store.get_stats()
    console.print(
        Panel(
            f"Sessions : {stats['total_sessions']}\n"
            f"Messages : {stats['total_messages']}\n"
            f"Facts    : {stats['total_facts']}\n"
            f"DB path  : {config.MEMORY_DB_PATH}",
            title="Memory DB Stats",
            border_style="cyan",
        )
    )


# ---------------------------------------------------------------------------
# Main chat loop
# ---------------------------------------------------------------------------


async def chat_loop() -> None:
    """Run the main interactive CLI chat loop with SQLite-backed memory."""
    _check_api_key()

    session_id = str(uuid.uuid4())[:8]

    # Register session in memory DB and audit log
    memory_store.create_session(session_id, model=config.AGENT_MODEL)
    audit_log.log_session_start(session_id)

    console.print(Text(BANNER, style="bold cyan"))
    console.print(
        f"[dim]Session ID: {session_id}  |  Model: {config.AGENT_MODEL}  "
        f"|  Memory DB: {config.MEMORY_DB_PATH}[/dim]\n"
    )

    # In-memory list for the current session (also persisted to DB per turn)
    history: list[dict[str, str]] = []

    try:
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

            # ── Slash commands ────────────────────────────────────────────────
            lower = raw.lower()

            if lower == "/audit":
                _cmd_audit()
                continue

            if lower == "/clear":
                _cmd_clear(history)
                continue

            if lower == "/help":
                _cmd_help()
                continue

            if lower.startswith("/history"):
                arg = raw[len("/history") :].strip()
                _cmd_history(session_id, arg)
                continue

            if lower == "/memory":
                _cmd_memory()
                continue

            if lower == "/sessions":
                _cmd_sessions()
                continue

            if lower == "/stats":
                _cmd_stats()
                continue

            # ── Normal conversation turn ──────────────────────────────────────
            history.append({"role": "user", "content": raw})
            # Persist user message immediately
            memory_store.save_message(session_id, "user", raw)

            console.print()
            with console.status(
                "[bold yellow]Thinking...[/bold yellow]", spinner="dots"
            ):
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

            # Extract and persist assistant response
            response_text = result.final_output or "(no response)"
            history.append({"role": "assistant", "content": response_text})
            memory_store.save_message(session_id, "assistant", response_text)

            console.print("[bold blue]Assistant:[/bold blue]")
            try:
                console.print(Markdown(response_text))
            except Exception:
                console.print(response_text)
            console.rule(style="red")

    finally:
        # Always mark the session as ended, even on crash / Ctrl+C
        memory_store.end_session(session_id)
        memory_store.close()


def main() -> None:
    """Entry point for windowsOS-coworker."""
    # Swallow the KeyboardInterrupt that bubbles out of asyncio.run when
    # Ctrl+C is pressed — prevents the ugly traceback on exit.
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
