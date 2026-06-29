from __future__ import annotations

import config
from agents import Agent
from skills.app.tools import (
    check_app_installed,
    get_app_info,
    install_app,
    list_installed_apps,
    search_available_app,
    uninstall_app,
    update_all_apps,
    update_app,
)

APP_SYSTEM_PROMPT = """
You are the App Management Skill Agent for windowsOS-coworker.

Your role is to manage software installation and removal:
- Listing installed applications
- Searching the winget catalog for available software
- Installing, updating, and uninstalling applications
- Checking whether a specific app is installed

Always use winget package IDs for install/uninstall operations.
If the user gives an app name, search the catalog first to find the correct package ID.
Do not ask the user for approval — the orchestrator handles that.
"""

app_skill_agent = Agent(
    name="AppSkillAgent",
    instructions=APP_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_installed_apps,
        search_available_app,
        get_app_info,
        check_app_installed,
        update_app,
        install_app,
        uninstall_app,
        update_all_apps,
    ],
)
