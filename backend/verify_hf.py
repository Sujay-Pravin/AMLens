"""
Phase 0 — HuggingFace Connectivity Verification Script
Run this to confirm the HF InferenceClient can reach the chosen model.

Usage:
    python verify_hf.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def verify_hf_connection():
    """Verify HuggingFace Inference API connectivity with a simple chat completion."""
    token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

    if not token or token == "hf_your_token_here":
        print("=" * 60)
        print("ERROR: HF_TOKEN not set or still placeholder.")
        print("Please update your .env file with a valid HuggingFace token.")
        print("Get one at: https://huggingface.co/settings/tokens")
        print("=" * 60)
        sys.exit(1)

    print(f"Model:  {model}")
    print(f"Token:  {token[:8]}...{token[-4:]}")
    print("-" * 60)

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(model=model, token=token)

        print("Sending test chat completion...")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            max_tokens=10,
            temperature=0.1,
        )

        reply = response.choices[0].message.content
        print(f"Response: {reply}")
        print("=" * 60)
        print("SUCCESS: HuggingFace Inference API is reachable!")
        print(f"Model '{model}' is live and responding.")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"FAILED: {type(e).__name__}: {e}")
        print("-" * 60)
        print("Troubleshooting:")
        print("  1. Check your HF_TOKEN is valid")
        print("  2. Check the model is available on HF Inference API")
        print("  3. Try a backup model:")
        print("     - mistralai/Mistral-7B-Instruct-v0.3")
        print("     - microsoft/Phi-3-mini-4k-instruct")
        print("     - HuggingFaceH4/zephyr-7b-beta")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    verify_hf_connection()
