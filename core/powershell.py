from __future__ import annotations

import subprocess
from typing import NamedTuple

from core.exceptions import ElevationRequiredError, PowerShellError


class PSResult(NamedTuple):
    """Result from a PowerShell command execution.

    Attributes:
        stdout: Standard output from the command.
        stderr: Standard error from the command.
        returncode: Process exit code.
    """

    stdout: str
    stderr: str
    returncode: int


def run_ps(command: str, *, timeout: int = 120) -> PSResult:
    """Execute a PowerShell command safely and return its output.

    All PowerShell invocations in skill files must go through this function.
    Never call ``subprocess`` with ``powershell`` directly in skill files.

    The command is passed as a value to ``-Command`` — it is NOT interpolated
    into a shell string, which prevents injection attacks.

    Args:
        command: The PowerShell command string to execute.
        timeout: Maximum seconds to wait before raising ``TimeoutExpired``.
                 Defaults to 120 seconds.

    Returns:
        A :class:`PSResult` with ``stdout``, ``stderr``, and ``returncode``.

    Raises:
        ElevationRequiredError: If PowerShell reports an access-denied error.
        PowerShellError: If the command exits with a non-zero return code.
        TimeoutExpired: If the command takes longer than *timeout* seconds.
    """
    result = subprocess.run(
        [
            "powershell.exe",
            "-NonInteractive",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    ps_result = PSResult(
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        returncode=result.returncode,
    )

    if result.returncode != 0:
        stderr_lower = result.stderr.lower()
        if "access is denied" in stderr_lower or "unauthorized" in stderr_lower:
            raise ElevationRequiredError(
                f"Access denied running PowerShell command. "
                f"Try running as Administrator.\nCommand: {command}"
            )
        raise PowerShellError(
            command=command,
            returncode=result.returncode,
            stderr=result.stderr.strip(),
        )

    return ps_result
