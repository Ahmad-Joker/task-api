import os
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks_test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

from fastapi.testclient import TestClient
import pytest

import auth
from main import app


client = TestClient(app)


def fake_user():
    return SimpleNamespace(
        id="user-123",
        email="test@example.com",
        created_at="2026-07-30T00:00:00Z",
    )


def fake_session():
    return SimpleNamespace(
        access_token="access-token",
        refresh_token="refresh-token",
    )


class FakeAuth:
    def __init__(self, fail_signup=False, fail_login=False):
        self.fail_signup = fail_signup
        self.fail_login = fail_login

    def sign_up(self, payload):
        if self.fail_signup:
            raise RuntimeError("supabase rejected signup")
        assert payload == {"email": "test@example.com", "password": "password123"}
        return SimpleNamespace(user=fake_user())

    def sign_in_with_password(self, payload):
        if self.fail_login:
            raise RuntimeError("invalid credentials")
        assert payload == {"email": "test@example.com", "password": "password123"}
        return SimpleNamespace(user=fake_user(), session=fake_session())


class FakeSupabase:
    def __init__(self, fake_auth):
        self.auth = fake_auth


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    monkeypatch.setattr(auth, "get_supabase", lambda: FakeSupabase(FakeAuth()))


def test_signup_success():
    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "user": {
            "id": "user-123",
            "email": "test@example.com",
            "created_at": "2026-07-30T00:00:00Z",
        }
    }


def test_signup_missing_email():
    response = client.post("/auth/signup", json={"password": "password123"})

    assert response.status_code == 400
    assert response.json() == {"error": "Email is required"}


def test_signup_missing_password():
    response = client.post("/auth/signup", json={"email": "test@example.com"})

    assert response.status_code == 400
    assert response.json() == {"error": "Password is required"}


def test_signup_invalid_email():
    response = client.post(
        "/auth/signup",
        json={"email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Valid email is required"}


def test_signup_empty_password():
    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": ""},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Password must be at least 8 characters"}


def test_signup_supabase_error(monkeypatch):
    monkeypatch.setattr(auth, "get_supabase", lambda: FakeSupabase(FakeAuth(fail_signup=True)))

    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Could not sign up user"}


def test_login_success():
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "user": {
            "id": "user-123",
            "email": "test@example.com",
            "created_at": "2026-07-30T00:00:00Z",
        },
    }


def test_login_missing_fields():
    response = client.post("/auth/login", json={})

    assert response.status_code == 400
    assert response.json() == {"error": "Email is required"}


def test_login_invalid_credentials(monkeypatch):
    monkeypatch.setattr(auth, "get_supabase", lambda: FakeSupabase(FakeAuth(fail_login=True)))

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid login credentials"}
