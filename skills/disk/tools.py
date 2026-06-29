from __future__ import annotations

import shutil
from pathlib import Path

import psutil
from agents import function_tool

from core.exceptions import SkillExecutionError
from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_disk_usage(drive: str = "C:") -> dict[str, str]:
    """Return disk space usage for a given drive letter.

    Args:
        drive: Drive letter with colon, e.g. "C:" or "D:".

    Returns:
        A dict with keys total_gb, used_gb, free_gb, percent_used, status.
    """
    try:
        usage = psutil.disk_usage(drive + "\\")
        return {
            "status": "ok",
            "drive": drive,
            "total_gb": f"{usage.total / 1e9:.1f}",
            "used_gb": f"{usage.used / 1e9:.1f}",
            "free_gb": f"{usage.free / 1e9:.1f}",
            "percent_used": f"{usage.percent}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_partitions() -> dict[str, str]:
    """List all disk partitions and their mount points.

    Returns:
        A dict with status and a newline-delimited 'partitions' string.
    """
    try:
        parts = psutil.disk_partitions()
        lines = [
            f"{p.device}  mountpoint={p.mountpoint}  fstype={p.fstype}  opts={p.opts}"
            for p in parts
        ]
        return {"status": "ok", "partitions": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def analyze_disk_usage(path: str = "C:\\", top_n: int = 10) -> dict[str, str]:
    """Show the top N folders by size under a given path.

    Args:
        path: Root path to analyse (default C:\\).
        top_n: Number of largest directories to return (default 10).

    Returns:
        A dict with status and a 'results' string listing folder sizes.
    """
    try:
        ps_cmd = (
            f"Get-ChildItem -Path '{path}' -Directory -ErrorAction SilentlyContinue | "
            f"ForEach-Object {{ $size = (Get-ChildItem $_.FullName -Recurse -File "
            f"-ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; "
            f"[PSCustomObject]@{{Path=$_.FullName; SizeGB=[math]::Round($size/1GB,2)}} }} | "
            f"Sort-Object SizeGB -Descending | Select-Object -First {top_n} | "
            f"Format-Table -AutoSize | Out-String"
        )
        result = run_ps(ps_cmd)
        return {"status": "ok", "results": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_large_files(
    path: str = "C:\\", min_size_mb: int = 500, top_n: int = 20
) -> dict[str, str]:
    """Find files larger than a given size threshold.

    Args:
        path: Root path to search (default C:\\).
        min_size_mb: Minimum file size in MB (default 500).
        top_n: Maximum number of results to return (default 20).

    Returns:
        A dict with status and a 'files' string listing matching files.
    """
    try:
        min_bytes = min_size_mb * 1024 * 1024
        ps_cmd = (
            f"Get-ChildItem -Path '{path}' -Recurse -File -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.Length -gt {min_bytes} }} | "
            f"Sort-Object Length -Descending | Select-Object -First {top_n} | "
            f"Select-Object FullName, @{{N='SizeMB';E={{[math]::Round($_.Length/1MB,1)}}}} | "
            f"Format-Table -AutoSize | Out-String"
        )
        result = run_ps(ps_cmd)
        return {"status": "ok", "files": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_drive_health() -> dict[str, str]:
    """Check physical drive health via SMART data.

    Returns:
        A dict with status and a 'health' string per physical disk.
    """
    try:
        ps_cmd = (
            "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, "
            "HealthStatus, OperationalStatus, Size | Format-Table -AutoSize | Out-String"
        )
        result = run_ps(ps_cmd)
        return {"status": "ok", "health": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def clean_temp_files() -> dict[str, str]:
    """Delete user and system temporary files to free disk space.

    Clears %TEMP%, %TMP%, and C:\\Windows\\Temp.

    Returns:
        A dict with status and a summary of how much space was freed.
    """
    freed = 0
    errors: list[str] = []
    temp_dirs = [
        Path(p)
        for p in [
            Path.home() / "AppData" / "Local" / "Temp",
            Path("C:\\Windows\\Temp"),
        ]
    ]
    for temp_dir in temp_dirs:
        if not temp_dir.exists():
            continue
        for item in temp_dir.iterdir():
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    freed += size
                elif item.is_dir():
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    shutil.rmtree(item, ignore_errors=True)
                    freed += size
            except Exception as exc:
                errors.append(str(exc))

    freed_mb = freed / 1e6
    msg = f"Freed {freed_mb:.1f} MB from temp folders."
    if errors:
        msg += f" ({len(errors)} items skipped — in use or access denied)"
    return {"status": "ok", "message": msg}


@risk(Risk.MEDIUM)
@function_tool
def clean_recycle_bin() -> dict[str, str]:
    """Empty the Windows Recycle Bin for all drives.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
        return {"status": "ok", "message": "Recycle Bin emptied."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def clean_windows_update_cache() -> dict[str, str]:
    """Remove the Windows Update download cache (SoftwareDistribution\\Download).

    Stops the Windows Update service, deletes the cache, then restarts the service.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps("Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue")
        cache_path = Path("C:\\Windows\\SoftwareDistribution\\Download")
        freed = 0
        if cache_path.exists():
            for item in cache_path.iterdir():
                try:
                    if item.is_file():
                        freed += item.stat().st_size
                        item.unlink()
                    elif item.is_dir():
                        freed += sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass
        run_ps("Start-Service -Name wuauserv -ErrorAction SilentlyContinue")
        freed_mb = freed / 1e6
        return {
            "status": "ok",
            "message": f"Windows Update cache cleared. Freed {freed_mb:.1f} MB.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def defrag_drive(drive: str = "C:") -> dict[str, str]:
    """Analyse and optimise (defragment) a drive.

    Args:
        drive: Drive letter with colon, e.g. "C:".

    Returns:
        A dict with status and the defrag output.
    """
    try:
        result = run_ps(
            f"Optimize-Volume -DriveLetter {drive.rstrip(':')} -Verbose 4>&1 | Out-String"
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
