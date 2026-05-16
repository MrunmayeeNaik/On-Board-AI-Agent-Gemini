"""Agent 3 — HR Buddy. Stateless wrapper around Gemini; the orchestrator passes prior chat history in on every call."""

from utils.gemini_client import call_gemini
from utils.prompt_templates import agent3_prompt


def run_agent3(
    question: str,
    chat_history: str = "",
    handbook_text: str = "",
    contacts_text: str = "",
) -> str:
    """Run the HR Buddy for one chat turn: build the HR-grounded prompt with handbook, history, and contacts, then return Gemini's answer.

    Args:
        question: The user's current question.
        chat_history: Prior conversation rendered as ``"ROLE: content"`` lines, used to keep
            the multi-turn chat coherent across orchestrator calls.
        handbook_text: Extracted handbook text. When non-empty the model is instructed to
            cite section names in its answer.
        contacts_text: Markdown excerpt of Agent 1's ``Key Contacts`` section so the model
            can name a specific person on escalation.

    Returns:
        Markdown answer suitable for direct display in ``st.chat_message``.
    """
    prompt = agent3_prompt(
        question=question,
        chat_history=chat_history,
        handbook_text=handbook_text,
        contacts_text=contacts_text,
    )
    return call_gemini(prompt=prompt)
