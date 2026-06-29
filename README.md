# windowsOS-coworker

> AI-powered Windows OS operations assistant for DevOps and ITOps engineers.  
> Manage your Windows system through natural language — no PowerShell memorisation required.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4.svg)](https://www.microsoft.com/windows)

---

## What is windowsOS-coworker?

A local CLI app that uses the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) to let you manage Windows OS operations through plain English. You describe what you need; the orchestrator routes your request to the right specialist agent, executes tools, and asks for your approval before making any system-level changes.

**Works with any OpenAI-compatible API** — including DeepSeek, Azure OpenAI, Ollama, etc.

---

## Built-in Skill Agents

| Agent | Capabilities |
|---|---|
| **Disk** | Usage, partitions, large files, drive health, temp cleanup, defrag |
| **Memory** | RAM stats, top consumers, paging file, leak suspects, cache flush |
| **CPU** | Usage, top processes, temperature, power plans, priority/affinity |
| **Process** | List, inspect, find, kill, suspend, resume |
| **Service** | Start, stop, restart, configure Windows services |
| **Network** | Adapters, DNS, firewall rules, connectivity test, reset stack |
| **App** | Install, uninstall, update software via `winget` |
| **Patch** | Windows Update — check, install, pause, resume, rollback |
| **EventLog** | Query, summarise, export event logs, find errors/crashes |
| **Registry** | Read, write, backup, restore, search registry keys |
| **TaskScheduler** | List, run, enable, disable, create, delete scheduled tasks |
| **Diagnostics** | SFC, DISM, system info, uptime, startup items, reliability |
| **EnvConfig** | Environment variables, PATH entries, Windows features |
| **Security** | Defender, firewall, BitLocker, UAC, certificates, port scan |
| **User** | Local users/groups, create, disable, reset passwords |
| **Files** | Create, read, write, move, copy, delete files and directories |

---

## Quick Install

### Prerequisites

- Windows 10 / 11 or Windows Server 2019+
- Python 3.11+
- An API key for any OpenAI-compatible LLM provider

### 1. Clone the repo

```cmd
git clone https://github.com/kingkongfft/windowsOS-coworker.git
cd windowsOS-coworker
```

### 2. Install dependencies

```cmd
pip install -r requirements.txt
```

### 3. Configure your API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com
AGENT_MODEL=deepseek-chat
```

> **Using OpenAI directly?** Set `OPENAI_BASE_URL=https://api.openai.com/v1` and `AGENT_MODEL=gpt-4o`.  
> **Using Azure OpenAI?** Set the Azure endpoint URL and your deployment name as the model.

### 4. Run

```cmd
python main.py
```

---

## Usage

Once running, just type what you need:

```
You: what's my disk usage?
You: show me the top 10 memory-consuming processes
You: check if Windows Defender is running
You: create a file at C:\Users\me\notes.txt with content "hello"
You: list all failed Windows services
You: is there a pending Windows update?
```

### Built-in commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/audit` | Show last 20 audit log entries |
| `/clear` | Clear conversation history |
| `exit` / `quit` | Exit the app |

---

## Architecture

```
User (natural language)
        │
        ▼
  Orchestrator Agent
        │
        ├── DiskSkillAgent       ──► psutil / PowerShell
        ├── MemorySkillAgent     ──► psutil / WMI
        ├── CpuSkillAgent        ──► psutil / PowerShell
        ├── ProcessSkillAgent    ──► psutil
        ├── ServiceSkillAgent    ──► PowerShell / sc.exe
        ├── NetworkSkillAgent    ──► PowerShell / netsh
        ├── AppSkillAgent        ──► winget
        ├── PatchSkillAgent      ──► Windows Update / PSWindowsUpdate
        ├── EventLogSkillAgent   ──► Windows Event Log API
        ├── RegistrySkillAgent   ──► winreg / PowerShell
        ├── TaskSchedulerSkillAgent ──► schtasks / PowerShell
        ├── DiagnosticsSkillAgent   ──► sfc / DISM / WMI
        ├── EnvConfigSkillAgent  ──► Environment / PowerShell
        ├── SecuritySkillAgent   ──► Defender / BitLocker / firewall
        ├── UserSkillAgent       ──► net user / PowerShell
        └── FileSkillAgent       ──► pathlib / shutil
```

The **Orchestrator** receives user intent and delegates to specialist agents via [handoffs](https://openai.github.io/openai-agents-python/handoffs/). High-risk operations surface a human-in-the-loop approval step before execution. Every action is written to an append-only audit log.

---

## Risk Levels

All tools are annotated with a risk level that controls the approval gate:

| Level | Behaviour | Examples |
|---|---|---|
| `LOW` | Executes immediately, no prompt | Read disk usage, list processes |
| `MEDIUM` | Asks "Shall I proceed?" | Restart a service, flush DNS cache |
| `HIGH` | Requires explicit confirmation | Kill a process, write to registry, delete files |

---

## Security

- **Secrets** — API keys and credentials live in `.env` only. `.env` is `.gitignore`-d and blocked by pre-commit hooks.
- **No shell interpolation** — all PowerShell calls go through `core/powershell.py:run_ps()`, which never builds shell strings from user input.
- **Audit log** — every tool call is recorded in `audit.jsonl`.
- **Pre-commit guards** — `detect-secrets`, private key detection, and `.env` file blocking run on every `git commit`.

---

## Development

```cmd
# Run all unit tests (no real OS calls)
pytest -m "not integration"

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Lint and format
ruff format . && ruff check .

# Type check
mypy .
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent runtime | [openai-agents](https://github.com/openai/openai-agents-python) SDK |
| LLM backend | Any OpenAI-compatible API (DeepSeek, OpenAI, Azure, etc.) |
| OS integration | `psutil`, `pywin32`, `winreg`, PowerShell via subprocess |
| CLI | [Rich](https://github.com/Textualize/rich) |
| Secret scanning | [detect-secrets](https://github.com/Yelp/detect-secrets) + pre-commit |

---

## License

[MIT](LICENSE) © 2026 Water Zhong
