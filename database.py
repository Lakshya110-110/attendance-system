"""
database.py - SQLite database setup and connection management
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")


def get_connection():
    """Return a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Users table (teachers and students)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('teacher','student')),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Students table (profile + face embedding)
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER UNIQUE REFERENCES users(id),
            name            TEXT NOT NULL,
            roll_no         TEXT UNIQUE NOT NULL,
            face_embedding  TEXT,           -- JSON-encoded float list
            registered_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Subjects
    c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            code        TEXT UNIQUE NOT NULL,
            teacher_id  INTEGER REFERENCES users(id),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Student ↔ Subject enrollment
    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER REFERENCES students(id),
            subject_id  INTEGER REFERENCES subjects(id),
            UNIQUE(student_id, subject_id)
        )
    """)

    # Attendance sessions (started by teacher)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,   -- UUID
            teacher_id  INTEGER REFERENCES users(id),
            subject_id  INTEGER REFERENCES subjects(id),
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            started_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at    DATETIME,
            is_active   INTEGER DEFAULT 1   -- 0 = stopped
        )
    """)

    # Attendance records
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT REFERENCES sessions(id),
            student_id  INTEGER REFERENCES students(id),
            face_score  REAL,
            distance_m  REAL,
            marked_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, student_id)  -- prevent duplicates
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialised.")
