#!/usr/bin/env python3
"""Pre-commit hook: scan staged files for hardcoded secrets using detect-secrets."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASELINE_PATH = Path(".secrets.baseline")
FILES = sys.argv[1:]

if not FILES:
    sys.exit(0)

# Run detect-secrets scan on the provided files
result = subprocess.run(
    [sys.executable, "-m", "detect_secrets", "scan"] + FILES,
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    print(result.stderr)
    sys.exit(result.returncode)

try:
    scan_output = json.loads(result.stdout)
except json.JSONDecodeError:
    # Unexpected output — fail safe
    print("detect-secrets: could not parse scan output")
    sys.exit(1)

# Load the baseline to allow already-acknowledged secrets through
baseline: dict = {}
if BASELINE_PATH.exists():
    try:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass

baseline_results: dict = baseline.get("results", {})
new_results: dict = scan_output.get("results", {})

# Find secrets in the scan that are NOT in the baseline
violations: list[tuple[str, dict]] = []
for filepath, findings in new_results.items():
    known = {
        (s.get("type"), s.get("line_number"))
        for s in baseline_results.get(filepath, [])
    }
    for finding in findings:
        key = (finding.get("type"), finding.get("line_number"))
        if key not in known:
            violations.append((filepath, finding))

if violations:
    print("\n" + "=" * 65)
    print("  COMMIT BLOCKED: hardcoded secret(s) detected in staged files")
    print("=" * 65)
    for filepath, finding in violations:
        line = finding.get("line_number", "?")
        kind = finding.get("type", "unknown")
        print(f"  [BLOCKED]  {filepath}:{line}  ({kind})")
    print()
    print("  Remove the secret from the file, then re-stage.")
    print("  If this is a false positive, run:")
    print("    python -m detect_secrets scan > .secrets.baseline")
    print("  and commit the updated baseline.")
    print("=" * 65 + "\n")
    sys.exit(1)

sys.exit(0)
