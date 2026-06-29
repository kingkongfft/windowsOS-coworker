#!/usr/bin/env python3
"""Pre-commit hook: block .env files from being committed."""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminals (cp1252 doesn't support box chars).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BLOCKED_NAMES = {".env"}

blocked: list[str] = []

for filepath in sys.argv[1:]:
    p = Path(filepath)
    name = p.name.lower()
    # Block .env and any variant like .env.local, .env.production, .env.staging
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        blocked.append(filepath)

if blocked:
    print("\n" + "=" * 60)
    print("  COMMIT BLOCKED: .env file(s) detected in staging area")
    print("=" * 60)
    for f in blocked:
        print(f"  [BLOCKED]  {f}")
    print()
    print("  .env files contain secrets and must NEVER be committed.")
    print("  To remove from staging:  git rm --cached <file>")
    print("  To ignore permanently:   ensure .env is in .gitignore")
    print("=" * 60 + "\n")
    sys.exit(1)

sys.exit(0)
