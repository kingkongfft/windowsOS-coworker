# windowsOS-coworker — Developing Status

> Date: 2026-06-29
> Phase: Phase 1 ✅ Complete | Phase 2 ✅ Complete | Phase 2.1 ✅ Complete | Phase 3 ✅ Complete | Phase 3 GUI Polish ✅ Complete

---

## Phase 3 — GUI Polish / Bug Fixes (2026-06-29) ✅ Complete

### Issues found (from live smoke-test screenshot)

Four visual defects were visible when running `python gui.py` for the first time:

1. **Assistant bubble text cut off** — only one line visible despite long response
2. **User bubble had no background** — `#EBF3FF` pill shape invisible, text appeared unstyled
3. **Header subtitle truncated** — "Session …" clipped to just a few characters
4. **Red divider spanned full window width** — ran edge-to-edge instead of aligning with message text

### Root causes & fixes

| Issue | Root Cause | Fix |
|---|---|---|
| Bubble text cut off | `QTextEdit.document().size().height()` measured before Qt layout pass (no width assigned yet) → always 1-line height; `setFixedHeight` locked it permanently | Replaced `QTextEdit` with `_AutoResizeBrowser(QTextBrowser)` that connects to `documentSizeChanged` signal — height recalculated *after* real layout pass |
| User bubble unstyled | `QTextEdit` silently ignores `border-radius`, `padding`, `background-color` from QSS (viewport architecture) | Replaced with `QLabel(wordWrap=True)` which fully honours all QSS properties |
| Header subtitle truncated | `addStretch()` between title and subtitle pushed subtitle to zero remaining space | Removed stretch; title uses `stretch=1`, subtitle sits naturally to the right |
| Divider full-width | Divider `QWidget` added directly to zero-margin `QVBoxLayout` — Qt stretches it to container width | Replaced with `_make_divider()` helper that wraps line in `QHBoxLayout` with 42 px left inset (= avatar 32 px + spacing 10 px) |
| Theme still flat / grey | Original Doubao palette was light & flat; user asked for “立体” (3D) blue theme | Rebuilt `ui/styles/theme.py` + `main.qss` with deep navy background, layered panels, glowing accent buttons, inset cards, and blue gradients |

### Files changed

| File | Lines (before → after) | Change |
|---|---|---|
| `ui/widgets/message_bubble.py` | 313 → 335 | `QTextEdit` → `QLabel` (user) + `_AutoResizeBrowser` (assistant); added `_AutoResizeBrowser` class with `documentSizeChanged` auto-resize |
| `ui/widgets/chat_area.py` | 312 → 334 | Added `_make_divider()` helper; fixed header layout (stretch=1 on title, removed addStretch); added `QSizePolicy` import |
| `ui/styles/main.qss` | 373 → 381 | Added `#AssistantBubble QAbstractScrollArea` rule to make viewport background transparent so border-radius shows through |

### Test result: **56/56 pass** (unchanged)

---

## Phase 3 — Desktop GUI (2026-06-29) ✅ Complete

### What was built

**Full PyQt6 GUI — 2082 lines across 15 files (14 UI + 1 test helper), all P3.1–P3.5 complete.**

**New entry point:** `gui.py` (31 lines) — `python gui.py` launches the GUI mode.

**New `ui/` package:**

