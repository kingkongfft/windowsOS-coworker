# windowsOS-coworker — Project Planning

> Status: Pre-development planning
> Last updated: 2026-06-29

---

## 1. Vision

Build a local Windows desktop app that acts as an AI-powered coworker for DevOps and ITOps engineers. The user describes a task in plain English; the agent plans it, executes it step by step using built-in OS skills, and asks for human approval before any destructive or high-risk action.

Inspired by Microsoft 365 Copilot Cowork, but at the **OS operations layer** — not the productivity layer.

---

## 2. Core Design Principles

| Principle | Description |
|---|---|
| **Natural language first** | Every operation starts with a plain English prompt |
| **Skills-based architecture** | Each capability is an isolated, composable skill with defined tools |
| **Human-in-the-loop by default** | Risk-rated actions (medium/high) require explicit user approval before execution |
| **Audit everything** | Every tool call, result, and approval decision is traced and logged |
| **Fail safe** | On ambiguity or unexpected state, the agent pauses and asks rather than guessing |
| **Least privilege** | Tools request only the permissions they need; no blanket admin escalation |

---

## 3. Agent Architecture

```
User (natural language prompt)
          │
          ▼
  ┌─────────────────────┐
  │  Orchestrator Agent  │  ← routes intent, manages conversation state,
  │  (triage + planner)  │    enforces human-in-the-loop, aggregates results
  └──────────┬──────────┘
             │  handoffs
    ┌────────┼──────────────────────────────────────┐
    │        │                                      │
    ▼        ▼                                      ▼
 App      Patch &       Resource &      System      Diagnostics
 Skill    Update        Process         Config       & Reporting
 Agent    Skill Agent   Skill Agent     Skill Agent  Skill Agent
```

Each **Skill Agent** is an `openai-agents` `Agent` with:
- A focused system prompt scoped to its domain
- A set of Python function tools (see Section 5)
- Its own guardrails for input validation
- Risk annotations on each tool (`low` / `medium` / `high`)

The **Orchestrator Agent** never executes OS commands directly. It delegates via handoffs and surfaces approvals to the user.

---

## 4. Skill Domains (Built-in Skills)

Analogous to Copilot Cowork's built-in skills (Word, Excel, Email…), windowsOS-coworker ships with the following built-in skill domains:

| # | Skill Domain | Agent | Purpose |
|---|---|---|---|
| 1 | App Management | `AppSkillAgent` | Install, update, uninstall, list software |
| 2 | Patch & Updates | `PatchSkillAgent` | Check, apply, rollback Windows updates |
| 3 | Disk Management | `DiskSkillAgent` | Cleanup, defrag, quota, partition info |
| 4 | Memory Management | `MemorySkillAgent` | Release memory, identify hogs, paging config |
| 5 | CPU Management | `CpuSkillAgent` | Affinity, priority, identify high-CPU processes |
| 6 | Process Management | `ProcessSkillAgent` | List, kill, suspend, inspect processes |
| 7 | Service Control | `ServiceSkillAgent` | Start/stop/restart/configure Windows services |
| 8 | Network Management | `NetworkSkillAgent` | Adapter info, firewall, DNS flush, connectivity |
| 9 | User & Access | `UserSkillAgent` | Local users, groups, permissions, password policy |
| 10 | Event Log Analysis | `EventLogSkillAgent` | Query, summarize, export Event Logs |
| 11 | Registry Operations | `RegistrySkillAgent` | Read, write, backup, restore registry keys |
| 12 | Scheduled Tasks | `TaskSchedulerSkillAgent` | Create, list, modify, delete scheduled tasks |
| 13 | System Diagnostics | `DiagnosticsSkillAgent` | sfc, DISM, health checks, system reports |
| 14 | Environment & Config | `EnvConfigSkillAgent` | Env vars, PATH, system settings, power plans |
| 15 | Security & Compliance | `SecuritySkillAgent` | BitLocker status, audit policy, defender status |

---

## 5. Built-in Command Skills (Tool Catalog)

Each skill domain exposes a set of **command skills** — Python functions decorated as `@function_tool` in the OpenAI Agents SDK. Below is the full planned catalog.

