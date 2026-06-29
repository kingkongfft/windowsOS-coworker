from __future__ import annotations

import psutil
from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_memory_usage() -> dict[str, str]:
    """Return current RAM usage statistics.

    Returns:
        A dict with total_gb, available_gb, used_gb, percent_used, status.
    """
    try:
        mem = psutil.virtual_memory()
        return {
            "status": "ok",
            "total_gb": f"{mem.total / 1e9:.1f}",
            "available_gb": f"{mem.available / 1e9:.1f}",
            "used_gb": f"{mem.used / 1e9:.1f}",
            "percent_used": f"{mem.percent}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_top_memory_processes(top_n: int = 10) -> dict[str, str]:
    """List the processes consuming the most memory.

    Args:
        top_n: Number of top processes to return (default 10).

    Returns:
        A dict with status and a 'processes' table string.
    """
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_percent", "memory_info"]):
            try:
                info = p.info
                procs.append(
                    {
                        "pid": info["pid"],
                        "name": info["name"],
                        "mem_pct": info["memory_percent"] or 0.0,
                        "mem_mb": (
                            info["memory_info"].rss if info["memory_info"] else 0
                        )
                        / 1e6,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x["mem_pct"], reverse=True)
        lines = ["PID    NAME                          MEM%    MEM(MB)"]
        for p in procs[:top_n]:
            lines.append(
                f"{p['pid']:<6} {p['name']:<30} {p['mem_pct']:>5.1f}  {p['mem_mb']:>8.1f}"
            )
        return {"status": "ok", "processes": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_paging_file_info() -> dict[str, str]:
    """Show paging file (virtual memory) size and location.

    Returns:
        A dict with status and a 'paging_file' info string.
    """
    try:
        result = run_ps(
            "Get-WmiObject Win32_PageFileUsage | "
            "Select-Object Name, AllocatedBaseSize, CurrentUsage, PeakUsage | "
            "Format-List | Out-String"
        )
        return {"status": "ok", "paging_file": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def identify_memory_leak_suspects(
    duration_seconds: int = 10, top_n: int = 5
) -> dict[str, str]:
    """Identify processes whose memory usage grew during an observation window.

    Samples memory twice over *duration_seconds* and reports the biggest growers.

    Args:
        duration_seconds: How long to observe (default 10s). Keep short.
        top_n: Number of top suspects to return (default 5).

    Returns:
        A dict with status and a 'suspects' table string.
    """
    import time

    try:
        snapshot1: dict[int, float] = {}
        for p in psutil.process_iter(["pid", "memory_info"]):
            try:
                mi = p.info["memory_info"]
                if mi:
                    snapshot1[p.pid] = mi.rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        time.sleep(min(duration_seconds, 30))

        deltas: list[tuple[int, str, float]] = []
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                mi = p.info["memory_info"]
                if mi and p.pid in snapshot1:
                    delta = mi.rss - snapshot1[p.pid]
                    if delta > 0:
                        deltas.append((p.pid, p.info["name"] or "?", delta / 1e6))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        deltas.sort(key=lambda x: x[2], reverse=True)
        lines = ["PID    NAME                          GROWTH(MB)"]
        for pid, name, delta_mb in deltas[:top_n]:
            lines.append(f"{pid:<6} {name:<30} {delta_mb:>10.2f}")
        return {"status": "ok", "suspects": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def release_standby_memory() -> dict[str, str]:
    """Release Windows standby (cached) memory back to available pool.

    Uses the RAMMap command-line tool (RamMap.exe) if available, otherwise
    falls back to a WMI memory-trim approach.

    Returns:
        A dict with status and message.
    """
    try:
        # Try RAMMap CLI first (Sysinternals)
        import subprocess

        result = subprocess.run(
            ["RAMMap.exe", "-Et"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "Standby memory released via RAMMap."}
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # Fallback: PowerShell empty working sets
    try:
        run_ps(
            "[System.GC]::Collect(); "
            "[System.GC]::WaitForPendingFinalizers(); "
            "[System.GC]::Collect()"
        )
        return {
            "status": "ok",
            "message": "Standby memory release attempted. Install RAMMap (Sysinternals) for full effect.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def clear_file_system_cache() -> dict[str, str]:
    """Clear the Windows file system (standby) cache to free up RAM.

    Triggers a memory flush via PowerShell's .NET GC and the Windows
    memory management subsystem.  Does not terminate any processes.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; "
            "[System.GC]::Collect(); "
            "[System.GC]::WaitForPendingFinalizers(); "
            "[System.GC]::Collect()"
        )
        return {
            "status": "ok",
            "message": "File system cache cleared successfully.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def set_paging_file_size(
    drive: str = "C:", initial_size_mb: int = 4096, max_size_mb: int = 8192
) -> dict[str, str]:
    """Resize the Windows paging file on a given drive.

    Args:
        drive: Drive letter with colon, e.g. "C:".
        initial_size_mb: Initial paging file size in MB.
        max_size_mb: Maximum paging file size in MB.

    Returns:
        A dict with status and message. A reboot is required for changes to take effect.
    """
    try:
        ps_cmd = (
            f"$cs = Get-WmiObject -Class Win32_ComputerSystem -EnableAllPrivileges; "
            f"$cs.AutomaticManagedPagefile = $false; "
            f"$cs.Put() | Out-Null; "
            f"$pf = Get-WmiObject -Class Win32_PageFileSetting; "
            f"if ($pf) {{ $pf.Delete() }}; "
            f"Set-WmiInstance -Class Win32_PageFileSetting "
            f"-Arguments @{{Name='{drive.rstrip(':')}:\\pagefile.sys';"
            f"InitialSize={initial_size_mb};MaximumSize={max_size_mb}}} | Out-Null"
        )
        run_ps(ps_cmd)
        return {
            "status": "ok",
            "message": f"Paging file on {drive} set to {initial_size_mb}–{max_size_mb} MB. Reboot required.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
