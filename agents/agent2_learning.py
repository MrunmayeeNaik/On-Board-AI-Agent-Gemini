from utils.gemini_client import call_gemini
from utils.doc_loader import load_pdf
from utils.prompt_templates import agent2_prompt
import os

def run_agent2(name: str, role: str, department: str, agent1_output: str) -> str:
    """Run the Learning Path Generator: load handbook context and Agent 1's output, then ask Gemini for a 30-60-90 day plan."""
    # Load company handbook if exists
    handbook_path = os.path.join("data", "company_handbook.pdf")
    handbook_text = ""
    
    if os.path.exists(handbook_path):
        handbook_text = load_pdf(handbook_path)
        handbook_context = f"""
                            Company Handbook Content:
                            {handbook_text[:3000]}
                            """
    else:
        handbook_context = """
                            Company Handbook:
                            - Annual learning budget: ₹50,000
                            - Udemy and Coursera access provided
                            - Quarterly performance reviews
                            - 360 degree feedback annually
                            """

    # Build prompt
    prompt = agent2_prompt(
        name=name,
        role=role,
        department=department,
        agent1_output=agent1_output
    )

    # Combine handbook context with agent1 output
    context = f"""
                {handbook_context}

                Agent 1 Provisioning Output:
                {agent1_output}
                """

    # Call Gemini
    output = call_gemini(prompt=prompt, context=context)
    return output