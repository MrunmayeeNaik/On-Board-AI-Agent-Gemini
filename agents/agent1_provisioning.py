from utils.gemini_client import call_gemini
from utils.doc_loader import load_tools, load_org_chart
from utils.prompt_templates import agent1_prompt
import json

def run_agent1(name: str, role: str, department: str) -> str:
    """Run the Provisioning Coordinator: look up tools, org, and schedule from JSON, then have Gemini render the onboarding narrative."""
    # Load data from JSON files
    tools = load_tools(department)
    org = load_org_chart(department)
    
    # Load schedule
    try:
        with open("data/schedules.json", "r") as f:
            schedules = json.load(f)
        schedule = schedules.get(department, {})
    except FileNotFoundError:
        schedule = {}
    
    # Build prompt
    prompt = agent1_prompt(
        name=name,
        role=role,
        department=department,
        tools=tools
    )
    
    # Add org and schedule context
    context = f"""
                Company Context:
                - Department Head: {org.get('head', 'TBD')}
                - Department Head Email: {org.get('email', 'TBD')}
                - Team Size: {org.get('team_size', 'TBD')} people

                Day 1 Schedule:
                {json.dumps(schedule, indent=2)}
            """
    
    # Call Gemini
    output = call_gemini(prompt=prompt, context=context)
    return output