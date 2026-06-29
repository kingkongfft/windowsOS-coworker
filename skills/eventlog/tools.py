from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_event_logs() -> dict[str, str]:
    """List all available Windows Event Log channels.

    Returns:
        A dict with status and a 'logs' list string.
    """
    try:
        result = run_ps(
            "Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | "
            "Where-Object { $_.RecordCount -gt 0 } | "
            "Select-Object LogName, RecordCount, IsEnabled | "
            "Sort-Object RecordCount -Descending | Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "logs": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_recent_errors(hours: int = 24, max_results: int = 50) -> dict[str, str]:
    """Return recent Error and Critical events from the System and Application logs.

    Args:
        hours: How far back to look (default 24 hours).
        max_results: Maximum number of events to return (default 50).

    Returns:
        A dict with status and an 'events' table string.
    """
    try:
        result = run_ps(
            f"$since = (Get-Date).AddHours(-{hours}); "
            "Get-WinEvent -FilterHashtable @{LogName='System','Application'; Level=1,2; "
            "StartTime=$since} -MaxEvents "
            + str(max_results)
            + " -ErrorAction SilentlyContinue | "
            "Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message | "
            "Format-Table -AutoSize -Wrap | Out-String"
        )
        output = (
            result.stdout.strip()
            or f"No Error/Critical events in the last {hours} hours."
        )
        return {"status": "ok", "events": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def query_event_log(
    log_name: str = "System",
    level: int = 0,
    hours: int = 12,
    keyword: str = "",
    max_results: int = 30,
) -> dict[str, str]:
    """Query a Windows Event Log with flexible filters.

    Args:
        log_name: Event log name (e.g. 'System', 'Application', 'Security').
        level: Event level: 0=all, 1=critical, 2=error, 3=warning, 4=information.
        hours: Look back this many hours (default 12).
        keyword: Filter events whose Message contains this string.
        max_results: Maximum events to return (default 30).

    Returns:
        A dict with status and an 'events' string.
    """
    try:
        level_clause = f"; Level={level}" if level > 0 else ""
        result = run_ps(
            f"$since = (Get-Date).AddHours(-{hours}); "
            f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; StartTime=$since{level_clause}}} "
            f"-MaxEvents {max_results} -ErrorAction SilentlyContinue | "
            f"{'Where-Object { $_.Message -like "*' + keyword + '*" } |' if keyword else ''}"
            "Select-Object TimeCreated, Id, LevelDisplayName, Message | "
            "Format-Table -AutoSize -Wrap | Out-String"
        )
        return {"status": "ok", "events": result.stdout or "No matching events found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_system_crashes(last_n: int = 10) -> dict[str, str]:
    """List recent unexpected system shutdowns and crashes (BSODs).

    Args:
        last_n: Number of crash events to return (default 10).

    Returns:
        A dict with status and a 'crashes' string.
    """
    try:
        result = run_ps(
            f"Get-WinEvent -FilterHashtable @{{LogName='System'; Id=41}} "
            f"-MaxEvents {last_n} -ErrorAction SilentlyContinue | "
            "Select-Object TimeCreated, Id, Message | Format-Table -AutoSize -Wrap | Out-String"
        )
        output = result.stdout.strip() or "No unexpected shutdown events found."
        return {"status": "ok", "crashes": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_application_errors(hours: int = 24, max_results: int = 20) -> dict[str, str]:
    """List recent application error events from the Application log.

    Args:
        hours: How far back to look (default 24).
        max_results: Maximum events to return (default 20).

    Returns:
        A dict with status and an 'errors' table string.
    """
    try:
        result = run_ps(
            f"$since = (Get-Date).AddHours(-{hours}); "
            "Get-WinEvent -FilterHashtable @{LogName='Application'; Level=2; StartTime=$since} "
            f"-MaxEvents {max_results} -ErrorAction SilentlyContinue | "
            "Select-Object TimeCreated, Id, ProviderName, Message | "
            "Format-Table -AutoSize -Wrap | Out-String"
        )
        output = (
            result.stdout.strip() or f"No application errors in the last {hours} hours."
        )
        return {"status": "ok", "errors": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def export_event_log(
    log_name: str = "System", output_path: str = "C:\\Temp\\events.csv", hours: int = 24
) -> dict[str, str]:
    """Export event log entries to a CSV file.

    Args:
        log_name: Event log name to export.
        output_path: Full path for the output CSV file.
        hours: How many hours of history to export (default 24).

    Returns:
        A dict with status, message, and the output path.
    """
    try:
        result = run_ps(
            f"$since = (Get-Date).AddHours(-{hours}); "
            f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; StartTime=$since}} "
            f"-ErrorAction SilentlyContinue | "
            f"Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message | "
            f"Export-Csv -Path '{output_path}' -NoTypeInformation -Encoding UTF8; "
            f"'Exported to {output_path}'"
        )
        return {"status": "ok", "message": result.stdout, "path": output_path}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def clear_event_log(log_name: str) -> dict[str, str]:
    """Clear all events from a specific Windows Event Log channel.

    Args:
        log_name: The log to clear (e.g. 'Application', 'System').

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"wevtutil cl '{log_name}'")
        return {"status": "ok", "message": f"Event log '{log_name}' cleared."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
