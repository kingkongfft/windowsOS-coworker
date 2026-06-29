from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import psutil

from skills.disk.tools import get_disk_usage, list_partitions


@patch("skills.disk.tools.psutil.disk_usage")
def test_get_disk_usage_success(mock_usage: MagicMock) -> None:
    mock_usage.return_value = MagicMock(
        total=500_000_000_000,
        used=200_000_000_000,
        free=300_000_000_000,
        percent=40.0,
    )
    result = get_disk_usage("C:")
    assert result["status"] == "ok"
    assert result["drive"] == "C:"
    assert "500.0" in result["total_gb"]
    assert "300.0" in result["free_gb"]
    assert result["percent_used"] == "40.0"


@patch("skills.disk.tools.psutil.disk_usage")
def test_get_disk_usage_error(mock_usage: MagicMock) -> None:
    mock_usage.side_effect = FileNotFoundError("Drive not found")
    result = get_disk_usage("Z:")
    assert result["status"] == "error"
    assert "Drive not found" in result["message"]


@patch("skills.disk.tools.psutil.disk_partitions")
def test_list_partitions_success(mock_parts: MagicMock) -> None:
    mock_parts.return_value = [
        MagicMock(device="C:\\", mountpoint="C:\\", fstype="NTFS", opts="rw"),
        MagicMock(device="D:\\", mountpoint="D:\\", fstype="NTFS", opts="rw"),
    ]
    result = list_partitions()
    assert result["status"] == "ok"
    assert "C:\\" in result["partitions"]
    assert "NTFS" in result["partitions"]


@patch("skills.disk.tools.psutil.disk_partitions")
def test_list_partitions_error(mock_parts: MagicMock) -> None:
    mock_parts.side_effect = RuntimeError("WMI error")
    result = list_partitions()
    assert result["status"] == "error"
