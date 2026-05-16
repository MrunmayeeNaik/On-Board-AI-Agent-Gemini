"""Agent 1 — Provisioning Coordinator. JSON-first, LLM-second: deterministic lookups for tools/org/schedule, then Gemini renders the narrative."""

import json

from utils.doc_loader import load_org_chart, load_tools
from utils.gemini_client import call_gemini
from utils.prompt_templates import agent1_prompt


def run_agent1(name: str, role: str, department: str) -> str:
    """Run the Provisioning Coordinator: look up tools, org chart, and Day-1 schedule from JSON, then have Gemini render the onboarding narrative.

    Args:
        name: New employee's full name.
        role: Job title.
        department: One of ``Engineering``, ``Marketing``, ``Sales``, ``HR`` — drives all
            three JSON lookups.

    Returns:
        Markdown string with the welcome, tool-provisioning checklist, Day-1 schedule, and
        key contacts. Actionable items use ``- [ ]`` task syntax for downstream tracking.
    """
    tools = load_tools(department)
    org = load_org_chart(department)

    try:
        with open("data/schedules.json") as f:
            schedules = json.load(f)
        schedule = schedules.get(department, {})
    except FileNotFoundError:
        schedule = {}

    prompt = agent1_prompt(
        name=name,
        role=role,
        department=department,
        tools=tools,
    )

    # The deterministic lookups go into the *context* (not the prompt itself) so they
    # ground the model without bloating the instructions.
    context = f"""
                Company Context:
                - Department Head: {org.get("head", "TBD")}
                - Department Head Email: {org.get("email", "TBD")}
                - Team Size: {org.get("team_size", "TBD")} people

                Day 1 Schedule:
                {json.dumps(schedule, indent=2)}
            """

    return call_gemini(prompt=prompt, context=context)