| File | Lines | Purpose |
|---|---|---|
| `ui/app.py` | 55 | `QApplication` init + main window startup |
| `ui/main_window.py` | 188 | `QMainWindow` — left/right split layout, session management, welcome screen |
| `ui/worker.py` | 76 | `QThread` worker — runs `Runner.run()` in background thread, pushes results via `pyqtSignal` |
| `ui/bridge.py` | 77 | SDK init + monkey-patches `core.approval.request_approval` with GUI dialog at startup |
| `ui/widgets/message_bubble.py` | 335 | User/assistant chat bubbles — `QLabel` (user) + `_AutoResizeBrowser` (assistant), Markdown-to-HTML, Pygments code highlighting, typewriter streaming |
| `ui/widgets/input_bar.py` | 153 | Multi-line input, Enter to send, Shift+Enter newline, quick-action chips, send/stop toggle |
| `ui/widgets/chat_area.py` | 334 | Scrollable message area, welcome screen, inset turn dividers, deferred scroll-to-bottom |
| `ui/widgets/sidebar.py` | 186 | History list (from `memory_store`), title-text search filter, new-chat button, session switching |
| `ui/widgets/approval_dialog.py` | 153 | MEDIUM (yellow) and HIGH (red, type-to-confirm) GUI approval dialogs |
| `ui/widgets/thinking_indicator.py` | 48 | Animated "thinking…" dots indicator |
| `ui/styles/theme.py` | 90 | Deep Blue 3D palette — layered backgrounds, accent colours, spacing |
| `ui/styles/main.qss` | 381 | Qt stylesheet — deep blue gradients, glowing buttons, cards/shadows |

**New test helper:** `tests/skills/conftest.py` (27 lines) — `raw()` unwraps `@function_tool` objects for unit testing.

**Dependencies added to `requirements.txt` and `pyproject.toml`:** `PyQt6>=6.7.0`, `qasync>=0.27.0`, `pygments>=2.18.0`

### Key design decisions

- GUI uses the same `core/`, `agents/`, `skills/` layers — zero duplication with CLI
- `ui/bridge.init_sdk()` monkey-patches `core.approval.request_approval` so all tool approval gates transparently show the GUI dialog instead of a Rich CLI prompt — no changes needed to orchestrator or skill files
- `AgentWorker` (QThread) runs `Runner.run()` off the main thread; results returned via `pyqtSignal`
- Markdown rendered via `_md_to_html` + Pygments; scroll-to-bottom deferred with `QTimer.singleShot(0, …)` so Qt reflows first
- `python main.py` → CLI unchanged; `python gui.py` → GUI; both share the same DB and agent layer

### P3 Iteration Status

| Iteration | Status | Milestone |
|---|---|---|
| **P3.1** — Skeleton window: main_window, QSS theme, gui.py entry | ✅ Complete | `python gui.py` opens window |
| **P3.2** — Message bubbles + input bar + send/receive flow | ✅ Complete | Can send messages + see replies |
| **P3.3** — Sidebar: history list, new chat, session switching | ✅ Complete | Can switch/search history |
| **P3.4** — Markdown rendering + code highlighting + typewriter effect | ✅ Complete | Formatted messages display |
| **P3.5** — Approval dialog + quick-action buttons + UI polish | ✅ Complete | Full CLI replacement |
| Update `requirements.txt` and `pyproject.toml` | ✅ Complete | — |

### Bugs fixed during completion

| Bug | Fix |
|---|---|
| `finish_assistant_message` — streaming bubble not re-rendered with final text | Added `MessageBubble.set_text()`; `finish_assistant_message` calls it with `full_text` |
| `clear_messages` — divider `QWidget`s left in layout on session switch | Rewrote to drain all layout items except the welcome screen |
| Scroll-to-bottom fires before Qt reflows new widget | Changed to `QTimer.singleShot(0, ...)` |
| Sidebar search always empty — searched `toolTip()` which was never set | `_SessionItem` now stores `_title_text`; `_filter_list` searches it |
| GUI approval gate defined but never wired — CLI prompts still fired in GUI | `bridge.init_sdk()` monkey-patches `core.approval.request_approval` at startup |
| 11 pre-existing skill tests failing — `@function_tool` wraps callables, not plain functions | Added `tests/skills/conftest.py:raw()`; updated all 3 skill test files |

### Test result: **56/56 pass**

---

## Phase 2.1 — Agent Self-Awareness of Memory (2026-06-29) ✅ Complete

### Problem

