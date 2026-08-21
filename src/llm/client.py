import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from src.llm.schema import TriageOutput


PROMPT_VERSION = "triage-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "prompts" / f"{PROMPT_VERSION}.md"
QUARANTINE_PATH = PROJECT_ROOT / "logs" / "quarantine.jsonl"


class ModelOutputError(Exception):
    def __init__(self, message: str, raw_output: str, validation_error: str):
        super().__init__(message)
        self.raw_output = raw_output
        self.validation_error = validation_error


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


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model output did not contain a JSON object")
    return text[start : end + 1]


def validate_model_output(raw_text: str) -> TriageOutput:
    json_text = extract_json_object(raw_text)
    return TriageOutput.model_validate_json(json_text)


def build_repair_instruction(raw_output: str, validation_error: str) -> str:
    return (
        "Your previous answer was rejected for this reason. "
        "Return only corrected JSON matching the schema.\n"
        f"Validation error: {validation_error}\n"
        f"Rejected output: {raw_output}"
    )


def quarantine_failure(user_text: str, raw_output: str, validation_error: str) -> None:
    QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_line: dict[str, Any] = {
        "prompt_version": PROMPT_VERSION,
        "input": {"text": user_text},
        "raw_model_output": raw_output,
        "error": validation_error,
    }
    with QUARANTINE_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(log_line, ensure_ascii=False) + "\n")


def complete_triage(user_text: str) -> TriageOutput:
    raw_output = complete_triage_raw(user_text)
    try:
        return validate_model_output(raw_output)
    except (ValidationError, ValueError) as exc:
        first_error = str(exc)

    repair_output = complete_triage_raw(
        user_text,
        repair_instruction=build_repair_instruction(raw_output, first_error),
    )
    try:
        return validate_model_output(repair_output)
    except (ValidationError, ValueError) as exc:
        final_error = str(exc)
        quarantine_failure(user_text, repair_output, final_error)
        raise ModelOutputError(
            "Model response did not match the triage schema",
            repair_output,
            final_error,
        ) from exc
