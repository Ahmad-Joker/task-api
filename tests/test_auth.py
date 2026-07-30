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
    def __init__(self, fail_signup=False, fail_login=False, invalid_token=False):
        self.fail_signup = fail_signup
        self.fail_login = fail_login
        self.invalid_token = invalid_token
        self.signed_out = False

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

    def get_user(self, token):
        if self.invalid_token or token != "valid-token":
            raise RuntimeError("invalid token")
        return SimpleNamespace(user=fake_user())

    def sign_out(self):
        self.signed_out = True


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


def test_public_route_returns_200_without_auth():
    response = client.get("/public/info")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome stranger! This info is public."}


def test_protected_profile_without_header_returns_401():
    response = client.get("/protected/profile")

    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_protected_profile_with_malformed_header_returns_401():
    response = client.get("/protected/profile", headers={"Authorization": "Bearer"})

    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_protected_profile_with_wrong_scheme_returns_401():
    response = client.get("/protected/profile", headers={"Authorization": "Basic abc123"})

    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_protected_profile_with_invalid_token_returns_401():
    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_protected_profile_with_expired_or_rejected_token_returns_401(monkeypatch):
    monkeypatch.setattr(auth, "get_supabase", lambda: FakeSupabase(FakeAuth(invalid_token=True)))

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_protected_profile_with_valid_token_returns_profile_data():
    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-123",
        "email": "test@example.com",
        "created_at": "2026-07-30T00:00:00Z",
    }


def test_second_protected_route_uses_same_dependency():
    response = client.get(
        "/protected/dashboard",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to your dashboard",
        "user_id": "user-123",
    }


def test_dashboard_rejects_invalid_token():
    response = client.get(
        "/protected/dashboard",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_logout_without_token_returns_401():
    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_logout_with_invalid_token_returns_401():
    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_logout_with_valid_token_returns_204():
    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
