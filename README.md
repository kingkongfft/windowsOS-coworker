# windowsOS-coworker

A local Windows desktop app that acts as an AI-powered coworker for DevOps and ITOps engineers — inspired by [Microsoft 365 Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/), but focused entirely on **Windows OS operations**.

Built on the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/), this app uses LLM reasoning and an agentic loop to help you manage Windows systems effectively — from app installs and patching to OS resource management — all through natural language.

---

## What is windowsOS-coworker?

While Copilot Cowork handles productivity tasks (emails, meetings, documents), **windowsOS-coworker** handles the operational layer of Windows:

- **App installation & removal** — install, update, or uninstall software via natural language
- **Patch management** — check for, apply, and report on Windows updates
- **OS resource management** — monitor and manage CPU, memory, disk, and network usage
- **Process management** — inspect, kill, or prioritize running processes
- **Service control** — start, stop, restart, and configure Windows services
- **Event log analysis** — query and summarize Windows Event Logs for errors and warnings
- **Registry operations** — read and modify registry keys safely
- **Scheduled tasks** — create, update, and remove scheduled tasks
- **User & group management** — manage local users, groups, and permissions
- **System diagnostics** — run health checks and generate system reports

You describe what you need in plain English. The agent breaks it into steps, executes them, and asks for your approval before making system-level changes.

---

## Why windowsOS-coworker?

Managing Windows at scale is tedious. Scripts exist, but they're scattered, hard to compose, and require expertise. windowsOS-coworker bridges the gap:

- **Natural language interface** — no need to memorize PowerShell cmdlets or WMI queries
- **Agentic loop** — the agent plans multi-step operations, handles errors, and retries automatically
- **Human-in-the-loop** — you approve high-risk actions (e.g. uninstalling software, modifying the registry) before they execute
- **Audit trail** — every action is traced and logged so you know exactly what ran and when
- **Composable agents** — specialized sub-agents (patching agent, monitoring agent, etc.) coordinate via handoffs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent runtime | [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) (`openai-agents`) |
| LLM backend | OpenAI API (GPT-4o or compatible) |
| OS integration | Python `subprocess`, `psutil`, `winreg`, `pywin32`, PowerShell |
| UI | Local desktop app (TBD: Tkinter / PyQt / web-based) |
| Tracing | OpenAI Agents SDK built-in tracing |
| Sessions | Persistent session memory (SQLite via `openai-agents` sessions) |

---

## Architecture Overview

```
User (natural language)
        │
        ▼
  Orchestrator Agent
  ├── App Management Agent   ──► winget / msiexec / PowerShell
  ├── Patch Agent            ──► Windows Update API / PSWindowsUpdate
  ├── Resource Monitor Agent ──► psutil / WMI / perfmon
  ├── Process Agent          ──► tasklist / taskkill / WMI
  ├── Service Agent          ──► sc.exe / PowerShell services
  └── Diagnostics Agent      ──► Event Logs / sfc / DISM
```

The **Orchestrator Agent** receives user intent and delegates to specialized sub-agents via [handoffs](https://openai.github.io/openai-agents-python/handoffs/). Each sub-agent has its own tools scoped to its domain. High-risk tool calls surface a human-in-the-loop approval step before execution.

---

## Getting Started

### Prerequisites

- Windows 10/11 or Windows Server 2019+
- Python 3.11+
- An OpenAI API key

### Installation

```bash
git clone https://github.com/your-org/windowsOS-coworker.git
cd windowsOS-coworker
pip install -r requirements.txt
```

### Configuration

```bash
set OPENAI_API_KEY=sk-...
```

### Run

```bash
python main.py
```

---

## References

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [openai-agents on GitHub](https://github.com/openai/openai-agents-python)
- [Microsoft 365 Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/) — inspiration
- [OpenAI Agents SDK: Running agents](https://openai.github.io/openai-agents-python/running_agents/)
- [OpenAI Agents SDK: Multi-agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/)
- [OpenAI Agents SDK: Human in the loop](https://openai.github.io/openai-agents-python/human_in_the_loop/)
- [OpenAI Agents SDK: Tracing](https://openai.github.io/openai-agents-python/tracing/)

---

## License

MIT
