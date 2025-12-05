"""
utils.py — shared utilities for the Resume Agent package

- Loads environment variables (.env)
- Initializes the shared Gemini LLM client
- Provides helper functions usable across modules
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# --------------------------------------------------------
# Load environment variables from .env
# --------------------------------------------------------

load_dotenv()   # ensures GOOGLE_API_KEY is loaded

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment. Please set it in your .env file.")

# --------------------------------------------------------
# Create a single shared LLM instance
# --------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# --------------------------------------------------------
# Helper: strip fences (optional, used if needed)
# --------------------------------------------------------

def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```json"):
        t = t[len("```json"):].strip()
    if t.startswith("```"):
        t = t[3:].strip()
    if t.endswith("```"):
        t = t[:-3].strip()
    return t
