from __future__ import annotations

import config
from agents import Agent
from skills.registry.tools import (
    backup_registry_key,
    delete_registry_key,
    delete_registry_value,
    list_registry_subkeys,
    read_registry_key,
    restore_registry_key,
    search_registry,
    write_registry_value,
)

REGISTRY_SYSTEM_PROMPT = """
You are the Registry Skill Agent for windowsOS-coworker.

Your role is to safely manage the Windows Registry:
- Reading and browsing registry keys and values
- Searching the registry for key or value patterns
- Writing and deleting registry values and keys
- Backing up and restoring registry keys

IMPORTANT: Always back up a registry key before modifying or deleting it.
Always use the full path format: HKLM\\path\\to\\key or HKCU\\path\\to\\key.
Clearly explain what a registry change will do before proceeding.
Do not ask the user for approval — the orchestrator handles that.
"""

registry_skill_agent = Agent(
    name="RegistrySkillAgent",
    instructions=REGISTRY_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        read_registry_key,
        list_registry_subkeys,
        backup_registry_key,
        search_registry,
        write_registry_value,
        delete_registry_value,
        delete_registry_key,
        restore_registry_key,
    ],
)
