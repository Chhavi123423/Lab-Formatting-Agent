"""
database.py — SQLite database layer for Lab Report Formatting Agent.
Handles user accounts and optional saved reports.
Uses parameterized queries throughout. Never stores plaintext passwords.

Schema:
  users           — account table
  saved_reports   — optional per-user saved report JSON blobs
  sessions        — server-side session tokens

Initialize by calling init_db() at application startup.
"""
import sqlite3
import json
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple

from src.auth import utc_now_str

# Database file location — at project root, gitignored
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "lab_reports.db"))


@contextmanager
def get_connection():
    """Context manager that yields a sqlite3 connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                email           TEXT    NOT NULL UNIQUE,
                password_hash   TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                updated_at      TEXT    NOT NULL,
                last_login_at   TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token           TEXT    PRIMARY KEY,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at      TEXT    NOT NULL,
                expires_at      TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS saved_reports (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title           TEXT    NOT NULL,
                document_data   TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                updated_at      TEXT    NOT NULL
            );
        """)


# ── User operations ──────────────────────────────────────────────────────────

def create_user(name: str, email: str, password_hash: str) -> Tuple[bool, str, Optional[int]]:
    """
    Insert a new user. Returns (success, message, user_id or None).
    Fails cleanly on duplicate email.
    """
    now = utc_now_str()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash, now, now)
            )
            return True, "Account created successfully.", cursor.lastrowid
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists.", None
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch a user record by email. Returns dict or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a user record by id. Returns dict or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_last_login(user_id: int):
    """Update last_login_at timestamp for a user."""
    now = utc_now_str()
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (now, now, user_id)
        )


# ── Session operations ────────────────────────────────────────────────────────

def create_session(token: str, user_id: int, expires_at: str):
    """Store a session token linked to a user."""
    now = utc_now_str()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, expires_at)
        )


def get_session(token: str) -> Optional[Dict[str, Any]]:
    """Return a session record if the token exists and has not expired."""
    from datetime import datetime, timezone
    now = utc_now_str()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE token = ? AND expires_at > ?",
            (token, now)
        ).fetchone()
        return dict(row) if row else None


def delete_session(token: str):
    """Remove a session (logout)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# ── Saved report operations ───────────────────────────────────────────────────

def save_report(user_id: int, title: str, document_data: dict) -> Tuple[bool, str, Optional[int]]:
    """Save or insert a report for a user. Returns (success, message, report_id)."""
    now = utc_now_str()
    data_json = json.dumps(document_data, ensure_ascii=False)
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO saved_reports (user_id, title, document_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, title.strip(), data_json, now, now)
            )
            return True, "Report saved.", cursor.lastrowid
    except Exception as e:
        return False, f"Failed to save report: {str(e)}", None


def update_report(report_id: int, user_id: int, title: str, document_data: dict) -> Tuple[bool, str]:
    """Update an existing report. Verifies ownership via user_id."""
    now = utc_now_str()
    data_json = json.dumps(document_data, ensure_ascii=False)
    try:
        with get_connection() as conn:
            result = conn.execute(
                "UPDATE saved_reports SET title = ?, document_data = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (title.strip(), data_json, now, report_id, user_id)
            )
            if result.rowcount == 0:
                return False, "Report not found or access denied."
            return True, "Report updated."
    except Exception as e:
        return False, f"Failed to update report: {str(e)}"


def get_user_reports(user_id: int) -> List[Dict[str, Any]]:
    """Fetch all saved reports for a user (metadata only, no document_data)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM saved_reports WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_report(report_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a full report by id, enforcing user ownership."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM saved_reports WHERE id = ? AND user_id = ?",
            (report_id, user_id)
        ).fetchone()
        if row:
            d = dict(row)
            d["document_data"] = json.loads(d["document_data"])
            return d
        return None


def delete_report(report_id: int, user_id: int) -> Tuple[bool, str]:
    """Delete a report, enforcing user ownership."""
    try:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM saved_reports WHERE id = ? AND user_id = ?",
                (report_id, user_id)
            )
            if result.rowcount == 0:
                return False, "Report not found or access denied."
            return True, "Report deleted."
    except Exception as e:
        return False, f"Failed to delete report: {str(e)}"

