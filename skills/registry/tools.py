from __future__ import annotations

import winreg
from typing import Any

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk

# Map short hive names to winreg constants
_HIVE_MAP: dict[str, int] = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKU": winreg.HKEY_USERS,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,
}


def _split_path(registry_path: str) -> tuple[int, str]:
    """Split a registry path like 'HKLM\\SOFTWARE\\...' into (hive, subkey).

    Args:
        registry_path: Full registry path starting with hive abbreviation.

    Returns:
        Tuple of (hive constant, subkey string).

    Raises:
        ValueError: If the hive is not recognised.
    """
    parts = registry_path.split("\\", 1)
    hive_name = parts[0].upper()
    subkey = parts[1] if len(parts) > 1 else ""
    if hive_name not in _HIVE_MAP:
        raise ValueError(f"Unknown hive '{hive_name}'. Use: {list(_HIVE_MAP)}")
    return _HIVE_MAP[hive_name], subkey


@risk(Risk.LOW)
@function_tool
def read_registry_key(registry_path: str, value_name: str = "") -> dict[str, str]:
    """Read a registry value from a given key path.

    Args:
        registry_path: Full path e.g. 'HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'.
        value_name: Name of the value to read. Empty string reads the default value.

    Returns:
        A dict with status, path, value_name, and data.
    """
    try:
        hive, subkey = _split_path(registry_path)
        with winreg.OpenKey(hive, subkey, access=winreg.KEY_READ) as key:
            data, reg_type = winreg.QueryValueEx(key, value_name)
        return {
            "status": "ok",
            "path": registry_path,
            "value_name": value_name or "(default)",
            "data": str(data),
            "type": str(reg_type),
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Registry key or value not found: {registry_path}\\{value_name}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_registry_subkeys(registry_path: str) -> dict[str, str]:
    """List all subkeys under a registry path.

    Args:
        registry_path: Full registry path (e.g. 'HKLM\\SOFTWARE').

    Returns:
        A dict with status and 'subkeys' newline-delimited string.
    """
    try:
        hive, subkey = _split_path(registry_path)
        keys = []
        with winreg.OpenKey(hive, subkey, access=winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    keys.append(winreg.EnumKey(key, i))
                    i += 1
                except OSError:
                    break
        return {"status": "ok", "subkeys": "\n".join(keys) or "(no subkeys)"}
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Registry path not found: {registry_path}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def backup_registry_key(
    registry_path: str, output_file: str = "C:\\Temp\\registry_backup.reg"
) -> dict[str, str]:
    """Export a registry key to a .reg file for backup.

    Args:
        registry_path: Full registry path to export (e.g. 'HKLM\\SOFTWARE\\MyApp').
        output_file: Destination .reg file path.

    Returns:
        A dict with status, message, and the backup file path.
    """
    try:
        run_ps(f"reg export '{registry_path}' '{output_file}' /y")
        return {
            "status": "ok",
            "message": f"Registry key exported to {output_file}.",
            "path": output_file,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def search_registry(
    registry_path: str, search_term: str, max_results: int = 20
) -> dict[str, str]:
    """Search for a key or value name pattern under a registry path.

    Args:
        registry_path: Root path to search under (e.g. 'HKLM\\SOFTWARE').
        search_term: Case-insensitive substring to match against key/value names.
        max_results: Maximum number of matches to return (default 20).

    Returns:
        A dict with status and 'matches' string.
    """
    try:
        result = run_ps(
            f"Get-ChildItem -Path 'Registry::{registry_path}' -Recurse -ErrorAction SilentlyContinue | "
            f"Where-Object {{ $_.Name -like '*{search_term}*' -or ($_.GetValueNames() | Where-Object {{ $_ -like '*{search_term}*' }}) }} | "
            f"Select-Object -First {max_results} | Format-Table -AutoSize | Out-String"
        )
        return {
            "status": "ok",
            "matches": result.stdout or f"No matches for '{search_term}'.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def write_registry_value(
    registry_path: str, value_name: str, data: str, reg_type: str = "REG_SZ"
) -> dict[str, str]:
    """Write a value to a registry key.

    Args:
        registry_path: Full registry path.
        value_name: Name of the value to write.
        data: String representation of the data to write.
        reg_type: Registry type: REG_SZ, REG_DWORD, REG_BINARY, REG_EXPAND_SZ, REG_MULTI_SZ.

    Returns:
        A dict with status and message.
    """
    type_map: dict[str, int] = {
        "REG_SZ": winreg.REG_SZ,
        "REG_DWORD": winreg.REG_DWORD,
        "REG_BINARY": winreg.REG_BINARY,
        "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
        "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
    }
    if reg_type not in type_map:
        return {
            "status": "error",
            "message": f"Unknown reg_type '{reg_type}'. Use: {list(type_map)}",
        }
    try:
        hive, subkey = _split_path(registry_path)
        typed_data: Any = data
        if reg_type == "REG_DWORD":
            typed_data = int(data)
        with winreg.OpenKey(hive, subkey, access=winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, value_name, 0, type_map[reg_type], typed_data)
        return {
            "status": "ok",
            "message": f"Set {registry_path}\\{value_name} = {data} ({reg_type}).",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def delete_registry_value(registry_path: str, value_name: str) -> dict[str, str]:
    """Delete a specific value from a registry key.

    Args:
        registry_path: Full registry path to the key.
        value_name: Name of the value to delete.

    Returns:
        A dict with status and message.
    """
    try:
        hive, subkey = _split_path(registry_path)
        with winreg.OpenKey(hive, subkey, access=winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, value_name)
        return {
            "status": "ok",
            "message": f"Deleted value '{value_name}' from {registry_path}.",
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Value '{value_name}' not found at {registry_path}.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def delete_registry_key(registry_path: str) -> dict[str, str]:
    """Delete a registry key and all its values.

    Args:
        registry_path: Full registry path to delete (e.g. 'HKCU\\Software\\MyApp').

    Returns:
        A dict with status and message.
    """
    try:
        hive, subkey = _split_path(registry_path)
        parent_path, _, key_name = subkey.rpartition("\\")
        with winreg.OpenKey(hive, parent_path, access=winreg.KEY_ALL_ACCESS) as parent:
            winreg.DeleteKey(parent, key_name)
        return {"status": "ok", "message": f"Registry key '{registry_path}' deleted."}
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Registry key not found: {registry_path}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def restore_registry_key(reg_file_path: str) -> dict[str, str]:
    """Restore a registry key from a .reg backup file.

    Args:
        reg_file_path: Path to the .reg file to import.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"reg import '{reg_file_path}'")
        return {"status": "ok", "message": f"Registry imported from {reg_file_path}."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