The agent had no knowledge that the SQLite memory infrastructure existed. When asked
"where is your memory stored?" or "do you remember me?", it deflected with generic
"I'm stateless" answers — factually wrong and unhelpful.

### Root cause

The orchestrator system prompt contained zero information about `memory_store.py`, the
DB path, or the slash commands. The LLM can only know what is in its prompt.

### Fix — `agents/orchestrator.py`

Added an "About yourself and your memory" section to `ORCHESTRATOR_SYSTEM_PROMPT`:

- States the agent has persistent SQLite memory at `sessions/memory.db`
- Describes all 3 tables (sessions, messages, facts) and what each stores
- Lists all 4 memory slash commands with descriptions (`/history`, `/memory`, `/sessions`, `/stats`)
- Explicitly instructs the agent to answer memory questions accurately instead of deflecting

### New test file — `tests/agents/test_orchestrator_memory.py` (9 tests, all passing)

No API key required — all tests run offline.

| Test | What it proves |
|---|---|
| `test_prompt_mentions_sqlite_db` | Prompt contains "sqlite" or "memory.db" |
| `test_prompt_mentions_sessions_db_path` | Exact path `sessions/memory.db` is in the prompt |
| `test_prompt_mentions_memory_slash_commands` | All 4 slash commands listed in prompt |
| `test_prompt_instructs_accurate_memory_answers` | "answer accurately" instruction present |
| `test_prompt_describes_three_tables` | All 3 table names in prompt |
| `test_conversation_round_trip` | 4-turn conversation saved and retrieved correctly |
| `test_session_survives_reconnect` | Data survives DB close + reopen (simulates restart) |
| `test_facts_persist_across_sessions` | Fact from session A visible in session B |
| `test_stats_reflect_real_conversation` | `get_stats()` counts match exactly what was written |

Test result: **56/56 pass** (all tests across the project, including 11 previously-failing skill tests now fixed)

---

## Phase 2 — SQLite Long-Term Memory (2026-06-29) ✅ Complete

### What was built

**`core/memory_store.py`** (new — 438 lines, stdlib `sqlite3`, no new dependencies)

Three-table schema stored at `sessions/memory.db`:

| Table | Purpose |
|---|---|
| `sessions` | One row per chat session — id, started_at, ended_at, model, summary |
| `messages` | Every user/assistant turn — FK → session, role, content, timestamp |
| `facts` | Persistent key/value facts that survive across all sessions — key, value, category, source, timestamps |

Key public API:

| Function | Description |
|---|---|
| `create_session(id, model)` | Register session start |
| `end_session(id, summary)` | Mark session ended |
| `list_sessions(limit)` | Recent sessions, newest first |
| `save_message(session_id, role, content)` | Persist a single turn |
| `save_messages(session_id, messages)` | Bulk-persist a list of turns |
| `load_session_messages(session_id)` | Replay full history for a session |
| `load_recent_messages(limit, session_id)` | Last N turns (cross-session or per-session) |
| `upsert_fact(key, value, category, source)` | Insert or update a persistent fact |
| `get_fact(key)` | Retrieve one fact by key |
| `list_facts(category)` | All facts, optionally filtered by category |
| `delete_fact(key)` | Remove a fact |
| `build_memory_context(session_id)` | Compact summary for injecting into agent prompts |
| `get_stats()` | Total sessions / messages / facts counts |
| `close()` | Graceful DB shutdown |

Implementation details:
- WAL journal mode — concurrent reads while writing
- `PRAGMA foreign_keys=ON` — cascading deletes if a session is removed
- Thread-safe via module-level `threading.Lock`
- Connection lazily initialised on first use, closed in `finally` block on app exit

**`config.py`** — added `MEMORY_DB_PATH = SESSIONS_DIR / "memory.db"`

**`main.py`** — wired in persistent memory:
- `create_session()` called at startup; `end_session()` called in `finally` (survives crashes)
- Every user turn saved to DB before sending to the agent
- Every assistant response saved to DB after receiving
- 5 new slash commands added:

| Command | Description |
|---|---|
| `/history [n]` | Show last n messages from current session (default 10) |
| `/memory` | Show all persistent facts in a Rich table |
| `/sessions` | List 10 most recent sessions |
| `/stats` | Memory DB stats (counts + file path) |
| `/audit` | (existing) Last 20 audit log entries |
| `/clear` | (existing) Clear in-memory history; DB records preserved |
| `/help` | (updated) All commands |

**`tests/core/test_memory_store.py`** (new — 19 tests, all passing)

| Test | What it covers |
|---|---|
| `test_schema_created_on_first_use` | Tables exist after first DB access |
| `test_create_session_persists` | Session row written with correct fields |
| `test_create_session_idempotent` | Duplicate create does not raise |
| `test_end_session_updates_ended_at` | `ended_at` and `summary` set correctly |
| `test_list_sessions_newest_first` | Correct sort order |
| `test_save_and_load_messages` | Round-trip single messages |
| `test_save_messages_bulk` | Bulk insert returns correct count and order |
| `test_save_messages_skips_invalid_roles` | Bad roles silently dropped |
| `test_load_recent_messages_limit` | `limit` param respected |
| `test_load_session_messages_empty` | Empty list for new session |
| `test_upsert_and_get_fact` | Fact round-trip |
| `test_upsert_fact_updates_existing` | Second upsert overwrites value |
| `test_get_fact_missing_returns_none` | Missing key → `None` |
| `test_list_facts_all` | All facts returned |
| `test_list_facts_by_category` | Category filter works |
| `test_delete_fact` | Returns `True` on delete, `False` on missing |
| `test_build_memory_context_empty` | Empty string when nothing stored |
| `test_build_memory_context_with_data` | Facts + messages appear in output |
| `test_get_stats_counts` | Correct counts after inserts |

Test result: **36/36 pass** (all core tests)

---

## Runtime fixes applied (2026-06-29)

| Fix | File | Detail |
|---|---|---|
| DeepSeek API configured | `.env` (new) | `OPENAI_API_KEY`, `OPENAI_BASE_URL=https://api.deepseek.com`, `AGENT_MODEL=deepseek-chat` |
| `.gitignore` added | `.gitignore` (new) | Protects `.env`, caches, runtime output from being committed |
| dotenv override | `config.py` | `load_dotenv(..., override=True)` — ensures `.env` key wins over system-level proxy keys |
| dotenv loading | `config.py` | Added `python-dotenv` load at startup; exposed `OPENAI_BASE_URL` config var |
| SDK namespace conflict fixed | `agents/__init__.py` | Local `agents/` folder was shadowing the installed `openai-agents` SDK; bridge now loads SDK from site-packages and re-exports its full public API + sub-modules |
| SDK API mode fixed | `main.py` | Set `chat_completions` mode + explicit `AsyncOpenAI` client — DeepSeek doesn't support the Responses API (was causing 404) |
| SDK tracing disabled | `main.py` | `set_tracing_disabled(True)` called before orchestrator import — eliminates `[non-fatal] Tracing: request failed` noise |
| Clean Ctrl+C exit | `main.py` | `KeyboardInterrupt` and `asyncio.CancelledError` caught at both loop and `main()` level — no more crash traceback on exit |
| UTF-8 console | `main.py` | `sys.stdout` re-wrapped with `utf-8` encoding — fixes `UnicodeEncodeError` for box-drawing characters on Windows cp1252 terminals |
| Missing tool added | `skills/memory/tools.py` | Implemented `clear_file_system_cache` (was referenced in `memory_skill_agent.py` but absent from tools module) |
| SDK installed | — | `pip install openai-agents>=0.0.19` (`openai-agents` was missing from environment) |

---

## What was just built — Phase 1 complete

### Project scaffolding
- `pyproject.toml` — ruff, mypy, pytest config
- `requirements.txt` — all dependencies
- `config.py` — API key, model, paths, auto-approve flag; now loads `.env` via python-dotenv