### 5.1 App Management Skills (`AppSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_installed_apps` | low | List all installed applications with version info | `winget list` / WMI `Win32_Product` |
| `search_available_app` | low | Search for an app in winget catalog | `winget search <query>` |
| `install_app` | **high** | Install an application by name or ID | `winget install <id> --silent` |
| `uninstall_app` | **high** | Uninstall an application by name or ID | `winget uninstall <id> --silent` |
| `update_app` | medium | Update a specific app to the latest version | `winget upgrade <id>` |
| `update_all_apps` | **high** | Update all installed apps | `winget upgrade --all` |
| `get_app_info` | low | Get detailed info about an installed app | `winget show <id>` |
| `check_app_installed` | low | Check whether a specific app is installed | `winget list --name <name>` |

### 5.2 Patch & Update Skills (`PatchSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `check_pending_updates` | low | List available Windows updates | `PSWindowsUpdate` / Windows Update Agent API |
| `install_updates` | **high** | Install pending updates (optionally filter by KB) | `Install-WindowsUpdate` |
| `install_security_updates_only` | **high** | Install only security-classified updates | `Install-WindowsUpdate -Category Security` |
| `rollback_update` | **high** | Uninstall a specific KB update | `wusa /uninstall /kb:<number>` |
| `get_update_history` | low | Show history of installed updates | `Get-WUHistory` / `Get-HotFix` |
| `pause_windows_update` | medium | Pause automatic Windows updates | Registry / `UsoClient` |
| `resume_windows_update` | medium | Resume automatic Windows updates | Registry / `UsoClient` |
| `schedule_update_reboot` | medium | Schedule a reboot for update completion | `shutdown /r /t <seconds>` |

### 5.3 Disk Management Skills (`DiskSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `get_disk_usage` | low | Show disk space usage per drive | `psutil.disk_usage` |
| `list_large_files` | low | Find files above a size threshold | PowerShell `Get-ChildItem` + sort |
| `clean_temp_files` | medium | Delete temp files (user + system) | `cleanmgr /sagerun` / manual temp dirs |
| `clean_recycle_bin` | medium | Empty the Recycle Bin | PowerShell `Clear-RecycleBin` |
| `clean_windows_update_cache` | medium | Remove Windows Update download cache | `Stop-Service wuauserv` + delete `SoftwareDistribution\Download` |
| `clean_browser_cache` | medium | Clear browser caches (Chrome, Edge, Firefox) | Profile cache directories |
| `analyze_disk_usage` | low | Show top folders by size | PowerShell `Get-ChildItem` + measure |
| `defrag_drive` | medium | Defragment or optimize a drive | `defrag <drive> /U /V` |
| `get_drive_health` | low | Check drive SMART health status | `Get-PhysicalDisk` / `wmic diskdrive` |
| `list_partitions` | low | List disk partitions and volumes | `Get-Partition` / `diskpart` |

### 5.4 Memory Management Skills (`MemorySkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `get_memory_usage` | low | Show total, used, and free RAM | `psutil.virtual_memory()` |
| `list_top_memory_processes` | low | List processes consuming the most memory | `psutil.process_iter` sorted by `memory_percent` |
| `release_standby_memory` | medium | Release Windows standby/cached memory | `RAMMap` CLI / `EmptyWorkingSet` API |
| `clear_file_system_cache` | medium | Clear the OS file system cache | `RAMMap` / low-level API calls |
| `get_paging_file_info` | low | Show paging file size and location | WMI `Win32_PageFileUsage` |
| `set_paging_file_size` | **high** | Resize or relocate the paging file | WMI `Win32_PageFileSetting` |
| `identify_memory_leak_suspects` | low | Flag processes with growing memory over time | Repeated `psutil` polling + delta analysis |

### 5.5 CPU Management Skills (`CpuSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `get_cpu_usage` | low | Show overall and per-core CPU usage | `psutil.cpu_percent(percpu=True)` |
| `list_top_cpu_processes` | low | List processes consuming the most CPU | `psutil.process_iter` sorted by `cpu_percent` |
| `set_process_priority` | medium | Change the priority of a running process | `psutil.Process.nice()` |
| `set_process_affinity` | medium | Pin a process to specific CPU cores | `psutil.Process.cpu_affinity()` |
| `kill_high_cpu_process` | **high** | Terminate a process exceeding a CPU threshold | `psutil.Process.kill()` |
| `get_cpu_temperature` | low | Read CPU temperature sensors (if available) | `wmi` / `OpenHardwareMonitor` COM |
| `get_power_plan` | low | Show active Windows power plan | `powercfg /getactivescheme` |
| `set_power_plan` | medium | Switch active power plan (balanced/high-perf/saver) | `powercfg /setactive <guid>` |

