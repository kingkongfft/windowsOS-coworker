# windowsOS-coworker — Developing Status

> Date: 2026-06-29
> Phase: Phase 1 — Foundation (MVP) **Complete**

---

## What was just built — Phase 1 complete

### Project scaffolding
- `pyproject.toml` — ruff, mypy, pytest config
- `requirements.txt` — all dependencies
- `config.py` — API key, model, paths, auto-approve flag

### `core/` — infrastructure layer

| File | Purpose |
|---|---|
| `exceptions.py` | `SkillExecutionError`, `ApprovalRequiredError`, `ElevationRequiredError`, `PowerShellError` |
| `risk.py` | `Risk` enum (LOW/MEDIUM/HIGH) + `@risk()` decorator + `get_risk()` |
| `powershell.py` | `run_ps()` — safe PowerShell wrapper, never shell-string interpolation, raises typed exceptions |
| `audit_log.py` | Append-only `.jsonl` audit trail — `log_tool_call`, `log_tool_result`, `log_session_start`, `tail()` |
| `approval.py` | Rich CLI approval gate — auto for LOW, one-click for MEDIUM, explicit type-to-confirm for HIGH |

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
- `/audit`, `/clear`, `/help` slash commands
- `Runner.run()` with full message history passed on each turn

### `tests/`

| Test File | Coverage |
|---|---|
| `tests/core/test_risk.py` | Risk enum, `@risk` decorator, `get_risk` default |
| `tests/core/test_audit_log.py` | All log functions, `tail()`, thread-safe writes |
| `tests/core/test_powershell.py` | `run_ps` success, flags, errors, elevation, output stripping |
| `tests/skills/test_disk.py` | `get_disk_usage`, `list_partitions` (mocked psutil) |
| `tests/skills/test_memory.py` | `get_memory_usage`, `list_top_memory_processes` (mocked psutil) |
| `tests/skills/test_process.py` | `list_processes`, `find_process_by_name`, `kill_process` (mocked psutil) |

---

## Full File Tree (62 Python files)

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
│   └── approval.py
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
│   ├── orchestrator.py
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
│   │   └── test_powershell.py
│   └── skills/
│       ├── test_disk.py
│       ├── test_memory.py
│       └── test_process.py
│
├── sessions/          (runtime — SQLite session storage)
├── traces/            (runtime — trace output)
└── init/
    └── copilot-cowork-overview.md
```

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
set OPENAI_API_KEY=sk-...

# Start the app
python main.py
```

### In-app commands

| Command | Description |
|---|---|
| `/audit` | Show last 20 audit log entries |
| `/clear` | Clear conversation history |
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
| **Phase 2 — Core Skills** | ⬜ Pending | Medium/high-risk flow end-to-end, session persistence, error retry logic |
| **Phase 3 — Desktop UI** | ⬜ Pending | Rich desktop chat interface, approval cards, audit viewer, status dashboard |
| **Phase 4 — Advanced** | ⬜ Pending | Scheduled prompts, proactive alerts, custom plugins, multi-machine support |
