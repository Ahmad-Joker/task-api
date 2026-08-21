from fastapi.testclient import TestClient

import main
from main import app
from src.llm import client as llm_client
from src.llm.client import ModelOutputError


client = TestClient(app)


def test_triage_stub_returns_schema_valid_response(monkeypatch):
    monkeypatch.setenv("LLM_STUB", "1")

    response = client.post("/triage", json={"text": "I cannot log in after resetting my password."})

    assert response.status_code == 200
    assert response.json() == {
        "category": "other",
        "urgency": "normal",
        "suggested_team": "support",
        "confidence": 0.4,
        "reason": "Stub mode returns the safe unsure response.",
    }


def test_triage_missing_text_returns_400(monkeypatch):
    monkeypatch.setenv("LLM_STUB", "1")

    response = client.post("/triage", json={})

    assert response.status_code == 400
    assert response.json()["error"].startswith("text:")


def test_triage_wrong_text_type_returns_400(monkeypatch):
    monkeypatch.setenv("LLM_STUB", "1")

    response = client.post("/triage", json={"text": 123})

    assert response.status_code == 400
    assert response.json()["error"].startswith("text:")


def test_triage_text_too_long_returns_400(monkeypatch):
    monkeypatch.setenv("LLM_STUB", "1")

    response = client.post("/triage", json={"text": "x" * 2001})

    assert response.status_code == 400
    assert response.json()["error"].startswith("text:")


def test_fenced_model_json_is_parsed_and_validated():
    raw = """```json
    {"category":"bug","urgency":"high","suggested_team":"engineering","confidence":0.9,"reason":"The export button crashes."}
    ```"""

    parsed = llm_client.validate_model_output(raw)

    assert parsed.category == "bug"
    assert parsed.suggested_team == "engineering"


def test_model_output_gets_one_repair_retry(monkeypatch):
    calls = []

    def fake_complete_raw(user_text, repair_instruction=None):
        calls.append(repair_instruction)
        if repair_instruction is None:
            return '{"category":"made_up","urgency":"high","suggested_team":"engineering","confidence":0.9,"reason":"Bad category."}'
        return '{"category":"bug","urgency":"high","suggested_team":"engineering","confidence":0.9,"reason":"The user reports a product failure."}'

    monkeypatch.setattr(llm_client, "complete_triage_raw", fake_complete_raw)

    result = llm_client.complete_triage("The export button crashes.")

    assert result.category == "bug"
    assert len(calls) == 2
    assert calls[1] is not None


def test_failed_repair_is_quarantined(monkeypatch, tmp_path):
    quarantine_path = tmp_path / "quarantine.jsonl"
    monkeypatch.setattr(llm_client, "QUARANTINE_PATH", quarantine_path)
    monkeypatch.setattr(llm_client, "complete_triage_raw", lambda *_args, **_kwargs: "not json")

    try:
        llm_client.complete_triage("Please classify this.")
    except ModelOutputError:
        pass
    else:
        raise AssertionError("Expected ModelOutputError")

    log_text = quarantine_path.read_text(encoding="utf-8")
    assert "not json" in log_text
    assert "triage-v1" in log_text


def test_endpoint_returns_422_when_model_cannot_match_schema(monkeypatch):
    monkeypatch.delenv("LLM_STUB", raising=False)
    monkeypatch.setattr(
        main,
        "complete_triage",
        lambda _text: (_ for _ in ()).throw(
            ModelOutputError("Model response did not match the triage schema", "bad", "bad")
        ),
    )

    response = client.post("/triage", json={"text": "Please help"})

    assert response.status_code == 422
    assert response.json() == {"error": "Model response did not match the triage schema"}
