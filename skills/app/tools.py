from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_installed_apps(name_filter: str = "") -> dict[str, str]:
    """List installed applications, optionally filtered by name.

    Args:
        name_filter: Optional substring to filter app names (case-insensitive).

    Returns:
        A dict with status and an 'apps' table string.
    """
    try:
        filter_clause = f"--name '{name_filter}'" if name_filter else ""
        result = run_ps(f"winget list {filter_clause} | Out-String")
        return {"status": "ok", "apps": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def search_available_app(query: str) -> dict[str, str]:
    """Search the winget catalog for an application.

    Args:
        query: Search term (app name, publisher, or keyword).

    Returns:
        A dict with status and 'results' string from the winget catalog.
    """
    try:
        result = run_ps(f"winget search '{query}' | Out-String")
        return {"status": "ok", "results": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_app_info(app_id: str) -> dict[str, str]:
    """Get detailed information about an application in the winget catalog.

    Args:
        app_id: The winget package ID (e.g. 'Python.Python.3.12').

    Returns:
        A dict with status and 'info' string.
    """
    try:
        result = run_ps(f"winget show '{app_id}' | Out-String")
        return {"status": "ok", "info": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def check_app_installed(app_name: str) -> dict[str, str]:
    """Check whether a specific application is installed.

    Args:
        app_name: Display name or partial name to search for.

    Returns:
        A dict with status, 'installed' (true/false), and 'details'.
    """
    try:
        result = run_ps(f"winget list --name '{app_name}' | Out-String")
        installed = app_name.lower() in result.stdout.lower()
        return {
            "status": "ok",
            "installed": str(installed).lower(),
            "details": result.stdout,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def update_app(app_id: str) -> dict[str, str]:
    """Update a specific application to the latest version via winget.

    Args:
        app_id: The winget package ID.

    Returns:
        A dict with status and the update output.
    """
    try:
        result = run_ps(
            f"winget upgrade --id '{app_id}' --silent --accept-package-agreements --accept-source-agreements | Out-String",
            timeout=300,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def install_app(app_id: str) -> dict[str, str]:
    """Install an application silently via winget.

    Args:
        app_id: The winget package ID (e.g. 'Python.Python.3.12').

    Returns:
        A dict with status and the install output.
    """
    try:
        result = run_ps(
            f"winget install --id '{app_id}' --silent "
            "--accept-package-agreements --accept-source-agreements | Out-String",
            timeout=600,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def uninstall_app(app_id: str) -> dict[str, str]:
    """Uninstall an application silently via winget.

    Args:
        app_id: The winget package ID or display name.

    Returns:
        A dict with status and the uninstall output.
    """
    try:
        result = run_ps(
            f"winget uninstall --id '{app_id}' --silent | Out-String",
            timeout=300,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def update_all_apps() -> dict[str, str]:
    """Update all installed applications to their latest versions via winget.

    Returns:
        A dict with status and the upgrade output.
    """
    try:
        result = run_ps(
            "winget upgrade --all --silent --accept-package-agreements --accept-source-agreements | Out-String",
            timeout=1800,
        )
        return {"status": "ok", "message": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
