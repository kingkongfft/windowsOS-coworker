from __future__ import annotations

import config
from agents import Agent

from skills.files.tools import (
    append_to_file,
    copy_file,
    create_directory,
    create_file,
    delete_directory,
    delete_file,
    file_exists,
    list_directory,
    move_file,
    read_file,
    write_file,
)

FILES_SYSTEM_PROMPT = """
You are the File Operations Skill Agent for windowsOS-coworker.

Your role is to handle all file and directory operations on the Windows file system:
- Creating, reading, writing, and appending to files
- Listing directory contents
- Moving, copying, and deleting files
- Creating and deleting directories
- Checking whether files or directories exist

Key rules:
- Expand environment variables like %USERPROFILE%, %TEMP%, %SystemRoot% in paths.
- Always confirm the full resolved path in your response.
- For destructive operations (delete, overwrite) briefly state what will be removed.
- Do not ask the user for approval — the orchestrator handles that.
- Return clear success or error messages after every operation.
"""

files_skill_agent = Agent(
    name="FileSkillAgent",
    instructions=FILES_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        create_file,
        read_file,
        write_file,
        append_to_file,
        list_directory,
        delete_file,
        move_file,
        copy_file,
        file_exists,
        create_directory,
        delete_directory,
    ],
)
