from __future__ import annotations

import config
from agents import Agent
from skills.service.tools import (
    get_service_dependencies,
    get_service_status,
    list_failed_services,
    list_services,
    restart_service,
    set_service_startup_type,
    start_service,
    stop_service,
)

SERVICE_SYSTEM_PROMPT = """
You are the Service Control Skill Agent for windowsOS-coworker.

Your role is to manage Windows services:
- Listing all services and their status
- Starting, stopping, and restarting services
- Changing service startup types
- Identifying auto-start services that have unexpectedly stopped

Always use the service's short name for commands, but display the friendly name to the user.
Warn before stopping services that other services depend on.
Do not ask the user for approval — the orchestrator handles that.
"""

service_skill_agent = Agent(
    name="ServiceSkillAgent",
    instructions=SERVICE_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_services,
        get_service_status,
        get_service_dependencies,
        list_failed_services,
        start_service,
        restart_service,
        stop_service,
        set_service_startup_type,
    ],
)
