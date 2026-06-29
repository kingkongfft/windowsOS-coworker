from __future__ import annotations

import config
from agents import Agent
from skills.taskscheduler.tools import (
    create_task,
    delete_task,
    disable_task,
    enable_task,
    get_task_details,
    get_task_run_history,
    list_scheduled_tasks,
    run_task_now,
)

TASKSCHEDULER_SYSTEM_PROMPT = """
You are the Task Scheduler Skill Agent for windowsOS-coworker.

Your role is to manage Windows scheduled tasks:
- Listing all scheduled tasks
- Getting task details and run history
- Running tasks immediately
- Enabling, disabling, creating, and deleting tasks

When creating tasks, confirm the schedule and command with the user before proceeding.
Show last run results when listing tasks to help identify failing tasks.
Do not ask the user for approval — the orchestrator handles that.
"""

taskscheduler_skill_agent = Agent(
    name="TaskSchedulerSkillAgent",
    instructions=TASKSCHEDULER_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_scheduled_tasks,
        get_task_details,
        get_task_run_history,
        run_task_now,
        enable_task,
        disable_task,
        create_task,
        delete_task,
    ],
)
