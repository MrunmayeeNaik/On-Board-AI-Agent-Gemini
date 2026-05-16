"""Centralized Gemini API access. Every agent goes through ``call_gemini`` so the model name and API key handling stay in one place."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def get_gemini_client() -> genai.Client:
    """Construct and return a Gemini API client using the ``GEMINI_API_KEY`` env var.

    Returns:
        A configured ``google.genai.Client`` instance ready to issue requests.

    Raises:
        ValueError: When ``GEMINI_API_KEY`` is missing from the environment / ``.env`` file.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    return genai.Client(api_key=api_key)


def call_gemini(prompt: str, context: str = "") -> str:
    """Send a prompt (optionally prefixed with grounding context) to Gemini and return the text response.

    Args:
        prompt: The instruction/task text the model should respond to.
        context: Optional grounding text prepended to ``prompt`` with a blank line separator
            — typically used to inject handbook content, JSON lookups, or prior agent output.

    Returns:
        The model's text response as a string. Markdown is preserved verbatim.
    """
    client = get_gemini_client()
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt,
    )
    return response.text
