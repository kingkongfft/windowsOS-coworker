from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_scheduled_tasks(folder: str = "\\") -> dict[str, str]:
    """List Windows scheduled tasks, optionally scoped to a folder.

    Args:
        folder: Task folder path (default root '\\').

    Returns:
        A dict with status and a 'tasks' table string.
    """
    try:
        result = run_ps(
            f"Get-ScheduledTask -TaskPath '{folder}*' -ErrorAction SilentlyContinue | "
            "Select-Object TaskName, TaskPath, State, @{N='LastRun';E={(Get-ScheduledTaskInfo $_.TaskName -ErrorAction SilentlyContinue).LastRunTime}} | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "tasks": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_task_details(task_name: str) -> dict[str, str]:
    """Get full details of a specific scheduled task.

    Args:
        task_name: The name of the scheduled task.

    Returns:
        A dict with status and 'details' string.
    """
    try:
        result = run_ps(
            f"Get-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop | "
            "Select-Object TaskName, TaskPath, Description, State, Triggers, Actions | "
            "Format-List | Out-String"
        )
        return {"status": "ok", "details": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_task_run_history(task_name: str) -> dict[str, str]:
    """Show last run time, result, and duration for a scheduled task.

    Args:
        task_name: The name of the scheduled task.

    Returns:
        A dict with status and 'history' string.
    """
    try:
        result = run_ps(
            f"Get-ScheduledTaskInfo -TaskName '{task_name}' -ErrorAction Stop | "
            "Select-Object LastRunTime, LastTaskResult, NextRunTime, NumberOfMissedRuns | "
            "Format-List | Out-String"
        )
        return {"status": "ok", "history": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def run_task_now(task_name: str) -> dict[str, str]:
    """Trigger a scheduled task to run immediately.

    Args:
        task_name: The name of the scheduled task.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Start-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop")
        return {"status": "ok", "message": f"Task '{task_name}' started."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def enable_task(task_name: str) -> dict[str, str]:
    """Enable a disabled scheduled task.

    Args:
        task_name: The name of the scheduled task.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Enable-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop")
        return {"status": "ok", "message": f"Task '{task_name}' enabled."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def disable_task(task_name: str) -> dict[str, str]:
    """Disable a scheduled task without deleting it.

    Args:
        task_name: The name of the scheduled task.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Disable-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop")
        return {"status": "ok", "message": f"Task '{task_name}' disabled."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def create_task(
    task_name: str,
    action_command: str,
    trigger_type: str = "Daily",
    trigger_time: str = "09:00",
    description: str = "",
) -> dict[str, str]:
    """Create a new Windows scheduled task.

    Args:
        task_name: Name for the new task.
        action_command: The command/script to run (e.g. 'powershell.exe -File C:\\script.ps1').
        trigger_type: 'Daily', 'Weekly', 'AtStartup', 'AtLogon'. Default 'Daily'.
        trigger_time: Time for Daily/Weekly triggers in HH:MM format (default '09:00').
        description: Optional description for the task.

    Returns:
        A dict with status and message.
    """
    try:
        desc_clause = f"-Description '{description}' " if description else ""
        trigger_clause = {
            "Daily": f"New-ScheduledTaskTrigger -Daily -At '{trigger_time}'",
            "Weekly": f"New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '{trigger_time}'",
            "AtStartup": "New-ScheduledTaskTrigger -AtStartup",
            "AtLogon": "New-ScheduledTaskTrigger -AtLogon",
        }.get(trigger_type, f"New-ScheduledTaskTrigger -Daily -At '{trigger_time}'")

        run_ps(
            f"$action = New-ScheduledTaskAction -Execute '{action_command}'; "
            f"$trigger = {trigger_clause}; "
            f"Register-ScheduledTask -TaskName '{task_name}' {desc_clause}"
            f"-Action $action -Trigger $trigger -RunLevel Highest -ErrorAction Stop | Out-Null"
        )
        return {"status": "ok", "message": f"Scheduled task '{task_name}' created."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def delete_task(task_name: str) -> dict[str, str]:
    """Permanently delete a scheduled task.

    Args:
        task_name: The name of the task to delete.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false -ErrorAction Stop"
        )
        return {"status": "ok", "message": f"Scheduled task '{task_name}' deleted."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
