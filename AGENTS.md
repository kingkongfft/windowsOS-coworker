# AGENTS.md

Guidance for agentic coding agents working in this repository.
This is a greenfield Python project — no source files exist yet. Follow these
conventions from the first line of code written.

---

## Project Overview

`windowsOS-coworker` is a local Windows desktop app that uses the OpenAI Agents
SDK to let DevOps/ITOps engineers manage Windows OS operations through natural
language. Core concepts: Orchestrator Agent → Skill Agents (handoffs) → function
tools → PowerShell/WMI/psutil. See `PLANNING.md` for full architecture and skill
catalog, and `README.md` for the project summary.

---

## Build & Environment Setup

```bash
# Create and activate a virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in editable/dev mode (once setup.py or pyproject.toml exists)
pip install -e ".[dev]"
```

**Minimum Python version:** 3.11  
**Target OS:** Windows 10/11 or Windows Server 2019+  
**Required env var:** `OPENAI_API_KEY=sk-...`

---

## Run the App

```bash
python main.py
```

---

## Lint & Format

```bash
# Format with ruff (replaces black + isort)
ruff format .

# Lint with ruff
ruff check .

# Type-check with mypy
mypy .

# Run all checks in one pass
ruff format . && ruff check . && mypy .
```

**Config files:** `pyproject.toml` holds ruff and mypy settings.  
All code must pass `ruff check` and `mypy` with zero errors before committing.

---

## Testing

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/skills/test_disk.py

# Run a single test by name
pytest tests/skills/test_disk.py::test_get_disk_usage

# Run with verbose output
pytest -v

# Run only fast (non-integration) tests
pytest -m "not integration"

# Run with coverage report
pytest --cov=. --cov-report=term-missing
```

Tests live in `tests/` mirroring the source structure:
- `tests/skills/` — unit tests per skill module
- `tests/agents/` — agent routing and handoff tests
- `tests/core/` — approval gate, audit log, risk decorator tests

Mark tests that call real OS APIs or PowerShell with `@pytest.mark.integration`.
Unit tests must mock all subprocess and psutil calls.

---

## Code Style

### Formatting
- **Formatter:** `ruff format` (88-char line length, double quotes)
- **Import order:** stdlib → third-party → local, enforced by ruff `isort` rules
- No trailing whitespace. Blank line at end of file.

### Imports
```python
# Good — absolute imports, grouped
import os
import subprocess
from pathlib import Path

import psutil
from agents import Agent, Runner, function_tool

from core.risk import Risk, risk
from core.audit_log import audit
```
Never use wildcard imports (`from module import *`).

### Type Annotations
- **All** function signatures must have type annotations (args + return type).
- Use `from __future__ import annotations` at the top of every file.
- Prefer `str | None` over `Optional[str]` (Python 3.10+ union syntax).
- Use `TypedDict` or `pydantic.BaseModel` for structured tool inputs/outputs.

```python
# Good
def get_disk_usage(drive: str = "C:") -> dict[str, int]:
    ...

# Bad
def get_disk_usage(drive):
    ...
```

### Naming Conventions
| Item | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `disk_skill_agent.py` |
| Classes | `PascalCase` | `DiskSkillAgent` |
| Functions / methods | `snake_case` | `get_disk_usage` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_DRIVE` |
| Tool functions | `snake_case` verb_noun | `clean_temp_files`, `kill_process` |
| Skill agents | `<Domain>SkillAgent` | `MemorySkillAgent` |
| Risk levels | `Risk.LOW / MEDIUM / HIGH` | enum members |

### Docstrings
Every public function and class must have a docstring.
Use Google-style docstrings:

```python
def install_app(app_id: str, silent: bool = True) -> dict[str, str]:
    """Install an application via winget.

    Args:
        app_id: The winget package identifier (e.g. "Python.Python.3.12").
        silent: Whether to suppress the installer UI.

    Returns:
        A dict with keys "status" ("ok" | "error") and "message".

    Raises:
        SkillExecutionError: If winget is not available or the install fails.
    """
```

---

## Error Handling

- Define custom exceptions in `core/exceptions.py`:
  - `SkillExecutionError` — a tool/skill call failed
  - `ApprovalRequiredError` — action needs human approval before continuing
  - `ElevationRequiredError` — action needs admin privileges
- Never swallow exceptions silently. Always log then re-raise or return a
  structured error dict.
- Tool functions return `dict[str, str]` with `"status": "ok" | "error"` and a
  `"message"` field. Never raise inside a `@function_tool` — return the error
  in the dict so the agent can reason about it.

```python
# Good — structured error return from a tool
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return {"status": "ok", "message": result.stdout.strip()}
except subprocess.CalledProcessError as e:
    return {"status": "error", "message": e.stderr.strip()}
```

---

## Tool / Skill Conventions

- All tool functions live in `skills/<domain>/` and are decorated with
  `@function_tool` from the OpenAI Agents SDK.
- Every tool must be annotated with a risk level using the `@risk(Risk.HIGH)`
  decorator from `core/risk.py`. The orchestrator reads this at runtime.
- Tool docstrings become the LLM-visible tool description — write them to be
  clear and imperative ("Install an application…", not "This function installs…").
- PowerShell invocations go through `core/powershell.py:run_ps(command: str)`
  — never call `subprocess` with `powershell` directly in skill files.
- Tools must never prompt the user directly. Approval gates are handled by
  `core/approval.py`, called by the orchestrator, not inside tools.

---

## Agent Conventions

- Agent definitions live in `agents/`. Each file exports exactly one `Agent`
  instance as a module-level constant named after the domain, e.g.
  `disk_skill_agent = Agent(...)`.
- System prompts are stored as multiline string constants at the top of each
  agent file, not inline in the `Agent(...)` call.
- Handoffs are wired in `agents/orchestrator.py` only — skill agents do not
  hand off to each other.
- Never hardcode the model name in individual agent files. Read it from
  `config.AGENT_MODEL` (defaults to `"gpt-4o"`).

---

## Security & Safety Rules

- Never log or print the `OPENAI_API_KEY` or any credential.
- Never pass unsanitized user input directly to `subprocess` or PowerShell.
  Always use argument lists (`["cmd", "/c", ...]`), never shell-string
  interpolation.
- Registry write, user creation, firewall changes, and uninstall operations
  are always `Risk.HIGH` — no exceptions.
- Do not broaden a tool's risk level downward without an explicit comment
  explaining why.
