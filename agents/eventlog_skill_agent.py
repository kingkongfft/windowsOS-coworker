from __future__ import annotations

import config
from agents import Agent
from skills.eventlog.tools import (
    clear_event_log,
    export_event_log,
    get_application_errors,
    get_recent_errors,
    get_system_crashes,
    list_event_logs,
    query_event_log,
)

EVENTLOG_SYSTEM_PROMPT = """
You are the Event Log Skill Agent for windowsOS-coworker.

Your role is to query and analyse Windows Event Logs:
- Listing available log channels
- Querying events with flexible filters (level, time, keyword)
- Summarising recent errors and critical events
- Identifying system crashes (BSODs)
- Exporting events to CSV
- Clearing log channels (high risk)

When reporting errors, provide a plain-English summary: what happened, which component, when.
Group similar errors and highlight the most severe ones first.
Do not ask the user for approval — the orchestrator handles that.
"""

eventlog_skill_agent = Agent(
    name="EventLogSkillAgent",
    instructions=EVENTLOG_SYSTEM_PROMPT,
    model=config.AGENT_MODEL,
    tools=[
        list_event_logs,
        get_recent_errors,
        query_event_log,
        get_system_crashes,
        get_application_errors,
        export_event_log,
        clear_event_log,
    ],
)
