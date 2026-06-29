"""Unit tests for skills/memory/tools.py — all psutil calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from skills.memory.tools import get_memory_usage, list_top_memory_processes

from tests.skills.conftest import raw

_get_memory_usage = raw(get_memory_usage)
_list_top_memory_processes = raw(list_top_memory_processes)


@patch("skills.memory.tools.psutil.virtual_memory")
def test_get_memory_usage_success(mock_mem: MagicMock) -> None:
    mock_mem.return_value = MagicMock(
        total=16_000_000_000,
        available=8_000_000_000,
        used=8_000_000_000,
        percent=50.0,
    )
    result = _get_memory_usage()
    assert result["status"] == "ok"
    assert "16.0" in result["total_gb"]
    assert "8.0" in result["available_gb"]
    assert result["percent_used"] == "50.0"


@patch("skills.memory.tools.psutil.virtual_memory")
def test_get_memory_usage_error(mock_mem: MagicMock) -> None:
    mock_mem.side_effect = Exception("OS error")
    result = _get_memory_usage()
    assert result["status"] == "error"
    assert "OS error" in result["message"]


@patch("skills.memory.tools.psutil.process_iter")
def test_list_top_memory_processes_returns_table(mock_iter: MagicMock) -> None:
    def make_proc(pid: int, name: str, mem_pct: float, rss: int) -> MagicMock:
        p = MagicMock()
        p.pid = pid
        p.info = {
            "pid": pid,
            "name": name,
            "memory_percent": mem_pct,
            "memory_info": MagicMock(rss=rss),
        }
        return p

    mock_iter.return_value = [
        make_proc(100, "chrome.exe", 15.0, 500_000_000),
        make_proc(200, "python.exe", 5.0, 100_000_000),
    ]
    result = _list_top_memory_processes(top_n=5)
    assert result["status"] == "ok"
    assert "chrome.exe" in result["processes"]
    assert "100" in result["processes"]  # PID
