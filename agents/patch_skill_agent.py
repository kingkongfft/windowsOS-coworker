from __future__ import annotations

import config
from agents import Agent
from skills.patch.tools import (
    check_pending_updates,
    get_update_history,
    install_security_updates_only,
    install_updates,
    pause_windows_update,
    resume_windows_update,
    rollback_update,
    schedule_update_reboot,
)

PATCH_SYSTEM_PROMPT = """
You are the Patch & Update Skill Agent for windowsOS-coworker.

Your role is to manage Windows updates and patching:
- Checking for pending updates
- Installing all or security-only updates
- Rolling back specific KB updates
- Pausing and resuming automatic updates
- Scheduling reboots for pending updates
- Showing update history

Always list pending updates before installing.
Warn the user that some updates require a reboot to take effect.
Do not ask the user for approval — the orchestrator handles that.
"""

patch_skill_agent = Agent(
    name="PatchSkillAgent",
    instructions=PATCH_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        check_pending_updates,
        get_update_history,
        pause_windows_update,
        resume_windows_update,
        schedule_update_reboot,
        install_updates,
        install_security_updates_only,
        rollback_update,
    ],
)
