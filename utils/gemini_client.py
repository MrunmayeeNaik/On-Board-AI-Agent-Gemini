import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    client = genai.Client(api_key=api_key)
    return client

def call_gemini(prompt: str, context: str = "") -> str:
    client = get_gemini_client()
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt
    )
    return response.text