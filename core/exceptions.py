from __future__ import annotations


class SkillExecutionError(Exception):
    """Raised when a tool/skill call fails during execution.

    Args:
        message: Human-readable description of what went wrong.
        tool_name: The name of the tool that failed (optional).
    """

    def __init__(self, message: str, tool_name: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(f"[{tool_name}] {message}" if tool_name else message)


class ApprovalRequiredError(Exception):
    """Raised when an action requires human approval before it can continue.

    The orchestrator catches this and surfaces the approval gate to the user.

    Args:
        message: Description of the action requiring approval.
        risk_level: 'medium' or 'high'.
    """

    def __init__(self, message: str, risk_level: str = "high") -> None:
        self.risk_level = risk_level
        super().__init__(message)


class ElevationRequiredError(Exception):
    """Raised when an action requires elevated (admin) privileges.

    Args:
        message: Description of what elevation is needed for.
    """

    def __init__(
        self, message: str = "This operation requires administrator privileges."
    ) -> None:
        super().__init__(message)


class PowerShellError(Exception):
    """Raised when a PowerShell command returns a non-zero exit code.

    Args:
        command: The PowerShell command that was run.
        returncode: The exit code returned.
        stderr: The stderr output from the command.
    """

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"PowerShell exited with code {returncode}.\nCommand: {command}\nStderr: {stderr}"
        )
