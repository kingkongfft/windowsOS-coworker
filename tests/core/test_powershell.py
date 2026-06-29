from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from core.exceptions import ElevationRequiredError, PowerShellError
from core.powershell import PSResult, run_ps


def _make_completed_process(
    stdout: str = "", stderr: str = "", returncode: int = 0
) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = stderr
    mock.returncode = returncode
    return mock


@patch("core.powershell.subprocess.run")
def test_run_ps_success(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_completed_process(stdout="hello", returncode=0)
    result = run_ps("Write-Output 'hello'")
    assert result.stdout == "hello"
    assert result.returncode == 0


@patch("core.powershell.subprocess.run")
def test_run_ps_passes_noninteractive_flags(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_completed_process()
    run_ps("Get-Date")
    args = mock_run.call_args[0][0]
    assert "-NonInteractive" in args
    assert "-NoProfile" in args
    assert "-ExecutionPolicy" in args
    assert "Bypass" in args


@patch("core.powershell.subprocess.run")
def test_run_ps_raises_powershell_error_on_nonzero(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_completed_process(stderr="some error", returncode=1)
    with pytest.raises(PowerShellError) as exc_info:
        run_ps("bad-command")
    assert exc_info.value.returncode == 1
    assert "some error" in str(exc_info.value)


@patch("core.powershell.subprocess.run")
def test_run_ps_raises_elevation_error_on_access_denied(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_completed_process(
        stderr="Access is denied", returncode=1
    )
    with pytest.raises(ElevationRequiredError):
        run_ps("some-admin-command")


@patch("core.powershell.subprocess.run")
def test_run_ps_strips_output(mock_run: MagicMock) -> None:
    mock_run.return_value = _make_completed_process(stdout="  padded  \n", returncode=0)
    result = run_ps("echo padded")
    assert result.stdout == "padded"
