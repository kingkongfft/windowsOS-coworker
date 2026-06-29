from __future__ import annotations

import platform

import psutil
from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_system_info() -> dict[str, str]:
    """Return a summary of OS version, hardware, and system configuration.

    Returns:
        A dict with status and system information fields.
    """
    try:
        uname = platform.uname()
        boot = psutil.boot_time()
        import datetime

        boot_dt = datetime.datetime.fromtimestamp(boot).isoformat()
        cpu_count = str(psutil.cpu_count(logical=True))
        ram_gb = f"{psutil.virtual_memory().total / 1e9:.1f}"
        return {
            "status": "ok",
            "os": uname.system,
            "version": uname.version,
            "release": uname.release,
            "machine": uname.machine,
            "processor": uname.processor,
            "hostname": uname.node,
            "cpu_cores": cpu_count,
            "ram_gb": ram_gb,
            "boot_time": boot_dt,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_system_uptime() -> dict[str, str]:
    """Show system boot time and current uptime.

    Returns:
        A dict with status, boot_time, and uptime_hours.
    """
    try:
        import datetime

        boot = psutil.boot_time()
        now = datetime.datetime.now().timestamp()
        uptime_hours = (now - boot) / 3600
        boot_dt = datetime.datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "ok",
            "boot_time": boot_dt,
            "uptime_hours": f"{uptime_hours:.1f}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_reliability_history(last_n_days: int = 7) -> dict[str, str]:
    """Show Windows Reliability Monitor history (application crashes, warnings).

    Args:
        last_n_days: How many days of history to retrieve (default 7).

    Returns:
        A dict with status and 'history' string.
    """
    try:
        result = run_ps(
            f"Get-WmiObject -Class Win32_ReliabilityRecords -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.TimeGenerated -gt (Get-Date).AddDays(-{last_n_days}).ToString('yyyyMMddHHmmss') }} | "
            "Select-Object TimeGenerated, ProductName, SourceName, Message | "
            "Sort-Object TimeGenerated -Descending | Format-Table -AutoSize -Wrap | Out-String"
        )
        output = result.stdout.strip() or "No reliability records found."
        return {"status": "ok", "history": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_startup_items() -> dict[str, str]:
    """List programs configured to run at Windows startup.

    Returns:
        A dict with status and 'startup_items' table string.
    """
    try:
        result = run_ps(
            "Get-CimInstance Win32_StartupCommand | "
            "Select-Object Name, Command, Location, User | Format-Table -AutoSize -Wrap | Out-String"
        )
        return {"status": "ok", "startup_items": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def generate_system_report(
    output_path: str = "C:\\Temp\\system_report.txt",
) -> dict[str, str]:
    """Generate a comprehensive system information report.

    Args:
        output_path: Path to save the report file.

    Returns:
        A dict with status, message, and the report file path.
    """
    try:
        run_ps(f"msinfo32 /report '{output_path}'", timeout=60)
        return {
            "status": "ok",
            "message": f"System report saved to {output_path}.",
            "path": output_path,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def run_sfc_scan() -> dict[str, str]:
    """Run the Windows System File Checker (sfc /scannow).

    Requires administrator privileges.

    Returns:
        A dict with status and scan output.
    """
    try:
        result = run_ps("sfc /scannow | Out-String", timeout=600)
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def run_dism_health_check() -> dict[str, str]:
    """Run DISM to check the Windows component store health.

    Returns:
        A dict with status and DISM output.
    """
    try:
        result = run_ps(
            "DISM /Online /Cleanup-Image /CheckHealth | Out-String",
            timeout=300,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def check_disk_errors(drive: str = "C:") -> dict[str, str]:
    """Run a chkdsk scan (read-only, no repair) on a volume.

    Args:
        drive: Drive letter with colon (e.g. 'C:').

    Returns:
        A dict with status and chkdsk output.
    """
    try:
        result = run_ps(f"chkdsk {drive} /scan | Out-String", timeout=300)
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def disable_startup_item(item_name: str) -> dict[str, str]:
    """Disable a startup program by name (removes from registry run key).

    Args:
        item_name: The name of the startup entry to disable.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            f"Remove-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' "
            f"-Name '{item_name}' -ErrorAction SilentlyContinue; "
            f"Remove-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' "
            f"-Name '{item_name}' -ErrorAction SilentlyContinue"
        )
        return {"status": "ok", "message": f"Startup item '{item_name}' disabled."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def run_dism_restore_health() -> dict[str, str]:
    """Run DISM to repair the Windows component store (downloads from Windows Update).

    This operation can take 15-30 minutes and requires internet access.

    Returns:
        A dict with status and DISM output.
    """
    try:
        result = run_ps(
            "DISM /Online /Cleanup-Image /RestoreHealth | Out-String",
            timeout=3600,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
