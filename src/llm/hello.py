"""Tiny provider smoke test for the Week 7 assignment.

Set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL in .env, then run:
python -m src.llm.hello
"""

import os

import httpx
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    if os.getenv("LLM_STUB") == "1":
        print("ready")
        return

    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ["LLM_MODEL"]

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly the word: ready"}],
            "temperature": 0,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    print(response.json()["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
