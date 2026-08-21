from fastapi.testclient import TestClient

from main import app


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