### 5.6 Process Management Skills (`ProcessSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_processes` | low | List all running processes with PID, CPU, memory | `psutil.process_iter` |
| `get_process_details` | low | Get full details for a specific process by name or PID | `psutil.Process` |
| `find_process_by_name` | low | Search processes by name pattern | `psutil.process_iter` + filter |
| `kill_process` | **high** | Terminate a process by PID or name | `psutil.Process.kill()` |
| `suspend_process` | medium | Suspend (pause) a process | `psutil.Process.suspend()` |
| `resume_process` | medium | Resume a suspended process | `psutil.Process.resume()` |
| `get_process_open_files` | low | List files opened by a process | `psutil.Process.open_files()` |
| `get_process_network_connections` | low | Show network connections of a process | `psutil.Process.connections()` |

### 5.7 Service Control Skills (`ServiceSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_services` | low | List all Windows services and their status | `psutil.win_service_iter()` |
| `get_service_status` | low | Get status of a specific service | `psutil.win_service_get()` |
| `start_service` | medium | Start a stopped service | `sc start <name>` / `pywin32` |
| `stop_service` | **high** | Stop a running service | `sc stop <name>` / `pywin32` |
| `restart_service` | medium | Restart a service | stop → start sequence |
| `set_service_startup_type` | **high** | Change service startup type (auto/manual/disabled) | `sc config <name> start=<type>` |
| `get_service_dependencies` | low | Show what a service depends on | `sc qc <name>` |
| `list_failed_services` | low | List services that have failed or stopped unexpectedly | `Get-Service` + status filter |

### 5.8 Network Management Skills (`NetworkSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `get_network_adapters` | low | List network adapters and IP configuration | `psutil.net_if_addrs()` / `ipconfig` |
| `get_network_stats` | low | Show bytes sent/received per adapter | `psutil.net_io_counters()` |
| `test_connectivity` | low | Ping a host or test TCP port reachability | `ping` / `socket.connect` |
| `flush_dns_cache` | medium | Flush the local DNS resolver cache | `ipconfig /flushdns` |
| `get_active_connections` | low | List active TCP/UDP connections | `psutil.net_connections()` |
| `list_firewall_rules` | low | List Windows Firewall rules | `Get-NetFirewallRule` |
| `add_firewall_rule` | **high** | Add an inbound or outbound firewall rule | `New-NetFirewallRule` |
| `remove_firewall_rule` | **high** | Remove a firewall rule by name | `Remove-NetFirewallRule` |
| `reset_network_stack` | **high** | Reset TCP/IP stack and Winsock | `netsh int ip reset` + `netsh winsock reset` |
| `get_dns_settings` | low | Show DNS server configuration | `Get-DnsClientServerAddress` |
| `set_dns_servers` | **high** | Set DNS servers for an adapter | `Set-DnsClientServerAddress` |

### 5.9 User & Access Skills (`UserSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_local_users` | low | List all local user accounts | `Get-LocalUser` |
| `get_user_info` | low | Get details for a specific local user | `Get-LocalUser -Name <name>` |
| `create_local_user` | **high** | Create a new local user account | `New-LocalUser` |
| `disable_local_user` | **high** | Disable a local user account | `Disable-LocalUser` |
| `enable_local_user` | medium | Enable a disabled local user account | `Enable-LocalUser` |
| `reset_local_user_password` | **high** | Reset a local user's password | `Set-LocalUser -Password` |
| `list_local_groups` | low | List all local groups and their members | `Get-LocalGroup` |
| `add_user_to_group` | **high** | Add a user to a local group | `Add-LocalGroupMember` |
| `remove_user_from_group` | **high** | Remove a user from a local group | `Remove-LocalGroupMember` |
| `get_logged_on_users` | low | Show currently logged-on users | `query user` / WMI |

### 5.10 Event Log Skills (`EventLogSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_event_logs` | low | List available Windows Event Log channels | `Get-WinEvent -ListLog *` |
| `query_event_log` | low | Query events by log, level, time range, or keyword | `Get-WinEvent -FilterHashtable` |
| `get_recent_errors` | low | Summarize recent Error/Critical events | `Get-WinEvent` filtered by Level 1/2 |
| `get_system_crashes` | low | List recent system crash events (BSODs) | EventID 41 (Kernel-Power) + memory dumps |
| `get_application_errors` | low | List recent application error events | Application log, Level=Error |
| `export_event_log` | low | Export event log entries to CSV or JSON | `Export-Csv` / custom serializer |
| `clear_event_log` | **high** | Clear a specific event log channel | `Clear-EventLog` / `wevtutil cl` |
| `summarize_event_log` | low | AI-generated plain-English summary of recent events | LLM sub-call on query results |

