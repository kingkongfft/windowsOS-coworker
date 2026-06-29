from __future__ import annotations

import config
from agents import Agent
from skills.disk.tools import (
    analyze_disk_usage,
    clean_recycle_bin,
    clean_temp_files,
    clean_windows_update_cache,
    defrag_drive,
    get_disk_usage,
    get_drive_health,
    list_large_files,
    list_partitions,
)

DISK_SYSTEM_PROMPT = """
You are the Disk Management Skill Agent for windowsOS-coworker.

Your role is to handle all disk-related operations:
- Reporting disk usage and partition information
- Identifying large files and folders consuming space
- Cleaning up temporary files, recycle bin, and caches
- Defragmenting and optimising drives
- Checking drive health

Always report disk sizes in human-readable format (GB/MB).
When cleaning, always report how much space was freed.
For medium/high risk actions, the orchestrator will handle approval — do not ask the user yourself.
When done, return a clear plain-English summary of what was done and the outcome.
"""

disk_skill_agent = Agent(
    name="DiskSkillAgent",
    instructions=DISK_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_disk_usage,
        list_partitions,
        analyze_disk_usage,
        list_large_files,
        get_drive_health,
        clean_temp_files,
        clean_recycle_bin,
        clean_windows_update_cache,
        defrag_drive,
    ],
)
