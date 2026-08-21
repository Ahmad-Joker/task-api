import json
import os
from pathlib import Path
import random
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from src.llm.schema import TriageOutput


PROMPT_VERSION = "triage-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "prompts" / f"{PROMPT_VERSION}.md"
QUARANTINE_PATH = PROJECT_ROOT / "logs" / "quarantine.jsonl"
COST_LOG_PATH = PROJECT_ROOT / "logs" / "llm-cost.jsonl"
MODEL_TIMEOUT_SECONDS = 30.0
MAX_ATTEMPTS = 3


class ModelOutputError(Exception):
    def __init__(self, message: str, raw_output: str, validation_error: str):
        super().__init__(message)
        self.raw_output = raw_output
        self.validation_error = validation_error


class ModelTimeoutError(Exception):
    pass


class ModelProviderError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


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


def retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def backoff_seconds(attempt_index: int, retry_after: str | None = None) -> float:
    retry_after_value = retry_after_seconds(retry_after)
    if retry_after_value is not None:
        return retry_after_value
    return (2 ** attempt_index) + random.uniform(0, 0.25)


def write_cost_log(
    model: str,
    usage: dict[str, Any],
    duration_ms: int,
    repair_count: int,
) -> None:
    COST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_line = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "duration_ms": duration_ms,
        "repair_count": repair_count,
    }
    with COST_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(log_line, ensure_ascii=False) + "\n")


def complete_triage_raw(user_text: str, repair_instruction: str | None = None) -> str:
    load_dotenv()
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ["LLM_MODEL"]
    payload = {
        "model": model,
        "messages": build_messages(user_text, repair_instruction),
        "temperature": 0.2,
    }

    for attempt in range(MAX_ATTEMPTS):
        started_at = time.monotonic()
        try:
            response = httpx.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=MODEL_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(backoff_seconds(attempt))
                continue
            raise ModelTimeoutError("Model request timed out") from exc

        duration_ms = int((time.monotonic() - started_at) * 1000)
        status_code = response.status_code
        if status_code == 200:
            data = response.json()
            write_cost_log(
                model=model,
                usage=data.get("usage", {}),
                duration_ms=duration_ms,
                repair_count=1 if repair_instruction else 0,
            )
            return data["choices"][0]["message"]["content"]

        if status_code == 429 or status_code >= 500:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(backoff_seconds(attempt, response.headers.get("Retry-After")))
                continue

        raise ModelProviderError(
            f"Model provider returned HTTP {status_code}",
            status_code=status_code,
        )

    raise ModelProviderError("Model provider failed after retries")


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