### 5.11 Registry Skills (`RegistrySkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `read_registry_key` | low | Read a registry key and its values | `winreg.OpenKey` + `QueryValue` |
| `list_registry_subkeys` | low | List subkeys under a registry path | `winreg.EnumKey` |
| `write_registry_value` | **high** | Write a value to a registry key | `winreg.SetValueEx` |
| `delete_registry_value` | **high** | Delete a specific registry value | `winreg.DeleteValue` |
| `delete_registry_key` | **high** | Delete a registry key and all its values | `winreg.DeleteKey` |
| `backup_registry_key` | low | Export a registry key to a .reg file | `reg export <path> <file>` |
| `restore_registry_key` | **high** | Import/restore a registry key from a .reg file | `reg import <file>` |
| `search_registry` | low | Search for a value or key name pattern | Recursive `winreg` traversal |

### 5.12 Scheduled Task Skills (`TaskSchedulerSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_scheduled_tasks` | low | List all scheduled tasks | `Get-ScheduledTask` |
| `get_task_details` | low | Get details of a specific task | `Get-ScheduledTask -TaskName <name>` |
| `run_task_now` | medium | Trigger a scheduled task immediately | `Start-ScheduledTask` |
| `enable_task` | medium | Enable a disabled scheduled task | `Enable-ScheduledTask` |
| `disable_task` | medium | Disable a scheduled task | `Disable-ScheduledTask` |
| `create_task` | **high** | Create a new scheduled task | `Register-ScheduledTask` |
| `delete_task` | **high** | Delete a scheduled task | `Unregister-ScheduledTask` |
| `get_task_run_history` | low | Show last run results and times for a task | `Get-ScheduledTaskInfo` |

### 5.13 System Diagnostics Skills (`DiagnosticsSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `run_sfc_scan` | medium | Run System File Checker (sfc /scannow) | `sfc /scannow` |
| `run_dism_health_check` | medium | Run DISM to check and repair Windows image | `DISM /Online /Cleanup-Image /CheckHealth` |
| `run_dism_restore_health` | **high** | Run full DISM repair (downloads from Windows Update) | `DISM /Online /Cleanup-Image /RestoreHealth` |
| `get_system_uptime` | low | Show system boot time and uptime | `psutil.boot_time()` |
| `get_system_info` | low | Show OS version, build, hardware summary | `platform` + WMI `Win32_ComputerSystem` |
| `check_disk_errors` | medium | Run chkdsk scan on a volume | `chkdsk <drive> /scan` |
| `get_reliability_history` | low | Show Windows Reliability Monitor history | WMI `Win32_ReliabilityRecords` |
| `generate_system_report` | low | Generate a full HTML system report | `msinfo32 /report` / custom aggregation |
| `get_startup_items` | low | List programs that run at startup | `Get-CimInstance Win32_StartupCommand` |
| `disable_startup_item` | medium | Disable a startup program | Registry / Task Manager startup key |

### 5.14 Environment & Config Skills (`EnvConfigSkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `list_env_variables` | low | List all environment variables (user + system) | `os.environ` / registry env keys |
| `get_env_variable` | low | Get the value of a specific env variable | `os.environ.get` |
| `set_env_variable` | **high** | Set a system or user environment variable persistently | `setx` / registry `Environment` key |
| `delete_env_variable` | **high** | Remove an environment variable | Registry deletion |
| `get_path_entries` | low | List all entries in the PATH variable | Parse `PATH` env var |
| `add_to_path` | **high** | Add a directory to the PATH variable | Registry `Environment\Path` update |
| `remove_from_path` | **high** | Remove a directory from PATH | Registry `Environment\Path` update |
| `get_power_plans` | low | List available Windows power plans | `powercfg /list` |
| `set_power_plan` | medium | Activate a power plan by name | `powercfg /setactive <guid>` |
| `get_windows_features` | low | List installed/available Windows optional features | `Get-WindowsOptionalFeature` |
| `enable_windows_feature` | **high** | Enable a Windows optional feature | `Enable-WindowsOptionalFeature` |
| `disable_windows_feature` | **high** | Disable a Windows optional feature | `Disable-WindowsOptionalFeature` |

### 5.15 Security & Compliance Skills (`SecuritySkillAgent`)

