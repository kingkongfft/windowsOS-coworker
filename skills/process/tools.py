from __future__ import annotations

import psutil
from agents import function_tool

from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_processes(top_n: int = 30) -> dict[str, str]:
    """List running processes sorted by CPU usage.

    Args:
        top_n: Maximum number of processes to return (default 30).

    Returns:
        A dict with status and a 'processes' table string.
    """
    try:
        import time

        for p in psutil.process_iter(["pid", "name"]):
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.5)

        procs = []
        for p in psutil.process_iter(["pid", "name", "status", "memory_info"]):
            try:
                cpu = p.cpu_percent(interval=None)
                mem = (p.info["memory_info"].rss if p.info["memory_info"] else 0) / 1e6
                procs.append(
                    {
                        "pid": p.pid,
                        "name": p.info["name"],
                        "cpu": cpu,
                        "mem_mb": mem,
                        "status": p.info["status"],
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x["cpu"], reverse=True)
        lines = ["PID    NAME                          CPU%   MEM(MB) STATUS"]
        for p in procs[:top_n]:
            lines.append(
                f"{p['pid']:<6} {(p['name'] or '?'):<30} {p['cpu']:>5.1f}  {p['mem_mb']:>7.1f} {p['status']}"
            )
        return {"status": "ok", "processes": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_process_details(identifier: str) -> dict[str, str]:
    """Get detailed information about a specific process by name or PID.

    Args:
        identifier: Process name (e.g. "chrome.exe") or numeric PID string.

    Returns:
        A dict with status and process details.
    """
    try:
        proc = _resolve_process(identifier)
        with proc.oneshot():
            info = {
                "pid": str(proc.pid),
                "name": proc.name(),
                "status": proc.status(),
                "exe": proc.exe() if proc.exe() else "N/A",
                "cpu_percent": f"{proc.cpu_percent(interval=0.5)}",
                "memory_mb": f"{proc.memory_info().rss / 1e6:.1f}",
                "threads": str(proc.num_threads()),
                "created": str(proc.create_time()),
            }
        return {"status": "ok", **info}
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def find_process_by_name(name_pattern: str) -> dict[str, str]:
    """Search for running processes whose name matches a pattern.

    Args:
        name_pattern: Case-insensitive substring to match against process names.

    Returns:
        A dict with status and a 'matches' table string.
    """
    try:
        pattern = name_pattern.lower()
        matches = []
        for p in psutil.process_iter(["pid", "name", "status"]):
            try:
                if pattern in (p.info["name"] or "").lower():
                    matches.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if not matches:
            return {
                "status": "ok",
                "matches": f"No processes matching '{name_pattern}'.",
            }
        lines = ["PID    NAME                          STATUS"]
        for m in matches:
            lines.append(f"{m['pid']:<6} {(m['name'] or '?'):<30} {m['status']}")
        return {"status": "ok", "matches": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_process_open_files(identifier: str) -> dict[str, str]:
    """List files currently opened by a specific process.

    Args:
        identifier: Process name or numeric PID string.

    Returns:
        A dict with status and an 'open_files' list string.
    """
    try:
        proc = _resolve_process(identifier)
        files = proc.open_files()
        if not files:
            return {
                "status": "ok",
                "open_files": "No open files (or insufficient permissions).",
            }
        return {"status": "ok", "open_files": "\n".join(f.path for f in files)}
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_process_network_connections(identifier: str) -> dict[str, str]:
    """Show active network connections for a specific process.

    Args:
        identifier: Process name or numeric PID string.

    Returns:
        A dict with status and a 'connections' table string.
    """
    try:
        proc = _resolve_process(identifier)
        conns = proc.connections()
        if not conns:
            return {"status": "ok", "connections": "No network connections found."}
        lines = ["PROTO  LOCAL_ADDR            REMOTE_ADDR          STATUS"]
        for c in conns:
            local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
            remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
            lines.append(f"{c.type.name:<6} {local:<20} {remote:<20} {c.status}")
        return {"status": "ok", "connections": "\n".join(lines)}
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def suspend_process(identifier: str) -> dict[str, str]:
    """Suspend (pause) a running process.

    Args:
        identifier: Process name or numeric PID string.

    Returns:
        A dict with status and message.
    """
    try:
        proc = _resolve_process(identifier)
        proc.suspend()
        return {
            "status": "ok",
            "message": f"Process '{proc.name()}' (PID {proc.pid}) suspended.",
        }
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def resume_process(identifier: str) -> dict[str, str]:
    """Resume a previously suspended process.

    Args:
        identifier: Process name or numeric PID string.

    Returns:
        A dict with status and message.
    """
    try:
        proc = _resolve_process(identifier)
        proc.resume()
        return {
            "status": "ok",
            "message": f"Process '{proc.name()}' (PID {proc.pid}) resumed.",
        }
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def kill_process(identifier: str) -> dict[str, str]:
    """Terminate a process by name or PID.

    If multiple processes share the same name, all matching processes are killed.

    Args:
        identifier: Process name (e.g. "notepad.exe") or numeric PID string.

    Returns:
        A dict with status and message listing what was killed.
    """
    try:
        if identifier.isdigit():
            proc = psutil.Process(int(identifier))
            name = proc.name()
            proc.kill()
            return {
                "status": "ok",
                "message": f"Killed process '{name}' (PID {identifier}).",
            }

        killed = []
        pattern = identifier.lower()
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if (p.info["name"] or "").lower() == pattern:
                    p.kill()
                    killed.append(f"{p.info['name']} (PID {p.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if not killed:
            return {
                "status": "error",
                "message": f"No processes named '{identifier}' found.",
            }
        return {"status": "ok", "message": f"Killed: {', '.join(killed)}"}
    except psutil.NoSuchProcess:
        return {"status": "error", "message": f"Process '{identifier}' not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_process(identifier: str) -> psutil.Process:
    """Resolve a process name or PID string to a :class:`psutil.Process`.

    Args:
        identifier: Numeric PID string or process name substring.

    Returns:
        The matching :class:`psutil.Process`.

    Raises:
        psutil.NoSuchProcess: If no matching process is found.
    """
    if identifier.isdigit():
        return psutil.Process(int(identifier))
    pattern = identifier.lower()
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if (p.info["name"] or "").lower() == pattern:
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    raise psutil.NoSuchProcess(pid=-1, name=identifier)
