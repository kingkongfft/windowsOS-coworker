from __future__ import annotations

import config
from agents import Agent
from skills.envconfig.tools import (
    add_to_path,
    delete_env_variable,
    disable_windows_feature,
    enable_windows_feature,
    get_env_variable,
    get_path_entries,
    get_power_plans,
    get_windows_features,
    list_env_variables,
    remove_from_path,
    set_env_variable,
    set_power_plan,
)

ENVCONFIG_SYSTEM_PROMPT = """
You are the Environment & Config Skill Agent for windowsOS-coworker.

Your role is to manage system environment and configuration:
- Listing, reading, setting, and deleting environment variables
- Managing PATH entries
- Listing and switching Windows power plans
- Enabling and disabling Windows optional features

When modifying PATH or environment variables, show the before/after values.
Warn if removing a PATH entry that might break existing tools.
Do not ask the user for approval — the orchestrator handles that.
"""

envconfig_skill_agent = Agent(
    name="EnvConfigSkillAgent",
    instructions=ENVCONFIG_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_env_variables,
        get_env_variable,
        get_path_entries,
        get_power_plans,
        get_windows_features,
        set_power_plan,
        set_env_variable,
        delete_env_variable,
        add_to_path,
        remove_from_path,
        enable_windows_feature,
        disable_windows_feature,
    ],
)
