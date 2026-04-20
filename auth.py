"""
auth.py - User signup, login, simple password hashing
"""

import hashlib
from database import get_connection
from models import SignupRequest, LoginRequest, LoginResponse


def _hash_password(password: str) -> str:
    """SHA-256 hash (good enough for demo; use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def signup(req: SignupRequest) -> dict:
    if req.role not in ("teacher", "student"):
        return {"error": "Role must be 'teacher' or 'student'"}

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            (req.email.lower().strip(), _hash_password(req.password), req.role),
        )
        conn.commit()
        return {"message": "User created successfully"}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"error": "Email already registered"}
        return {"error": str(e)}
    finally:
        conn.close()


def login(req: LoginRequest) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, email, role FROM users WHERE email=? AND password=?",
            (req.email.lower().strip(), _hash_password(req.password)),
        ).fetchone()

        if not row:
            return {"error": "Invalid email or password"}

        return {"user_id": row["id"], "email": row["email"], "role": row["role"],
                "message": "Login successful"}
    finally:
        conn.close()