| Command Skill | Risk | Description | Under the Hood |
|---|---|---|---|
| `get_defender_status` | low | Show Windows Defender / antivirus status | `Get-MpComputerStatus` |
| `run_defender_quick_scan` | medium | Trigger a Windows Defender quick scan | `Start-MpScan -ScanType QuickScan` |
| `get_firewall_status` | low | Show Windows Firewall status per profile | `Get-NetFirewallProfile` |
| `get_bitlocker_status` | low | Show BitLocker encryption status per volume | `Get-BitLockerVolume` |
| `enable_bitlocker` | **high** | Enable BitLocker on a drive | `Enable-BitLocker` |
| `get_audit_policy` | low | Show local audit policy settings | `auditpol /get /category:*` |
| `list_open_shares` | low | List SMB shares on the machine | `Get-SmbShare` |
| `check_uac_level` | low | Check User Account Control configuration | Registry `ConsentPromptBehaviorAdmin` |
| `list_installed_certificates` | low | List certificates in local cert stores | `Get-ChildItem Cert:\` |
| `scan_open_ports` | low | List open listening ports on the machine | `netstat -ano` / `psutil.net_connections` |

---

## 6. Risk Classification & Human-in-the-Loop

Every command skill carries a risk level. The Orchestrator Agent enforces approval gates based on this classification.

| Risk Level | Behavior | Examples |
|---|---|---|
| **low** | Executes immediately, result shown in chat | `get_memory_usage`, `list_processes`, `query_event_log` |
| **medium** | Shows a preview of what will happen, one-click confirm | `clean_temp_files`, `restart_service`, `flush_dns_cache` |
| **high** | Shows detailed impact summary, explicit typed/clicked confirmation required | `install_app`, `kill_process`, `delete_registry_key`, `reset_network_stack` |

High-risk actions also write an entry to the audit log before and after execution.

---

## 7. Conversation Flow

```
User: "My laptop is running slow, fix it"
          │
          ▼
  Orchestrator Agent
  ├── Assess: query CPU, memory, disk usage  (low risk → auto-execute)
  ├── Report findings to user
  ├── Propose plan:
  │     1. Kill top CPU hog process?         (high risk → ask)
  │     2. Release standby memory?           (medium risk → confirm)
  │     3. Clean temp files?                 (medium risk → confirm)
  │     4. Clean Windows Update cache?       (medium risk → confirm)
  ├── User approves each step
  └── Execute approved steps, report results
```

---

## 8. Project File Structure (Planned)

```
windowsOS-coworker/
│
├── main.py                         # Entry point — starts the UI and agent loop
│
├── agents/
│   ├── orchestrator.py             # Orchestrator Agent definition
│   ├── app_skill_agent.py          # App Management Skill Agent
│   ├── patch_skill_agent.py        # Patch & Update Skill Agent
│   ├── disk_skill_agent.py         # Disk Management Skill Agent
│   ├── memory_skill_agent.py       # Memory Management Skill Agent
│   ├── cpu_skill_agent.py          # CPU Management Skill Agent
│   ├── process_skill_agent.py      # Process Management Skill Agent
│   ├── service_skill_agent.py      # Service Control Skill Agent
│   ├── network_skill_agent.py      # Network Management Skill Agent
│   ├── user_skill_agent.py         # User & Access Skill Agent
│   ├── eventlog_skill_agent.py     # Event Log Skill Agent
│   ├── registry_skill_agent.py     # Registry Skill Agent
│   ├── taskscheduler_skill_agent.py# Scheduled Task Skill Agent
│   ├── diagnostics_skill_agent.py  # System Diagnostics Skill Agent
│   ├── envconfig_skill_agent.py    # Environment & Config Skill Agent
│   └── security_skill_agent.py    # Security & Compliance Skill Agent
│
├── skills/                         # Tool implementations (function tools)
│   ├── app/
│   ├── patch/
│   ├── disk/
│   ├── memory/
│   ├── cpu/
│   ├── process/
│   ├── service/
│   ├── network/
│   ├── user/
│   ├── eventlog/
│   ├── registry/
│   ├── taskscheduler/
│   ├── diagnostics/
│   ├── envconfig/
│   └── security/
│
├── core/
│   ├── approval.py                 # Human-in-the-loop approval gate logic
│   ├── audit_log.py                # Audit trail writer
│   ├── risk.py                     # Risk classification constants & decorators
│   └── powershell.py               # PowerShell execution helper
│
├── ui/
│   └── app.py                      # Desktop UI (chat interface)
│
├── sessions/                       # SQLite session storage
│
├── traces/                         # Local trace output directory
│
├── config.py                       # App configuration (model, API key, log paths)
├── requirements.txt
├── README.md
├── PLANNING.md
└── init/                           # Reference docs
    └── copilot-cowork-overview.md
