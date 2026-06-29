# windowsOS-coworker — Developing Status

> Date: 2026-06-29
> Phase: Phase 1 ✅ Complete | Phase 2 ✅ Complete | Phase 2.1 — Agent Self-Awareness ✅ Complete

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

Test result: **45/45 pass** (all tests across the project)

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

## Full File Tree (64 Python files)

```
windowsOS-coworker/
├── main.py
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
│       ├── test_disk.py
│       ├── test_memory.py
│       └── test_process.py
│
├── sessions/          (runtime — SQLite memory.db lives here)
├── traces/            (runtime — trace output)
└── init/
    └── copilot-cowork-overview.md
```

---

## How to Run

```bash
# Install dependencies (openai-agents must be installed)
pip install -r requirements.txt

# Credentials are loaded automatically from .env — no manual set needed
# .env contains: OPENAI_API_KEY, OPENAI_BASE_URL, AGENT_MODEL

# Start the app
python main.py
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
| **Phase 3 — Desktop UI** | ⬜ Pending | Rich desktop chat interface, approval cards, audit viewer, status dashboard |
| **Phase 4 — Advanced** | ⬜ Pending | Scheduled prompts, proactive alerts, custom plugins, multi-machine support |
