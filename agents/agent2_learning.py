"""Agent 2 — Learning Path Generator. Combines the company handbook and Agent 1's output to produce a 30-60-90 day plan."""

from utils.gemini_client import call_gemini
from utils.prompt_templates import agent2_prompt


def run_agent2(
    name: str,
    role: str,
    department: str,
    agent1_output: str,
    handbook_text: str = "",
) -> str:
    """Run the Learning Path Generator: combine the handbook text and Agent 1's output, then ask Gemini for a 30-60-90 day plan.

    Args:
        name: Employee's name (passed through to the prompt for personalization).
        role: Job title used to tailor learning recommendations.
        department: Department name used to scope the plan.
        agent1_output: Raw Markdown produced by Agent 1; flowed in as context so Agent 2
            references the same tools and contacts.
        handbook_text: Extracted handbook text. When empty, a small default policy block
            is used instead so the prompt still has *some* grounding signal.

    Returns:
        Markdown string with the 30-60-90 day plan using ``- [ ]`` task items. Lengths
        roughly match what the Learning Path tab is sized to display.
    """
    if handbook_text.strip():
        handbook_context = f"Company Handbook Content:\n{handbook_text}"
    else:
        handbook_context = (
            "Company Handbook (defaults):\n"
            "- Annual learning budget: ₹50,000\n"
            "- Udemy and Coursera access provided\n"
            "- Quarterly performance reviews\n"
            "- 360 degree feedback annually\n"
        )

    prompt = agent2_prompt(
        name=name,
        role=role,
        department=department,
        agent1_output=agent1_output,
    )

    context = f"""{handbook_context}

Agent 1 Provisioning Output:
{agent1_output}
"""

    return call_gemini(prompt=prompt, context=context)
