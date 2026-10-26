"""
auth.py — Secure authentication helpers.
Uses bcrypt for password hashing. Never stores plaintext passwords.
"""
import secrets
import hashlib
import bcrypt
from datetime import datetime, timezone
from typing import Optional, Tuple


def hash_password(plaintext: str) -> str:
    """Hash a password using bcrypt with a random salt. Returns the hash string."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate a cryptographically secure random session token."""
    return secrets.token_urlsafe(48)


def validate_email(email: str) -> Tuple[bool, str]:
    """Basic email format validation. Returns (is_valid, message)."""
    import re
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "Email is required."
    if not re.match(pattern, email):
        return False, "Please enter a valid email address."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Basic password strength validation."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    return True, ""


def normalize_email(email: str) -> str:
    """Normalize email to lowercase for consistent deduplication."""
    return email.strip().lower()


def utc_now_str() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()

