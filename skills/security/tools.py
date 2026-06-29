from __future__ import annotations

from agents import function_tool

from core.powershell import run_ps
from core.risk import Risk, risk


@risk(Risk.LOW)
@function_tool
def get_defender_status() -> dict[str, str]:
    """Show Windows Defender / antivirus status and last scan time.

    Returns:
        A dict with status and 'defender_status' string.
    """
    try:
        result = run_ps(
            "Get-MpComputerStatus | Select-Object AMServiceEnabled, AntispywareEnabled, "
            "AntivirusEnabled, RealTimeProtectionEnabled, QuickScanAge, FullScanAge, "
            "AntivirusSignatureLastUpdated | Format-List | Out-String"
        )
        return {"status": "ok", "defender_status": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_firewall_status() -> dict[str, str]:
    """Show Windows Firewall status for Domain, Private, and Public profiles.

    Returns:
        A dict with status and 'firewall_status' string.
    """
    try:
        result = run_ps(
            "Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, "
            "DefaultOutboundAction | Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "firewall_status": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_bitlocker_status() -> dict[str, str]:
    """Show BitLocker drive encryption status for all volumes.

    Returns:
        A dict with status and 'bitlocker_status' string.
    """
    try:
        result = run_ps(
            "Get-BitLockerVolume -ErrorAction SilentlyContinue | "
            "Select-Object MountPoint, VolumeStatus, EncryptionPercentage, ProtectionStatus | "
            "Format-Table -AutoSize | Out-String"
        )
        output = (
            result.stdout.strip() or "BitLocker cmdlets not available on this edition."
        )
        return {"status": "ok", "bitlocker_status": output}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def get_audit_policy() -> dict[str, str]:
    """Show the local security audit policy settings.

    Returns:
        A dict with status and 'audit_policy' string.
    """
    try:
        result = run_ps("auditpol /get /category:* | Out-String")
        return {"status": "ok", "audit_policy": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_open_shares() -> dict[str, str]:
    """List SMB shares exposed on this machine.

    Returns:
        A dict with status and a 'shares' table string.
    """
    try:
        result = run_ps(
            "Get-SmbShare | Select-Object Name, Path, Description, CurrentUsers | "
            "Format-Table -AutoSize | Out-String"
        )
        return {"status": "ok", "shares": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def check_uac_level() -> dict[str, str]:
    """Check the User Account Control (UAC) configuration level.

    Returns:
        A dict with status and 'uac_level' description.
    """
    try:
        result = run_ps(
            "$val = (Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
            "-Name ConsentPromptBehaviorAdmin -ErrorAction Stop).ConsentPromptBehaviorAdmin; "
            "@{0='Never notify';1='Notify app changes (no dimming)';2='Notify app changes (dim)';5='Always notify'}[$val]"
        )
        return {"status": "ok", "uac_level": result.stdout.strip()}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def list_installed_certificates(store: str = "My") -> dict[str, str]:
    """List certificates in a local certificate store.

    Args:
        store: Certificate store name: 'My', 'Root', 'CA', 'TrustedPublisher'. Default 'My'.

    Returns:
        A dict with status and a 'certificates' table string.
    """
    try:
        result = run_ps(
            f"Get-ChildItem -Path 'Cert:\\LocalMachine\\{store}' -ErrorAction SilentlyContinue | "
            "Select-Object Subject, Thumbprint, NotAfter, Issuer | "
            "Format-Table -AutoSize -Wrap | Out-String"
        )
        return {"status": "ok", "certificates": result.stdout}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.LOW)
@function_tool
def scan_open_ports() -> dict[str, str]:
    """List ports currently listening on this machine.

    Returns:
        A dict with status and a 'ports' table string.
    """
    try:
        import psutil

        conns = psutil.net_connections()
        listening = [c for c in conns if c.status == "LISTEN" and c.laddr]
        listening.sort(key=lambda c: c.laddr.port)
        lines = ["PORT   PROTO  PID    ADDRESS"]
        seen: set[int] = set()
        for c in listening:
            if c.laddr.port not in seen:
                seen.add(c.laddr.port)
                lines.append(
                    f"{c.laddr.port:<6} {c.type.name:<6} {c.pid or '-':<6} {c.laddr.ip}"
                )
        return {"status": "ok", "ports": "\n".join(lines)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.MEDIUM)
@function_tool
def run_defender_quick_scan() -> dict[str, str]:
    """Trigger a Windows Defender quick scan.

    Returns:
        A dict with status and message.
    """
    try:
        run_ps("Start-MpScan -ScanType QuickScan -ErrorAction Stop")
        return {"status": "ok", "message": "Windows Defender quick scan initiated."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@risk(Risk.HIGH)
@function_tool
def enable_bitlocker(
    drive: str = "C:", recovery_password: bool = True
) -> dict[str, str]:
    """Enable BitLocker encryption on a drive.

    Args:
        drive: Drive letter with colon (e.g. 'C:').
        recovery_password: Whether to generate a recovery password key protector.

    Returns:
        A dict with status and message. Encryption runs in the background.
    """
    try:
        password_clause = "-RecoveryPasswordProtector " if recovery_password else ""
        result = run_ps(
            f"Enable-BitLocker -MountPoint '{drive}' {password_clause}-ErrorAction Stop | Out-String",
            timeout=120,
        )
        return {
            "status": "ok",
            "message": f"BitLocker encryption started on {drive}. "
            f"Encryption runs in the background.\n{result.stdout}",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
