#!/usr/bin/env python3
"""Pre-commit hook: detect PEM private key material in staged files."""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PRIVATE_KEY_MARKERS = [
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN DSA PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN ENCRYPTED PRIVATE KEY-----",
    b"-----BEGIN PGP PRIVATE KEY BLOCK-----",
]

blocked: list[str] = []

for filepath in sys.argv[1:]:
    try:
        content = Path(filepath).read_bytes()
        if any(marker in content for marker in PRIVATE_KEY_MARKERS):
            blocked.append(filepath)
    except (OSError, PermissionError):
        pass

if blocked:
    print("\n" + "=" * 60)
    print("  COMMIT BLOCKED: private key material detected")
    print("=" * 60)
    for f in blocked:
        print(f"  [BLOCKED]  {f}")
    print()
    print("  Files contain private key headers and must NEVER be committed.")
    print("  To remove from staging:  git rm --cached <file>")
    print("=" * 60 + "\n")
    sys.exit(1)

sys.exit(0)
