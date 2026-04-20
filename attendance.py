"""
attendance.py - Session management, attendance marking, GPS validation, reports
"""

import uuid
import json
import math
from datetime import datetime, timedelta
from typing import Optional, List

from database import get_connection
from models import (
    StartSessionRequest, MarkAttendanceRequest,
    EnrollRequest, SubjectCreateRequest, StudentRegisterRequest
)
from face_engine import verify_face, embedding_to_str, generate_embedding
from qr_service import generate_qr

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_DISTANCE_METERS = 50        # GPS proximity limit
SESSION_TIMEOUT_MINUTES = 120   # Auto-expire after 2 hours


# ── Haversine distance ────────────────────────────────────────────────────────

def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    """Return distance in metres between two GPS coordinates."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ── Student registration ──────────────────────────────────────────────────────

def register_student(req: StudentRegisterRequest) -> dict:
    conn = get_connection()
    try:
        # Generate a deterministic embedding if none supplied
        embedding = req.face_embedding if req.face_embedding else generate_embedding(seed=req.user_id)
        emb_str = embedding_to_str(embedding)

        conn.execute(
            "INSERT INTO students (user_id, name, roll_no, face_embedding) VALUES (?,?,?,?)",
            (req.user_id, req.name, req.roll_no, emb_str),
        )
        conn.commit()
        return {"message": f"Student '{req.name}' registered successfully"}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"error": "Roll number or user already registered"}
        return {"error": str(e)}
    finally:
        conn.close()


def get_student_by_roll(roll_no: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM students WHERE roll_no=?", (roll_no,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_face_embedding(roll_no: str, embedding: list) -> dict:
    """Allow a student to update their face embedding."""
    conn = get_connection()
    try:
        emb_str = embedding_to_str(embedding)
        result = conn.execute(
            "UPDATE students SET face_embedding=? WHERE roll_no=?", (emb_str, roll_no)
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Student not found"}
        return {"message": "Face embedding updated"}
    finally:
        conn.close()


# ── Subject management ────────────────────────────────────────────────────────

def create_subject(req: SubjectCreateRequest) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO subjects (name, code, teacher_id) VALUES (?,?,?)",
            (req.name, req.code, req.teacher_id),
        )
        conn.commit()
        return {"message": f"Subject '{req.name}' created"}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"error": "Subject code already exists"}
        return {"error": str(e)}
    finally:
        conn.close()


def list_subjects(teacher_id: Optional[int] = None) -> list:
    conn = get_connection()
    try:
        if teacher_id:
            rows = conn.execute(
                "SELECT * FROM subjects WHERE teacher_id=?", (teacher_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM subjects").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def enroll_student(req: EnrollRequest) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO enrollments (student_id, subject_id) VALUES (?,?)",
            (req.student_id, req.subject_id),
        )
        conn.commit()
        return {"message": "Student enrolled"}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"error": "Already enrolled"}
        return {"error": str(e)}
    finally:
        conn.close()


def list_enrolled_students(subject_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.name, s.roll_no
            FROM students s
            JOIN enrollments e ON e.student_id = s.id
            WHERE e.subject_id = ?
        """, (subject_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Session management ────────────────────────────────────────────────────────

def start_session(req: StartSessionRequest) -> dict:
    conn = get_connection()
    try:
        # Check subject belongs to teacher
        subject = conn.execute(
            "SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (req.subject_id, req.teacher_id),
        ).fetchone()
        if not subject:
            return {"error": "Subject not found or not yours"}

        session_id = str(uuid.uuid4())
        qr_b64 = generate_qr(session_id)

        conn.execute(
            "INSERT INTO sessions (id, teacher_id, subject_id, lat, lon) VALUES (?,?,?,?,?)",
            (session_id, req.teacher_id, req.subject_id, req.lat, req.lon),
        )
        conn.commit()

        return {
            "session_id": session_id,
            "qr_base64": qr_b64,
            "subject_name": subject["name"],
            "started_at": datetime.utcnow().isoformat(),
        }
    finally:
        conn.close()


def stop_session(session_id: str, teacher_id: int) -> dict:
    conn = get_connection()
    try:
        result = conn.execute(
            "UPDATE sessions SET is_active=0, ended_at=CURRENT_TIMESTAMP WHERE id=? AND teacher_id=?",
            (session_id, teacher_id),
        )
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Session not found or not yours"}
        return {"message": "Session stopped"}
    finally:
        conn.close()


def get_active_sessions(teacher_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.started_at, sub.name as subject_name, s.lat, s.lon
            FROM sessions s JOIN subjects sub ON sub.id = s.subject_id
            WHERE s.teacher_id=? AND s.is_active=1
        """, (teacher_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Attendance marking ────────────────────────────────────────────────────────

def mark_attendance(req: MarkAttendanceRequest) -> dict:
    conn = get_connection()
    try:
        # 1. Fetch session
        session = conn.execute(
            "SELECT * FROM sessions WHERE id=?", (req.session_id,)
        ).fetchone()
        if not session:
            return {"success": False, "message": "Session not found"}
        if not session["is_active"]:
            return {"success": False, "message": "Session is no longer active"}

        # 2. Session timeout check
        started = datetime.fromisoformat(session["started_at"])
        if datetime.utcnow() - started > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            conn.execute("UPDATE sessions SET is_active=0 WHERE id=?", (req.session_id,))
            conn.commit()
            return {"success": False, "message": "Session has timed out"}

        # 3. Fetch student
        student = conn.execute(
            "SELECT * FROM students WHERE roll_no=?", (req.student_roll_no,)
        ).fetchone()
        if not student:
            return {"success": False, "message": "Student not found — please register first"}

        # 4. Check enrollment
        enrolled = conn.execute(
            "SELECT 1 FROM enrollments WHERE student_id=? AND subject_id=?",
            (student["id"], session["subject_id"]),
        ).fetchone()
        if not enrolled:
            return {"success": False, "message": "Student not enrolled in this subject"}

        # 5. Duplicate attendance check
        already = conn.execute(
            "SELECT 1 FROM attendance WHERE session_id=? AND student_id=?",
            (req.session_id, student["id"]),
        ).fetchone()
        if already:
            return {"success": False, "message": "Attendance already marked for this session"}

        # 6. GPS validation
        distance = haversine_meters(session["lat"], session["lon"], req.lat, req.lon)
        if distance > MAX_DISTANCE_METERS:
            return {
                "success": False,
                "message": f"Too far from class ({distance:.1f} m). Must be within {MAX_DISTANCE_METERS} m",
                "distance_m": round(distance, 1),
            }

        # 7. Face verification
        if not student["face_embedding"]:
            return {"success": False, "message": "No face embedding registered for this student"}

        face_result = verify_face(student["face_embedding"], req.face_embedding)
        face_score = face_result["score"]
        if not face_result["match"]:
            return {
                "success": False,
                "message": f"Face not recognised (score {face_score}). Please look at the camera clearly",
                "face_score": face_score,
            }

        # 8. Mark attendance ✓
        conn.execute(
            "INSERT INTO attendance (session_id, student_id, face_score, distance_m) VALUES (?,?,?,?)",
            (req.session_id, student["id"], face_score, round(distance, 1)),
        )
        conn.commit()

        return {
            "success": True,
            "message": f"✅ Attendance marked for {student['name']}",
            "face_score": face_score,
            "distance_m": round(distance, 1),
        }
    except Exception as e:
        return {"success": False, "message": f"Server error: {str(e)}"}
    finally:
        conn.close()


# ── Reports ───────────────────────────────────────────────────────────────────

def session_attendance_report(session_id: str) -> list:
    """All attendance records for a single session."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT s.name, s.roll_no, a.face_score, a.distance_m, a.marked_at
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE a.session_id = ?
            ORDER BY a.marked_at
        """, (session_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def student_attendance_report(roll_no: str) -> list:
    """All attendance records for a student across all sessions."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT sub.name as subject, ses.started_at as session_date,
                   a.face_score, a.distance_m, a.marked_at
            FROM attendance a
            JOIN sessions ses ON ses.id = a.session_id
            JOIN subjects sub ON sub.id = ses.subject_id
            JOIN students st ON st.id = a.student_id
            WHERE st.roll_no = ?
            ORDER BY a.marked_at DESC
        """, (roll_no,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def subject_summary_report(subject_id: int) -> list:
    """Attendance percentage per student for a subject."""
    conn = get_connection()
    try:
        total_sessions = conn.execute(
            "SELECT COUNT(*) as cnt FROM sessions WHERE subject_id=?", (subject_id,)
        ).fetchone()["cnt"]

        rows = conn.execute("""
            SELECT st.name, st.roll_no,
                   COUNT(a.id) as attended,
                   ? as total_sessions
            FROM students st
            JOIN enrollments e ON e.student_id = st.id
            LEFT JOIN attendance a ON a.student_id = st.id
                AND a.session_id IN (SELECT id FROM sessions WHERE subject_id=?)
            WHERE e.subject_id = ?
            GROUP BY st.id
        """, (total_sessions, subject_id, subject_id)).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            d["percentage"] = round((d["attended"] / total_sessions * 100) if total_sessions else 0, 1)
            result.append(d)
        return result
    finally:
        conn.close()
