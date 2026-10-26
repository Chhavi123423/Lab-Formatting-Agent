"""
test_auth.py — Tests for authentication helpers (auth.py).
Never uses real user data or live database in unit tests.
"""
import pytest
from src.auth import (
    hash_password, verify_password, validate_email, validate_password,
    normalize_email, generate_session_token,
)


def test_password_hash_is_not_plaintext():
    pw = "MySecur3Pass!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert len(hashed) > 20


def test_password_verify_correct():
    pw = "CorrectHorseBattery9"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_password_verify_wrong():
    hashed = hash_password("rightpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_password_verify_empty():
    hashed = hash_password("something")
    assert verify_password("", hashed) is False


def test_two_hashes_are_different_salts():
    pw = "samepassword"
    h1 = hash_password(pw)
    h2 = hash_password(pw)
    assert h1 != h2  # Different salts each time


def test_validate_email_valid():
    ok, msg = validate_email("student@university.edu")
    assert ok is True
    assert msg == ""


def test_validate_email_missing_at():
    ok, msg = validate_email("studentuniversity.edu")
    assert ok is False
    assert "valid email" in msg.lower()


def test_validate_email_empty():
    ok, msg = validate_email("")
    assert ok is False


def test_validate_password_too_short():
    ok, msg = validate_password("abc")
    assert ok is False
    assert "8" in msg


def test_validate_password_ok():
    ok, msg = validate_password("12345678")
    assert ok is True


def test_normalize_email():
    assert normalize_email("  Student@UNIV.EDU  ") == "student@univ.edu"


def test_session_token_unique():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert t1 != t2
    assert len(t1) > 20

