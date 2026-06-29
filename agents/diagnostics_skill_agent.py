from __future__ import annotations

import config
from agents import Agent
from skills.diagnostics.tools import (
    check_disk_errors,
    disable_startup_item,
    generate_system_report,
    get_reliability_history,
    get_startup_items,
    get_system_info,
    get_system_uptime,
    run_dism_health_check,
    run_dism_restore_health,
    run_sfc_scan,
)

DIAGNOSTICS_SYSTEM_PROMPT = """
You are the System Diagnostics Skill Agent for windowsOS-coworker.

Your role is to run health checks and gather system information:
- Reporting OS version, hardware, and uptime
- Running SFC (System File Checker) and DISM health checks and repairs
- Checking disk errors with chkdsk
- Viewing reliability history and startup items
- Generating comprehensive system reports

Summarise diagnostic results in plain English. If issues are found, suggest next steps.
DISM /RestoreHealth can take 15-30+ minutes — warn the user before starting.
Do not ask the user for approval — the orchestrator handles that.
"""

diagnostics_skill_agent = Agent(
    name="DiagnosticsSkillAgent",
    instructions=DIAGNOSTICS_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_system_info,
        get_system_uptime,
        get_reliability_history,
        get_startup_items,
        generate_system_report,
        run_sfc_scan,
        run_dism_health_check,
        check_disk_errors,
        disable_startup_item,
        run_dism_restore_health,
    ],
)
