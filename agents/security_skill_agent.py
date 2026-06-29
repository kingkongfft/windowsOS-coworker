from __future__ import annotations

import config
from agents import Agent
from skills.security.tools import (
    check_uac_level,
    enable_bitlocker,
    get_audit_policy,
    get_bitlocker_status,
    get_defender_status,
    get_firewall_status,
    list_installed_certificates,
    list_open_shares,
    run_defender_quick_scan,
    scan_open_ports,
)

SECURITY_SYSTEM_PROMPT = """
You are the Security & Compliance Skill Agent for windowsOS-coworker.

Your role is to assess and manage the security posture of this Windows machine:
- Checking Windows Defender and antivirus status
- Reviewing Windows Firewall configuration
- Checking BitLocker encryption status
- Reviewing audit policy settings
- Listing open SMB shares and listening ports
- Checking UAC configuration
- Browsing certificate stores
- Enabling BitLocker encryption

Always frame security findings in terms of risk: what is exposed, to whom, and how to fix it.
Do not ask the user for approval — the orchestrator handles that.
"""

security_skill_agent = Agent(
    name="SecuritySkillAgent",
    instructions=SECURITY_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_defender_status,
        get_firewall_status,
        get_bitlocker_status,
        get_audit_policy,
        list_open_shares,
        check_uac_level,
        list_installed_certificates,
        scan_open_ports,
        run_defender_quick_scan,
        enable_bitlocker,
    ],
)
