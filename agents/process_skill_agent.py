from __future__ import annotations

import config
from agents import Agent
from skills.process.tools import (
    find_process_by_name,
    get_process_details,
    get_process_network_connections,
    get_process_open_files,
    kill_process,
    list_processes,
    resume_process,
    suspend_process,
)

PROCESS_SYSTEM_PROMPT = """
You are the Process Management Skill Agent for windowsOS-coworker.

Your role is to handle all process-related operations:
- Listing and searching running processes
- Inspecting process details, open files, and network connections
- Suspending, resuming, and terminating processes

Always identify a process by both name and PID for clarity.
Warn the user if they attempt to kill a critical system process (e.g. svchost, lsass, csrss).
Do not ask the user for approval — the orchestrator handles that.
"""

process_skill_agent = Agent(
    name="ProcessSkillAgent",
    instructions=PROCESS_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_processes,
        get_process_details,
        find_process_by_name,
        get_process_open_files,
        get_process_network_connections,
        suspend_process,
        resume_process,
        kill_process,
    ],
)
