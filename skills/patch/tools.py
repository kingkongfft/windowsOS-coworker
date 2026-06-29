from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def check_pending_updates() -> dict[str, str]:
    """List available Windows updates that are pending installation.

    Returns:
        A dict with status and an 'updates' list string.
    """
    try:
        result = run_ps(
            "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5 | "
            "Select-Object HotFixID, Description, InstalledOn | Format-Table -AutoSize | Out-String"
        )
        # Try PSWindowsUpdate if available
        ps_wu = run_ps(
            "if (Get-Module -ListAvailable -Name PSWindowsUpdate) { "
            "Import-Module PSWindowsUpdate; Get-WUList | Select-Object KB, Title, Size, IsDownloaded | "
            "Format-Table -AutoSize | Out-String } else { 'PSWindowsUpdate module not installed. "
            "Showing recent hotfixes only.' }"
        )
        output = ps_wu.stdout or result.stdout
        return {"status": "ok", "updates": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_update_history(last_n: int = 20) -> dict[str, str]:
    """Show the history of installed Windows updates.

    Args:
        last_n: Number of most recent updates to show (default 20).

    Returns:
        A dict with status and an 'history' table string.
    """
    try:
        result = run_ps(
            f"Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First {last_n} | "
            "Select-Object HotFixID, Description, InstalledBy, InstalledOn | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "history": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def pause_windows_update(days: int = 7) -> dict[str, str]:
    """Pause automatic Windows updates for a specified number of days.

    Args:
        days: Number of days to pause updates (default 7, max 35).

    Returns:
        A dict with status and message.
    """
    try:
        days = min(days, 35)
        result = run_ps(
            f"$date = (Get-Date).AddDays({days}).ToString('yyyy-MM-ddTHH:mm:ssZ'); "
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings' "
            "-Name 'PauseUpdatesExpiryTime' -Value $date -ErrorAction Stop"
        )
        return {"status": "ok", "message": f"Windows updates paused for {days} days."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def resume_windows_update() -> dict[str, str]:
    """Resume automatic Windows updates (clears the pause).

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            "Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings' "
            "-Name 'PauseUpdatesExpiryTime' -ErrorAction SilentlyContinue"
        )
        return {"status": "ok", "message": "Windows updates resumed."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def schedule_update_reboot(delay_minutes: int = 30) -> dict[str, str]:
    """Schedule a system reboot to complete pending Windows updates.

    Args:
        delay_minutes: Minutes to wait before rebooting (default 30).

    Returns:
        A dict with status and message.
    """
    try:
        delay_seconds = delay_minutes * 60
        run_ps(
            f"shutdown /r /t {delay_seconds} /c 'Scheduled reboot for Windows Update'"
        )
        return {
            "status": "ok",
            "message": f"Reboot scheduled in {delay_minutes} minutes. Run 'shutdown /a' to cancel.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def install_updates(kb_filter: str = "") -> dict[str, str]:
    """Install pending Windows updates, optionally filtered by KB number.

    Requires the PSWindowsUpdate PowerShell module.

    Args:
        kb_filter: Optional KB number to target (e.g. 'KB5034441'). Empty = install all.

    Returns:
        A dict with status and installation output.
    """
    try:
        kb_clause = f"-KBArticleID '{kb_filter}'" if kb_filter else ""
        result = run_ps(
            f"Import-Module PSWindowsUpdate -ErrorAction Stop; "
            f"Install-WindowsUpdate {kb_clause} -AcceptAll -AutoReboot:$false | Out-String",
            timeout=1800,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def install_security_updates_only() -> dict[str, str]:
    """Install only security-classified Windows updates.

    Requires the PSWindowsUpdate PowerShell module.

    Returns:
        A dict with status and installation output.
    """
    try:
        result = run_ps(
            "Import-Module PSWindowsUpdate -ErrorAction Stop; "
            "Install-WindowsUpdate -Category 'Security Updates' -AcceptAll -AutoReboot:$false | Out-String",
            timeout=1800,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def rollback_update(kb_number: str) -> dict[str, str]:
    """Uninstall a specific Windows update by KB number.

    Args:
        kb_number: The KB identifier, e.g. 'KB5034441' or '5034441'.

    Returns:
        A dict with status and message.
    """
    try:
        kb = kb_number.upper().lstrip("KB").strip()
        result = run_ps(
            f"wusa /uninstall /kb:{kb} /quiet /norestart",
            timeout=300,
        )
        return {
            "status": "ok",
            "message": f"KB{kb} uninstall initiated. A reboot may be required.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
