from utils.gemini_client import call_gemini
from utils.prompt_templates import agent3_prompt

def run_agent3(question: str, chat_history: str = "") -> str:
    """Run the HR Buddy for one chat turn: build the HR-grounded prompt with prior history and return Gemini's answer."""
    # Build prompt
    prompt = agent3_prompt(
        question=question,
        chat_history=chat_history
    )
    
    # Call Gemini
    output = call_gemini(prompt=prompt)
    return output