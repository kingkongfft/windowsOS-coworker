from __future__ import annotations

import config
from agents import Agent
from skills.user.tools import (
    add_user_to_group,
    create_local_user,
    disable_local_user,
    enable_local_user,
    get_logged_on_users,
    get_user_info,
    list_local_groups,
    list_local_users,
    remove_user_from_group,
    reset_local_user_password,
)

USER_SYSTEM_PROMPT = """
You are the User & Access Management Skill Agent for windowsOS-coworker.

Your role is to manage local user accounts and group membership:
- Listing local users and groups
- Creating, enabling, and disabling user accounts
- Resetting passwords
- Managing group membership
- Showing currently logged-on users

Never echo passwords back to the user or include them in summaries.
Warn before adding users to the Administrators group — explain the security implications.
Do not ask the user for approval — the orchestrator handles that.
"""

user_skill_agent = Agent(
    name="UserSkillAgent",
    instructions=USER_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_local_users,
        get_user_info,
        list_local_groups,
        get_logged_on_users,
        enable_local_user,
        create_local_user,
        disable_local_user,
        reset_local_user_password,
        add_user_to_group,
        remove_user_from_group,
    ],
)
