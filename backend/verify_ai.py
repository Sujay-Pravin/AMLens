"""
Phase 0 — Google AI Studio Connectivity Verification Script
Run this to confirm the Google GenAI client can reach the chosen model.

Usage:
    python verify_ai.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def verify_ai_connection():
    """Verify Google AI Studio API connectivity with a simple generation."""
    token = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")

    if not token or token == "your_api_key_here":
        print("=" * 60)
        print("ERROR: GEMINI_API_KEY not set or still placeholder.")
        print("Please update your .env file with a valid Google AI Studio token.")
        print("=" * 60)
        sys.exit(1)

    print(f"Model:  {model}")
    print(f"Token:  {token[:8]}...{token[-4:]}")
    print("-" * 60)

    try:
        from google import genai
        client = genai.Client(api_key=token)

        print("Sending test content generation...")
        response = client.models.generate_content(
            model=model,
            contents="Say 'hello' in one word.",
        )

        reply = response.text.strip()
        print(f"Response: {reply}")
        print("=" * 60)
        print("SUCCESS: Google AI Studio API is reachable!")
        print(f"Model '{model}' is live and responding.")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"FAILED: {type(e).__name__}: {e}")
        print("-" * 60)
        sys.exit(1)


if __name__ == "__main__":
    verify_ai_connection()
