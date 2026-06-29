from __future__ import annotations

import config
from agents import Agent
from skills.memory.tools import (
    clear_file_system_cache,
    get_memory_usage,
    get_paging_file_info,
    identify_memory_leak_suspects,
    list_top_memory_processes,
    release_standby_memory,
    set_paging_file_size,
)

MEMORY_SYSTEM_PROMPT = """
You are the Memory Management Skill Agent for windowsOS-coworker.

Your role is to handle all RAM and memory-related operations:
- Reporting current memory usage
- Identifying processes using the most memory
- Releasing standby/cached memory
- Investigating memory leak suspects
- Configuring the paging file

Always present memory sizes in GB or MB as appropriate.
When identifying memory hogs, suggest action if usage looks abnormal.
Do not ask the user for approval — the orchestrator handles that.
"""

memory_skill_agent = Agent(
    name="MemorySkillAgent",
    instructions=MEMORY_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_memory_usage,
        list_top_memory_processes,
        get_paging_file_info,
        identify_memory_leak_suspects,
        release_standby_memory,
        clear_file_system_cache,
        set_paging_file_size,
    ],
)
