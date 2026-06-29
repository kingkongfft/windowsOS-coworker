from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# LLM / Agent
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
AGENT_MODEL: str = os.environ.get("AGENT_MODEL", "gpt-4o")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent
SESSIONS_DIR: Path = BASE_DIR / "sessions"
TRACES_DIR: Path = BASE_DIR / "traces"
AUDIT_LOG_PATH: Path = BASE_DIR / "audit.jsonl"

# Ensure runtime directories exist
SESSIONS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------
# When True the approval gate auto-approves medium-risk actions (useful for
# automated testing — never set True in production).
AUTO_APPROVE_MEDIUM: bool = (
    os.environ.get("AUTO_APPROVE_MEDIUM", "false").lower() == "true"
)
