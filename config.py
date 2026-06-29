from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root, overriding any existing env vars.
# This ensures the DeepSeek key takes precedence over system-level vars
# (e.g. proxy keys set by the IDE/agent environment).
load_dotenv(Path(__file__).parent / ".env", override=True)

# ---------------------------------------------------------------------------
# LLM / Agent
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
AGENT_MODEL: str = os.environ.get("AGENT_MODEL", "gpt-4o")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent
SESSIONS_DIR: Path = BASE_DIR / "sessions"
TRACES_DIR: Path = BASE_DIR / "traces"
AUDIT_LOG_PATH: Path = BASE_DIR / "audit.jsonl"

# SQLite long-term memory database (stored inside sessions/ so it is
# covered by the existing .gitignore rule for that directory).
MEMORY_DB_PATH: Path = SESSIONS_DIR / "memory.db"

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
