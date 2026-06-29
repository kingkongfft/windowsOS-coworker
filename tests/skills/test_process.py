from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skills.process.tools import (
    find_process_by_name,
    kill_process,
    list_processes,
)


@patch("skills.process.tools.psutil.process_iter")
@patch("skills.process.tools.psutil.cpu_percent", return_value=None)
def test_list_processes_returns_table(
    mock_cpu: MagicMock, mock_iter: MagicMock
) -> None:
    import time

    with patch("skills.process.tools.time.sleep"):

        def make_proc(pid: int, name: str, cpu: float, rss: int) -> MagicMock:
            p = MagicMock()
            p.pid = pid
            p.name.return_value = name
            p.cpu_percent.return_value = cpu
            p.info = {
                "pid": pid,
                "name": name,
                "status": "running",
                "memory_info": MagicMock(rss=rss),
            }
            return p

        mock_iter.return_value = [
            make_proc(1, "System", 0.1, 1_000_000),
            make_proc(100, "chrome.exe", 5.0, 200_000_000),
        ]
        result = list_processes()

    assert result["status"] == "ok"
    assert "chrome.exe" in result["processes"]


@patch("skills.process.tools.psutil.process_iter")
def test_find_process_by_name_match(mock_iter: MagicMock) -> None:
    p = MagicMock()
    p.pid = 42
    p.info = {"pid": 42, "name": "notepad.exe", "status": "running"}
    mock_iter.return_value = [p]

    result = find_process_by_name("notepad")
    assert result["status"] == "ok"
    assert "notepad.exe" in result["matches"]


@patch("skills.process.tools.psutil.process_iter")
def test_find_process_by_name_no_match(mock_iter: MagicMock) -> None:
    mock_iter.return_value = []
    result = find_process_by_name("doesnotexist")
    assert result["status"] == "ok"
    assert "No processes" in result["matches"]


@patch("skills.process.tools.psutil.Process")
def test_kill_process_by_pid(mock_process_cls: MagicMock) -> None:
    mock_proc = MagicMock()
    mock_proc.name.return_value = "notepad.exe"
    mock_process_cls.return_value = mock_proc

    result = kill_process("1234")
    assert result["status"] == "ok"
    mock_proc.kill.assert_called_once()
