from __future__ import annotations

import config
from agents import Agent
from skills.network.tools import (
    add_firewall_rule,
    flush_dns_cache,
    get_active_connections,
    get_dns_settings,
    get_network_adapters,
    get_network_stats,
    list_firewall_rules,
    remove_firewall_rule,
    reset_network_stack,
    set_dns_servers,
    test_connectivity,
)

NETWORK_SYSTEM_PROMPT = """
You are the Network Management Skill Agent for windowsOS-coworker.

Your role is to handle all network-related operations:
- Listing adapter configuration and network stats
- Testing connectivity (ping, TCP port checks)
- Flushing the DNS cache
- Listing and managing firewall rules
- Resetting the TCP/IP stack and Winsock
- Configuring DNS servers

Present IP addresses and adapter names clearly. For firewall changes, summarise the impact.
Do not ask the user for approval — the orchestrator handles that.
"""

network_skill_agent = Agent(
    name="NetworkSkillAgent",
    instructions=NETWORK_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        get_network_adapters,
        get_network_stats,
        test_connectivity,
        get_active_connections,
        get_dns_settings,
        list_firewall_rules,
        flush_dns_cache,
        add_firewall_rule,
        remove_firewall_rule,
        reset_network_stack,
        set_dns_servers,
    ],
)
