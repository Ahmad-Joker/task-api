import os
import re

from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

load_dotenv()

bearer_scheme = HTTPBearer(auto_error=False)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


class AuthConfigurationError(RuntimeError):
    pass


class AuthServiceError(RuntimeError):
    pass


class InvalidCredentialsError(RuntimeError):
    pass


class InvalidTokenError(RuntimeError):
    pass


def get_supabase_settings():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise AuthConfigurationError(
            "SUPABASE_URL and SUPABASE_KEY environment variables are required"
        )

    return supabase_url, supabase_key


def get_supabase_client():
    supabase_url, supabase_key = get_supabase_settings()
    return create_client(supabase_url, supabase_key)


def get_supabase():
    return get_supabase_client()


def validate_email(email):
    if not isinstance(email, str) or email.strip() == "":
        return None

    email = email.strip()
    if not EMAIL_PATTERN.match(email):
        return None

    return email


def validate_password(password):
    if not isinstance(password, str) or password == "":
        return None
    if len(password) < MIN_PASSWORD_LENGTH:
        return None
    return password


def safe_user_info(user):
    if user is None:
        return None

    return {
        "id": get_value(user, "id"),
        "email": get_value(user, "email"),
        "created_at": get_value(user, "created_at"),
    }


def get_value(source, key):
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)
