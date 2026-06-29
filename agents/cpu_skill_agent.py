from __future__ import annotations

import config
from agents import Agent
from skills.cpu.tools import (
    get_cpu_temperature,
    get_cpu_usage,
    get_power_plan,
    kill_high_cpu_process,
    list_top_cpu_processes,
    set_power_plan,
    set_process_affinity,
    set_process_priority,
)

CPU_SYSTEM_PROMPT = """
You are the CPU Management Skill Agent for windowsOS-coworker.

Your role is to handle all CPU-related operations:
- Reporting overall and per-core CPU usage
- Identifying processes consuming the most CPU
- Adjusting process priority and CPU affinity
- Managing Windows power plans
- Reading CPU temperature if available
- Terminating runaway high-CPU processes

Present CPU percentages clearly. When a process is using unexpected CPU, explain what it is.
Do not ask the user for approval — the orchestrator handles that.
"""

cpu_skill_agent = Agent(
    name="CpuSkillAgent",
    instructions=CPU_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_cpu_usage,
        list_top_cpu_processes,
        get_power_plan,
        get_cpu_temperature,
        set_process_priority,
        set_process_affinity,
        set_power_plan,
        kill_high_cpu_process,
    ],
)
