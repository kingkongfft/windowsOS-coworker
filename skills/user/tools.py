from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def list_local_users() -> dict[str, str]:
    """List all local user accounts on this machine.

    Returns:
        A dict with status and a 'users' table string.
    """
    try:
        result = run_ps(
            "Get-LocalUser | Select-Object Name, Enabled, LastLogon, PasswordLastSet, "
            "Description | Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "users": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_user_info(username: str) -> dict[str, str]:
    """Get detailed information about a specific local user account.

    Args:
        username: The local account username.

    Returns:
        A dict with status and user details.
    """
    try:
        result = run_ps(
            f"Get-LocalUser -Name '{username}' -ErrorAction Stop | Format-List | Out-String"
        )
        return {"status": "ok", "user_info": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_local_groups() -> dict[str, str]:
    """List all local groups and their members.

    Returns:
        A dict with status and a 'groups' table string.
    """
    try:
        result = run_ps(
            "Get-LocalGroup | ForEach-Object { "
            "$members = (Get-LocalGroupMember $_.Name -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty Name) -join ', '; "
            "[PSCustomObject]@{Group=$_.Name; Members=$members} } | "
            "Format-Table -AutoSize -Wrap | Out-String"
        )
        return {"status": "ok", "groups": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_logged_on_users() -> dict[str, str]:
    """Show users currently logged on to this machine.

    Returns:
        A dict with status and 'logged_on_users' string.
    """
    try:
        result = run_ps("query user 2>&1 | Out-String")
        return {"status": "ok", "logged_on_users": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def enable_local_user(username: str) -> dict[str, str]:
    """Enable a disabled local user account.

    Args:
        username: The local account username to enable.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Enable-LocalUser -Name '{username}' -ErrorAction Stop")
        return {"status": "ok", "message": f"User '{username}' enabled."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def create_local_user(
    username: str, password: str, full_name: str = "", description: str = ""
) -> dict[str, str]:
    """Create a new local user account.

    Args:
        username: Username for the new account.
        password: Password for the new account.
        full_name: Optional full name.
        description: Optional description.

    Returns:
        A dict with status and message.
    """
    try:
        full_clause = f"-FullName '{full_name}' " if full_name else ""
        desc_clause = f"-Description '{description}' " if description else ""
        run_ps(
            f"$pw = ConvertTo-SecureString '{password}' -AsPlainText -Force; "
            f"New-LocalUser -Name '{username}' -Password $pw {full_clause}{desc_clause}-ErrorAction Stop"
        )
        return {"status": "ok", "message": f"User '{username}' created."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def disable_local_user(username: str) -> dict[str, str]:
    """Disable a local user account without deleting it.

    Args:
        username: The local account username to disable.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(f"Disable-LocalUser -Name '{username}' -ErrorAction Stop")
        return {"status": "ok", "message": f"User '{username}' disabled."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def reset_local_user_password(username: str, new_password: str) -> dict[str, str]:
    """Reset the password for a local user account.

    Args:
        username: The local account username.
        new_password: The new password to set.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            f"$pw = ConvertTo-SecureString '{new_password}' -AsPlainText -Force; "
            f"Set-LocalUser -Name '{username}' -Password $pw -ErrorAction Stop"
        )
        return {"status": "ok", "message": f"Password for '{username}' reset."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def add_user_to_group(username: str, group_name: str) -> dict[str, str]:
    """Add a local user to a local group.

    Args:
        username: The local account username.
        group_name: The local group name (e.g. 'Administrators', 'Remote Desktop Users').

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            f"Add-LocalGroupMember -Group '{group_name}' -Member '{username}' -ErrorAction Stop"
        )
        return {
            "status": "ok",
            "message": f"User '{username}' added to group '{group_name}'.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def remove_user_from_group(username: str, group_name: str) -> dict[str, str]:
    """Remove a local user from a local group.

    Args:
        username: The local account username.
        group_name: The local group name.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps(
            f"Remove-LocalGroupMember -Group '{group_name}' -Member '{username}' -ErrorAction Stop"
        )
        return {
            "status": "ok",
            "message": f"User '{username}' removed from group '{group_name}'.",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
