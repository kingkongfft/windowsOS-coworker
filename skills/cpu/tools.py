from __future__ import annotations

import psutil
from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_cpu_usage() -> dict[str, str]:
    """Return overall and per-core CPU usage percentages.

    Returns:
        A dict with status, overall_percent, and per_core breakdown.
    """
    try:
        overall = psutil.cpu_percent(interval=1)
        per_core = psutil.cpu_percent(interval=1, percpu=True)
        core_str = ", ".join(f"Core{i}:{v}%" for i, v in enumerate(per_core))
        return {
            "status": "ok",
            "overall_percent": str(overall),
            "per_core": core_str,
            "cpu_count": str(psutil.cpu_count(logical=True)),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_top_cpu_processes(top_n: int = 10) -> dict[str, str]:
    """List processes consuming the most CPU.

    Args:
        top_n: Number of top processes to return (default 10).

    Returns:
        A dict with status and a 'processes' table string.
    """
    try:
        # Prime the cpu_percent counters
        for p in psutil.process_iter(["pid", "name"]):
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        import time

        time.sleep(1)

        procs = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                cpu = p.cpu_percent(interval=None)
                procs.append({"pid": p.pid, "name": p.name(), "cpu_pct": cpu})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x["cpu_pct"], reverse=True)
        lines = ["PID    NAME                          CPU%"]
        for p in procs[:top_n]:
            lines.append(f"{p['pid']:<6} {p['name']:<30} {p['cpu_pct']:>5.1f}")
        return {"status": "ok", "processes": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_power_plan() -> dict[str, str]:
    """Show the currently active Windows power plan.

    Returns:
        A dict with status and 'power_plan' description.
    """
    try:
        result = run_ps("powercfg /getactivescheme")
        return {"status": "ok", "power_plan": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_cpu_temperature() -> dict[str, str]:
    """Read CPU temperature sensors if available via WMI.

    Returns:
        A dict with status and 'temperature' string (or a note if unavailable).
    """
    try:
        result = run_ps(
            "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
            "-ErrorAction SilentlyContinue | "
            "Select-Object @{N='TempC';E={[math]::Round(($_.CurrentTemperature - 2732)/10,1)}} | "
            "Format-Table -AutoSize | Out-String"
        )
        output = result.stdout.strip()
        if not output:
            output = (
                "Temperature data not available on this hardware/driver configuration."
            )
        return {"status": "ok", "temperature": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def set_process_priority(pid: int, priority: str = "normal") -> dict[str, str]:
    """Change the scheduling priority of a running process.

    Args:
        pid: The process ID to adjust.
        priority: One of: idle, below_normal, normal, above_normal, high, realtime.

    Returns:
        A dict with status and message.
    """
    priority_map = {
        "idle": psutil.IDLE_PRIORITY_CLASS,
        "below_normal": psutil.BELOW_NORMAL_PRIORITY_CLASS,
        "normal": psutil.NORMAL_PRIORITY_CLASS,
        "above_normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
        "high": psutil.HIGH_PRIORITY_CLASS,
        "realtime": psutil.REALTIME_PRIORITY_CLASS,
    }
    if priority not in priority_map:
        return {
            "status": "error",
            "message": f"Invalid priority '{priority}'. Choose from: {', '.join(priority_map)}",
        }
    try:
        p = psutil.Process(pid)
        p.nice(priority_map[priority])
        return {
            "status": "ok",
            "message": f"Process {pid} ({p.name()}) priority set to '{priority}'.",
        }
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"No process with PID {pid}."}
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
            "message": f"Unknown plan '{plan}'. Choose from: {', '.join(plan_guids)}",
        }
    try:
        run_ps(f"powercfg /setactive {plan_guids[plan]}")
        return {"status": "ok", "message": f"Power plan set to '{plan}'."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def set_process_affinity(pid: int, cores: list[int]) -> dict[str, str]:
    """Pin a process to a specific set of CPU cores.

    Args:
        pid: The process ID to adjust.
        cores: List of zero-based core indices, e.g. [0, 1].

    Returns:
        A dict with status and message.
    """
    try:
        p = psutil.Process(pid)
        p.cpu_affinity(cores)
        return {
            "status": "ok",
            "message": f"Process {pid} ({p.name()}) pinned to cores {cores}.",
        }
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"No process with PID {pid}."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def kill_high_cpu_process(threshold_percent: float = 90.0) -> dict[str, str]:
    """Terminate the process with the highest CPU usage if it exceeds a threshold.

    Args:
        threshold_percent: CPU% threshold above which the process is killed (default 90.0).

    Returns:
        A dict with status and message describing what was killed.
    """
    try:
        import time

        for p in psutil.process_iter(["pid", "name"]):
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(1)

        worst: tuple[float, int, str] = (0.0, -1, "")
        for p in psutil.process_iter(["pid", "name"]):
            try:
                cpu = p.cpu_percent(interval=None)
                if cpu > worst[0]:
                    worst = (cpu, p.pid, p.name())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        cpu_val, pid, name = worst
        if pid == -1 or cpu_val < threshold_percent:
            return {
                "status": "ok",
                "message": f"No process exceeded {threshold_percent}% CPU. Highest was {cpu_val:.1f}%.",
            }
        proc = psutil.Process(pid)
        proc.kill()
        return {
            "status": "ok",
            "message": f"Killed process '{name}' (PID {pid}) using {cpu_val:.1f}% CPU.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