### `core/` — infrastructure layer

| File | Purpose |
|---|---|
| `exceptions.py` | `SkillExecutionError`, `ApprovalRequiredError`, `ElevationRequiredError`, `PowerShellError` |
| `risk.py` | `Risk` enum (LOW/MEDIUM/HIGH) + `@risk()` decorator + `get_risk()` |
| `powershell.py` | `run_ps()` — safe PowerShell wrapper, never shell-string interpolation, raises typed exceptions |
| `audit_log.py` | Append-only `.jsonl` audit trail — `log_tool_call`, `log_tool_result`, `log_session_start`, `tail()` |
| `approval.py` | Rich CLI approval gate — auto for LOW, one-click for MEDIUM, explicit type-to-confirm for HIGH |
| `memory_store.py` | SQLite long-term memory — sessions, messages, facts tables; thread-safe; WAL mode |

### `skills/` — 15 skill tool modules (100+ `@function_tool` functions)

All tools return `{"status": "ok"|"error", "message": ...}`. All decorated with `@risk()`.

| Skill Module | Tools |
|---|---|
| `skills/disk/` | `get_disk_usage`, `list_partitions`, `analyze_disk_usage`, `list_large_files`, `get_drive_health`, `clean_temp_files`, `clean_recycle_bin`, `clean_windows_update_cache`, `defrag_drive` |
| `skills/memory/` | `get_memory_usage`, `list_top_memory_processes`, `get_paging_file_info`, `identify_memory_leak_suspects`, `release_standby_memory`, `clear_file_system_cache`, `set_paging_file_size` |
| `skills/cpu/` | `get_cpu_usage`, `list_top_cpu_processes`, `get_power_plan`, `get_cpu_temperature`, `set_process_priority`, `set_process_affinity`, `set_power_plan`, `kill_high_cpu_process` |
| `skills/process/` | `list_processes`, `get_process_details`, `find_process_by_name`, `get_process_open_files`, `get_process_network_connections`, `suspend_process`, `resume_process`, `kill_process` |
| `skills/service/` | `list_services`, `get_service_status`, `get_service_dependencies`, `list_failed_services`, `start_service`, `restart_service`, `stop_service`, `set_service_startup_type` |
| `skills/network/` | `get_network_adapters`, `get_network_stats`, `test_connectivity`, `get_active_connections`, `get_dns_settings`, `list_firewall_rules`, `flush_dns_cache`, `add_firewall_rule`, `remove_firewall_rule`, `reset_network_stack`, `set_dns_servers` |
| `skills/app/` | `list_installed_apps`, `search_available_app`, `get_app_info`, `check_app_installed`, `update_app`, `install_app`, `uninstall_app`, `update_all_apps` |
| `skills/patch/` | `check_pending_updates`, `get_update_history`, `pause_windows_update`, `resume_windows_update`, `schedule_update_reboot`, `install_updates`, `install_security_updates_only`, `rollback_update` |
| `skills/eventlog/` | `list_event_logs`, `get_recent_errors`, `query_event_log`, `get_system_crashes`, `get_application_errors`, `export_event_log`, `clear_event_log` |
| `skills/registry/` | `read_registry_key`, `list_registry_subkeys`, `backup_registry_key`, `search_registry`, `write_registry_value`, `delete_registry_value`, `delete_registry_key`, `restore_registry_key` |
| `skills/taskscheduler/` | `list_scheduled_tasks`, `get_task_details`, `get_task_run_history`, `run_task_now`, `enable_task`, `disable_task`, `create_task`, `delete_task` |
| `skills/diagnostics/` | `get_system_info`, `get_system_uptime`, `get_reliability_history`, `get_startup_items`, `generate_system_report`, `run_sfc_scan`, `run_dism_health_check`, `check_disk_errors`, `disable_startup_item`, `run_dism_restore_health` |
| `skills/envconfig/` | `list_env_variables`, `get_env_variable`, `get_path_entries`, `get_power_plans`, `get_windows_features`, `set_power_plan`, `set_env_variable`, `delete_env_variable`, `add_to_path`, `remove_from_path`, `enable_windows_feature`, `disable_windows_feature` |
| `skills/security/` | `get_defender_status`, `get_firewall_status`, `get_bitlocker_status`, `get_audit_policy`, `list_open_shares`, `check_uac_level`, `list_installed_certificates`, `scan_open_ports`, `run_defender_quick_scan`, `enable_bitlocker` |
| `skills/user/` | `list_local_users`, `get_user_info`, `list_local_groups`, `get_logged_on_users`, `enable_local_user`, `create_local_user`, `disable_local_user`, `reset_local_user_password`, `add_user_to_group`, `remove_user_from_group` |

