import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


PROMPT_VERSION = "triage-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "prompts" / f"{PROMPT_VERSION}.md"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_messages(user_text: str, repair_instruction: str | None = None):
    messages = [
        {"role": "system", "content": load_prompt()},
        {"role": "user", "content": json.dumps({"text": user_text})},
    ]
    if repair_instruction is not None:
        messages.append({"role": "user", "content": repair_instruction})
    return messages


def complete_triage_raw(user_text: str, repair_instruction: str | None = None) -> str:
    load_dotenv()
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ["LLM_MODEL"]

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": build_messages(user_text, repair_instruction),
            "temperature": 0.2,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
