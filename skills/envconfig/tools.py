from __future__ import annotations

import os

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_env_variables(scope: str = "all") -> dict[str, str]:
    """List environment variables.

    Args:
        scope: 'all' for current process, 'user' for user-level, 'system' for system-level.

    Returns:
        A dict with status and an 'variables' string.
    """
    try:
        if scope == "all":
            lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
            return {"status": "ok", "variables": "\n".join(lines)}
        target = "User" if scope == "user" else "Machine"
        result = run_ps(
            f"[System.Environment]::GetEnvironmentVariables([System.EnvironmentVariableTarget]::{target}) | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "variables": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_env_variable(name: str) -> dict[str, str]:
    """Get the value of a specific environment variable.

    Args:
        name: Environment variable name (case-insensitive on Windows).

    Returns:
        A dict with status, name, and value.
    """
    try:
        value = os.environ.get(name)
        if value is None:
            return {
                "status": "error",
                "message": f"Environment variable '{name}' not found.",
            }
        return {"status": "ok", "name": name, "value": value}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_path_entries() -> dict[str, str]:
    """List all entries in the PATH environment variable.

    Returns:
        A dict with status and a numbered 'entries' list string.
    """
    try:
        path_val = os.environ.get("PATH", "")
        entries = [e.strip() for e in path_val.split(";") if e.strip()]
        lines = [f"{i + 1:3}. {e}" for i, e in enumerate(entries)]
        return {"status": "ok", "entries": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_power_plans() -> dict[str, str]:
    """List all available Windows power plans.

    Returns:
        A dict with status and a 'plans' table string.
    """
    try:
        result = run_ps("powercfg /list | Out-String")
        return {"status": "ok", "plans": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_windows_features() -> dict[str, str]:
    """List installed and available Windows optional features.

    Returns:
        A dict with status and a 'features' table string.
    """
    try:
        result = run_ps(
            "Get-WindowsOptionalFeature -Online -ErrorAction SilentlyContinue | "
            "Select-Object FeatureName, State | Sort-Object FeatureName | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "features": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def set_power_plan(plan: str = "balanced") -> dict[str, str]:
    """Activate a Windows power plan by friendly name.

    Args:
        plan: One of: balanced, high_performance, power_saver.

    Returns:
        A dict with status and message.
    """
    plan_guids = {
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
    }
    if plan not in plan_guids:
        return {
            "status": "error",
            "message": f"Unknown plan '{plan}'. Choose: {list(plan_guids)}",
        }
    try:
        run_ps(f"powercfg /setactive {plan_guids[plan]}")
        return {"status": "ok", "message": f"Power plan set to '{plan}'."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def set_env_variable(name: str, value: str, scope: str = "user") -> dict[str, str]:
    """Set an environment variable persistently (user or system scope).

    Args:
        name: Name of the environment variable.
        value: Value to assign.
        scope: 'user' or 'system'. System scope requires admin privileges.

    Returns:
        A dict with status and message.
    """
    try:
        target = "User" if scope == "user" else "Machine"
        run_ps(
            f"[System.Environment]::SetEnvironmentVariable('{name}', '{value}', "
            f"[System.EnvironmentVariableTarget]::{target})"
        )
        return {"status": "ok", "message": f"Set {scope} env var {name}={value}."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def delete_env_variable(name: str, scope: str = "user") -> dict[str, str]:
    """Remove an environment variable persistently.

    Args:
        name: Name of the environment variable to remove.
        scope: 'user' or 'system'.

    Returns:
        A dict with status and message.
    """
    try:
        target = "User" if scope == "user" else "Machine"
        run_ps(
            f"[System.Environment]::SetEnvironmentVariable('{name}', $null, "
            f"[System.EnvironmentVariableTarget]::{target})"
        )
        return {"status": "ok", "message": f"Removed {scope} env var '{name}'."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def add_to_path(directory: str, scope: str = "user") -> dict[str, str]:
    """Add a directory to the PATH environment variable persistently.

    Args:
        directory: The directory path to add to PATH.
        scope: 'user' or 'system'.

    Returns:
        A dict with status and message.
    """
    try:
        target = "User" if scope == "user" else "Machine"
        run_ps(
            f"$current = [System.Environment]::GetEnvironmentVariable('PATH', '{target}'); "
            f"if ($current -notlike '*{directory}*') {{ "
            f"[System.Environment]::SetEnvironmentVariable('PATH', \"$current;{directory}\", '{target}') }}"
        )
        return {"status": "ok", "message": f"Added '{directory}' to {scope} PATH."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def remove_from_path(directory: str, scope: str = "user") -> dict[str, str]:
    """Remove a directory from the PATH environment variable.

    Args:
        directory: The directory path to remove from PATH.
        scope: 'user' or 'system'.

    Returns:
        A dict with status and message.
    """
    try:
        target = "User" if scope == "user" else "Machine"
        run_ps(
            f"$current = [System.Environment]::GetEnvironmentVariable('PATH', '{target}'); "
            f"$new = ($current -split ';' | Where-Object {{ $_ -ne '{directory}' }}) -join ';'; "
            f"[System.Environment]::SetEnvironmentVariable('PATH', $new, '{target}')"
        )
        return {"status": "ok", "message": f"Removed '{directory}' from {scope} PATH."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def enable_windows_feature(feature_name: str) -> dict[str, str]:
    """Enable a Windows optional feature.

    Args:
        feature_name: The feature name (e.g. 'Microsoft-Windows-Subsystem-Linux').

    Returns:
        A dict with status and message. A reboot may be required.
    """
    try:
        result = run_ps(
            f"Enable-WindowsOptionalFeature -Online -FeatureName '{feature_name}' -NoRestart -ErrorAction Stop | Out-String",
            timeout=600,
        )
        return {
            "status": "ok",
            "message": result.stdout
            or f"Feature '{feature_name}' enabled. Reboot may be required.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def disable_windows_feature(feature_name: str) -> dict[str, str]:
    """Disable a Windows optional feature.

    Args:
        feature_name: The feature name.

    Returns:
        A dict with status and message.
    """
    try:
        result = run_ps(
            f"Disable-WindowsOptionalFeature -Online -FeatureName '{feature_name}' -NoRestart -ErrorAction Stop | Out-String",
            timeout=600,
        )
        return {
            "status": "ok",
            "message": result.stdout or f"Feature '{feature_name}' disabled.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