### `agents/` — 16 agents

- 15 focused skill agents: `disk`, `memory`, `cpu`, `process`, `service`, `network`, `app`, `patch`, `eventlog`, `registry`, `taskscheduler`, `diagnostics`, `envconfig`, `security`, `user`
- **`orchestrator.py`** — wires all 15 via `handoff()`, handles routing, risk prompting, multi-step task planning

### `main.py`

- Async Rich CLI loop with conversation history
- Every turn persisted to SQLite in real time (no data loss on crash)
- Session lifecycle managed with `create_session()` / `end_session()` in `finally`
- `/audit`, `/clear`, `/help`, `/history`, `/memory`, `/sessions`, `/stats` slash commands
- `Runner.run()` with full message history passed on each turn

### `tests/`

| Test File | Coverage |
|---|---|
| `tests/core/test_risk.py` | Risk enum, `@risk` decorator, `get_risk` default |
| `tests/core/test_audit_log.py` | All log functions, `tail()`, thread-safe writes |
| `tests/core/test_powershell.py` | `run_ps` success, flags, errors, elevation, output stripping |
| `tests/core/test_memory_store.py` | All 3 tables — session CRUD, message CRUD, facts CRUD, context builder, stats (19 tests) |
| `tests/agents/test_orchestrator_memory.py` | Prompt self-awareness (5 tests) + memory round-trip, restart, cross-session facts, stats (4 tests) |
| `tests/skills/test_disk.py` | `get_disk_usage`, `list_partitions` (mocked psutil) |
| `tests/skills/test_memory.py` | `get_memory_usage`, `list_top_memory_processes` (mocked psutil) |
| `tests/skills/test_process.py` | `list_processes`, `find_process_by_name`, `kill_process` (mocked psutil) |

---

## Full File Tree (79 Python files + 1 QSS)