```

---

## 9. Development Phases

### Phase 1 — Foundation (MVP)
> Goal: single working agent that can answer OS questions and run low-risk read-only skills

- [ ] Project scaffolding (folder structure, `requirements.txt`, `config.py`)
- [ ] `core/powershell.py` — safe PowerShell execution wrapper
- [ ] `core/risk.py` — risk annotation decorator
- [ ] `core/approval.py` — CLI-based approval gate (pre-UI)
- [ ] `core/audit_log.py` — append-only JSON audit log
- [ ] Implement all **low-risk** skills across all 15 domains
- [ ] Orchestrator Agent with basic routing
- [ ] CLI chat loop (`main.py` with text I/O)
- [ ] OpenAI Agents SDK tracing enabled

### Phase 2 — Core Skills
> Goal: full medium and high-risk skill coverage with approval gates working end-to-end

- [ ] Implement all **medium** and **high-risk** skills across all 15 domains
- [ ] Human-in-the-loop approval gate with risk summary display
- [ ] Per-skill agent handoff wiring in orchestrator
- [ ] Session persistence (SQLite) — retain conversation context across restarts
- [ ] Error handling — skill failures surface clean messages, agent retries intelligently

### Phase 3 — Desktop UI
> Goal: replace CLI with a proper local desktop chat interface

- [ ] Evaluate UI framework (PyQt6 vs Electron+Python vs web-based local server)
- [ ] Chat interface with streaming output
- [ ] Action approval cards (approve / reject / modify)
- [ ] Active skills panel (shows which skill agent is active, like Cowork's side panel)
- [ ] Audit log viewer
- [ ] System status dashboard (CPU, memory, disk at-a-glance)

### Phase 4 — Advanced Capabilities
> Goal: automation, scheduling, and extensibility

- [ ] **Scheduled prompts** — run a prompt on a cron-like schedule (e.g. "clean temp every Monday")
- [ ] **Proactive alerts** — agent monitors resources and alerts when thresholds are breached
- [ ] **Custom skill plugins** — allow users to add their own PowerShell/Python tools as skills
- [ ] **Multi-machine support** — connect to remote Windows machines via WinRM/SSH
- [ ] **Report generation** — produce HTML/PDF system health reports
- [ ] **Fine-tuning data collection** — capture approved action pairs for future model improvement

---

## 10. Key Dependencies

```
openai-agents          # Agent runtime, tool execution, handoffs, tracing
openai                 # LLM backend (GPT-4o)
psutil                 # Cross-platform process, CPU, memory, disk, network info
pywin32                # Windows-specific APIs (services, COM, WMI)
wmi                    # WMI queries (hardware, system info)
pywinrm                # WinRM for remote machine support (Phase 4)
pydantic               # Input validation for tool parameters
rich                   # Terminal output formatting (Phase 1 CLI)
PyQt6                  # Desktop UI (Phase 3)
```

---

## 11. Open Questions / Decisions Needed

| # | Question | Options | Notes |
|---|---|---|---|
| 1 | UI framework | PyQt6 vs local web (FastAPI + browser) vs Electron | PyQt6 is Windows-native; web is more flexible |
| 2 | Elevation strategy | Always run as admin vs UAC-prompt per high-risk action | UAC-prompt per action is safer and more transparent |
| 3 | LLM model | GPT-4o vs GPT-4o-mini vs local (Ollama) | Start with GPT-4o; local model as optional fallback |
| 4 | Remote machine support | WinRM vs SSH vs agent-on-target | Out of scope for Phase 1–3, revisit in Phase 4 |
| 5 | Session storage | SQLite (default) vs Redis | SQLite for local app; Redis only if multi-machine |
| 6 | winget availability | winget requires Windows Package Manager | Fallback to direct MSI/EXE for machines without winget |

---

## 12. Success Criteria

- User can say "my disk is full, help me clean it up" and the agent diagnoses, proposes, and executes a cleanup plan with approvals
- User can say "install Python 3.12" and the agent installs it via winget with a single approval
- User can say "what's eating my CPU?" and the agent reports the top processes in plain English
- Every destructive action is gated behind an explicit approval with a clear risk explanation
- All actions are recorded in the audit log with timestamps and outcomes
- The app runs fully locally with no data sent anywhere except the OpenAI API for LLM calls
