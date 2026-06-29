from __future__ import annotations

import os
import shutil
from pathlib import Path

from agents import function_tool

from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def create_file(path: str, content: str = "") -> dict[str, str]:
    """Create a new file at the given path with optional content.

    Parent directories are created automatically if they do not exist.
    Supports environment variable expansion (e.g. %USERPROFILE%).

    Args:
        path: Full or relative path to the file to create.
        content: Optional text content to write into the file.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return {"status": "ok", "message": f"File created: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def read_file(path: str) -> dict[str, str]:
    """Read and return the text content of a file.

    Args:
        path: Full or relative path to the file.

    Returns:
        A dict with status and content (or message on error).
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        content = resolved.read_text(encoding="utf-8", errors="replace")
        return {"status": "ok", "content": content}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_directory(path: str = "%USERPROFILE%") -> dict[str, str]:
    """List files and folders in a directory.

    Args:
        path: Directory path to list. Defaults to the user's home folder.

    Returns:
        A dict with status and a listing string.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        entries = sorted(
            resolved.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
        lines = []
        for entry in entries:
            kind = "FILE" if entry.is_file() else "DIR "
            size = f"{entry.stat().st_size:>12,} B" if entry.is_file() else ""
            lines.append(f"{kind}  {entry.name:<50} {size}")
        return {"status": "ok", "listing": "\n".join(lines) or "(empty)"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def write_file(path: str, content: str) -> dict[str, str]:
    """Overwrite a file with new content (creates it if it does not exist).

    Args:
        path: Full or relative path to the file.
        content: Text content to write.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return {"status": "ok", "message": f"File written: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def append_to_file(path: str, content: str) -> dict[str, str]:
    """Append text to the end of an existing file (creates it if absent).

    Args:
        path: Full or relative path to the file.
        content: Text to append.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("a", encoding="utf-8") as f:
            f.write(content)
        return {"status": "ok", "message": f"Content appended to: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def delete_file(path: str) -> dict[str, str]:
    """Delete a file.

    Args:
        path: Full or relative path to the file to delete.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        resolved.unlink()
        return {"status": "ok", "message": f"File deleted: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def move_file(source: str, destination: str) -> dict[str, str]:
    """Move or rename a file.

    Args:
        source: Current path of the file.
        destination: Target path (including new filename if renaming).

    Returns:
        A dict with status and message.
    """
    try:
        src = Path(os.path.expandvars(source)).expanduser()
        dst = Path(os.path.expandvars(destination)).expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"status": "ok", "message": f"Moved: {src} -> {dst}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def copy_file(source: str, destination: str) -> dict[str, str]:
    """Copy a file to a new location.

    Args:
        source: Path of the file to copy.
        destination: Target path for the copy.

    Returns:
        A dict with status and message.
    """
    try:
        src = Path(os.path.expandvars(source)).expanduser()
        dst = Path(os.path.expandvars(destination)).expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        return {"status": "ok", "message": f"Copied: {src} -> {dst}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def file_exists(path: str) -> dict[str, str]:
    """Check whether a file or directory exists at the given path.

    Args:
        path: Path to check.

    Returns:
        A dict with status, exists (true/false), and type (file/directory/none).
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        if resolved.is_file():
            kind = "file"
        elif resolved.is_dir():
            kind = "directory"
        else:
            kind = "none"
        return {
            "status": "ok",
            "exists": str(resolved.exists()).lower(),
            "type": kind,
            "path": str(resolved),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def delete_directory(path: str, recursive: bool = False) -> dict[str, str]:
    """Delete a directory.

    Args:
        path: Path to the directory to delete.
        recursive: If True, delete all contents recursively. Defaults to False.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        if recursive:
            shutil.rmtree(str(resolved))
        else:
            resolved.rmdir()
        return {"status": "ok", "message": f"Directory deleted: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def create_directory(path: str) -> dict[str, str]:
    """Create a directory (and any missing parent directories).

    Args:
        path: Path of the directory to create.

    Returns:
        A dict with status and message.
    """
    try:
        resolved = Path(os.path.expandvars(path)).expanduser()
        resolved.mkdir(parents=True, exist_ok=True)
        return {"status": "ok", "message": f"Directory created: {resolved}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