```
windowsOS-coworker/
├── main.py
├── gui.py                                ← NEW (Phase 3) GUI entry point
├── config.py
├── pyproject.toml
├── requirements.txt
├── AGENTS.md
├── PLANNING.md
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── risk.py
│   ├── powershell.py
│   ├── audit_log.py
│   ├── approval.py
│   └── memory_store.py               ← NEW (Phase 2)
│
├── skills/
│   ├── __init__.py
│   ├── app/tools.py
│   ├── patch/tools.py
│   ├── disk/tools.py
│   ├── memory/tools.py
│   ├── cpu/tools.py
│   ├── process/tools.py
│   ├── service/tools.py
│   ├── network/tools.py
│   ├── user/tools.py
│   ├── eventlog/tools.py
│   ├── registry/tools.py
│   ├── taskscheduler/tools.py
│   ├── diagnostics/tools.py
│   ├── envconfig/tools.py
│   └── security/tools.py
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py               ← UPDATED (Phase 2.1 — self-awareness prompt)
│   ├── app_skill_agent.py
│   ├── patch_skill_agent.py
│   ├── disk_skill_agent.py
│   ├── memory_skill_agent.py
│   ├── cpu_skill_agent.py
│   ├── process_skill_agent.py
│   ├── service_skill_agent.py
│   ├── network_skill_agent.py
│   ├── user_skill_agent.py
│   ├── eventlog_skill_agent.py
│   ├── registry_skill_agent.py
│   ├── taskscheduler_skill_agent.py
│   ├── diagnostics_skill_agent.py
│   ├── envconfig_skill_agent.py
│   └── security_skill_agent.py
│
├── tests/
│   ├── core/
│   │   ├── test_risk.py
│   │   ├── test_audit_log.py
│   │   ├── test_powershell.py
│   │   └── test_memory_store.py      ← NEW (Phase 2)
│   ├── agents/
│   │   └── test_orchestrator_memory.py ← NEW (Phase 2.1)
│   └── skills/
│       ├── conftest.py               ← NEW (Phase 3) raw() FunctionTool unwrapper
│       ├── test_disk.py
│       ├── test_memory.py
│       └── test_process.py
│
├── sessions/          (runtime — SQLite memory.db lives here)
├── traces/            (runtime — trace output)
├── ui/                                   ← NEW (Phase 3) GUI package
│   ├── __init__.py
│   ├── app.py
│   ├── main_window.py
│   ├── worker.py
│   ├── bridge.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── message_bubble.py
│   │   ├── input_bar.py
│   │   ├── chat_area.py
│   │   ├── sidebar.py
│   │   ├── approval_dialog.py
│   │   └── thinking_indicator.py
│   └── styles/
│       ├── __init__.py
│       ├── theme.py
│       └── main.qss
└── init/
    └── copilot-cowork-overview.md
```

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Credentials loaded automatically from .env
# .env contains: OPENAI_API_KEY, OPENAI_BASE_URL, AGENT_MODEL

# CLI mode (original)
python main.py

# GUI mode (Phase 3)
python gui.py
```

### In-app commands

| Command | Description |
|---|---|
| `/audit` | Show last 20 audit log entries |
| `/clear` | Clear in-memory history (DB records preserved) |
| `/history [n]` | Show last n messages from current session (default 10) |
| `/memory` | Show all persistent facts |
| `/sessions` | List 10 most recent sessions |
| `/stats` | Memory DB stats + file path |
| `/help` | Show available commands |
| `exit` / `quit` | Exit the app |

### Run tests

```bash
# All unit tests (no real OS calls)
pytest -m "not integration"

# With coverage
pytest --cov=. --cov-report=term-missing

# Single test file
pytest tests/core/test_risk.py

# Single test by name
pytest tests/core/test_risk.py::test_risk_enum_values
```

---

## Phase Roadmap

| Phase | Status | Description |
|---|---|---|
| **Phase 1 — Foundation** | ✅ Complete | Core infra, all 15 skill tool modules, all agents, CLI loop, unit tests |
| **Runtime fixes** | ✅ Complete | DeepSeek API wired, SDK conflicts resolved, clean exit, UTF-8 console, tracing disabled |
| **App running** | ✅ Verified | `python main.py` works end-to-end with DeepSeek; all 15 skill agents confirmed importable |
| **Phase 2 — SQLite Memory** | ✅ Complete | `memory_store.py` (sessions + messages + facts), persistent turn logging, 5 new slash commands, 19 new tests |
| **Phase 2.1 — Agent Self-Awareness** | ✅ Complete | Orchestrator prompt updated with memory self-knowledge; 9 new offline tests confirming prompt content and DB round-trips |
| **Phase 3 — Desktop GUI** | ✅ Complete | Full PyQt6 GUI — all P3.1–P3.5 delivered; 56/56 tests passing |
| **Phase 3 Polish** | ✅ Complete | 4 visual bugs fixed post smoke-test: bubble height, bubble styling, header subtitle, divider width |
| **Phase 4 — Advanced** | ⬜ Pending | Scheduled prompts, proactive alerts, custom plugins, multi-machine support |
