from __future__ import annotations

import psutil
from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_services(status_filter: str = "all") -> dict[str, str]:
    """List Windows services and their current status.

    Args:
        status_filter: Filter by status: 'all', 'running', 'stopped'. Default 'all'.

    Returns:
        A dict with status and a 'services' table string.
    """
    try:
        services = []
        for svc in psutil.win_service_iter():
            try:
                info = svc.as_dict()
                s = info.get("status", "")
                if status_filter == "running" and s != "running":
                    continue
                if status_filter == "stopped" and s != "stopped":
                    continue
                services.append(info)
            except Exception:
                pass
        services.sort(key=lambda x: x.get("name", ""))
        lines = ["NAME                               STATUS   START_TYPE  DISPLAY_NAME"]
        for s in services:
            lines.append(
                f"{s.get('name', ''):<34} {s.get('status', ''):<8} {s.get('start_type', ''):<11} {s.get('display_name', '')}"
            )
        return {"status": "ok", "services": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_service_status(service_name: str) -> dict[str, str]:
    """Get the status and configuration of a specific Windows service.

    Args:
        service_name: The short service name (e.g. "wuauserv").

    Returns:
        A dict with status, display_name, current_status, start_type, pid.
    """
    try:
        svc = psutil.win_service_get(service_name)
        info = svc.as_dict()
        return {
            "status": "ok",
            "name": info.get("name", ""),
            "display_name": info.get("display_name", ""),
            "current_status": info.get("status", ""),
            "start_type": info.get("start_type", ""),
            "pid": str(info.get("pid", "")),
            "username": info.get("username", ""),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_service_dependencies(service_name: str) -> dict[str, str]:
    """Show what services a given service depends on.

    Args:
        service_name: The short service name.

    Returns:
        A dict with status and 'dependencies' string.
    """
    try:
        result = run_ps(f"sc.exe qc '{service_name}' | Out-String")
        return {"status": "ok", "dependencies": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_failed_services() -> dict[str, str]:
    """List services that are stopped but have auto-start configured.

    Returns:
        A dict with status and a 'failed_services' list string.
    """
    try:
        result = run_ps(
            "Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Stopped' } | "
            "Select-Object Name, DisplayName, Status, StartType | Format-Table -AutoSize | Out-String"
        )
        output = (
            result.stdout.strip() or "No auto-start services are currently stopped."
        )
        return {"status": "ok", "failed_services": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def start_service(service_name: str) -> dict[str, str]:
    """Start a stopped Windows service.

    Args:
        service_name: The short service name (e.g. "spooler").

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Start-Service -Name '{service_name}' -ErrorAction Stop")
        return {"status": "ok", "message": f"Service '{service_name}' started."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def restart_service(service_name: str) -> dict[str, str]:
    """Restart a Windows service (stop then start).

    Args:
        service_name: The short service name.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Restart-Service -Name '{service_name}' -Force -ErrorAction Stop")
        return {"status": "ok", "message": f"Service '{service_name}' restarted."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def stop_service(service_name: str) -> dict[str, str]:
    """Stop a running Windows service.

    Args:
        service_name: The short service name.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Stop-Service -Name '{service_name}' -Force -ErrorAction Stop")
        return {"status": "ok", "message": f"Service '{service_name}' stopped."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def set_service_startup_type(
    service_name: str, startup_type: str = "Manual"
) -> dict[str, str]:
    """Change the startup type of a Windows service.

    Args:
        service_name: The short service name.
        startup_type: One of: Automatic, Manual, Disabled, AutomaticDelayed.

    Returns:
        A dict with status and message.
    """
    valid = {"Automatic", "Manual", "Disabled", "AutomaticDelayed"}
    if startup_type not in valid:
        return {
            "status": "error",
            "message": f"Invalid startup_type '{startup_type}'. Choose from: {valid}",
        }
    try:
        start_val = (
            "delayed-auto"
            if startup_type == "AutomaticDelayed"
            else startup_type.lower()
        )
        run_ps(
            f"Set-Service -Name '{service_name}' -StartupType {startup_type} -ErrorAction Stop"
        )
        return {
            "status": "ok",
            "message": f"Service '{service_name}' startup type set to '{startup_type}'.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
