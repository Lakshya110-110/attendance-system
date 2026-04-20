"""
main.py - FastAPI application entry point
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from database import init_db
from models import (
    SignupRequest, LoginRequest,
    StudentRegisterRequest, SubjectCreateRequest, EnrollRequest,
    StartSessionRequest, MarkAttendanceRequest,
)
import auth
import attendance as att

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Attendance System API",
    description="Face + GPS + QR attendance verification",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/signup", tags=["Auth"])
def signup(req: SignupRequest):
    result = auth.signup(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/auth/login", tags=["Auth"])
def login(req: LoginRequest):
    result = auth.login(req)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


# ── Student routes ────────────────────────────────────────────────────────────

@app.post("/students/register", tags=["Students"])
def register_student(req: StudentRegisterRequest):
    result = att.register_student(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/students/{roll_no}", tags=["Students"])
def get_student(roll_no: str):
    s = att.get_student_by_roll(roll_no)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    s.pop("face_embedding", None)   # don't expose raw embedding
    return s


@app.post("/students/update-embedding", tags=["Students"])
def update_embedding(roll_no: str, embedding: list):
    result = att.update_face_embedding(roll_no, embedding)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Subject routes ────────────────────────────────────────────────────────────

@app.post("/subjects", tags=["Subjects"])
def create_subject(req: SubjectCreateRequest):
    result = att.create_subject(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/subjects", tags=["Subjects"])
def list_subjects(teacher_id: Optional[int] = None):
    return att.list_subjects(teacher_id)


@app.post("/subjects/enroll", tags=["Subjects"])
def enroll(req: EnrollRequest):
    result = att.enroll_student(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/subjects/{subject_id}/students", tags=["Subjects"])
def enrolled_students(subject_id: int):
    return att.list_enrolled_students(subject_id)


# ── Session routes ────────────────────────────────────────────────────────────

@app.post("/sessions/start", tags=["Sessions"])
def start_session(req: StartSessionRequest):
    result = att.start_session(req)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/sessions/{session_id}/stop", tags=["Sessions"])
def stop_session(session_id: str, teacher_id: int):
    result = att.stop_session(session_id, teacher_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/sessions/active", tags=["Sessions"])
def active_sessions(teacher_id: int):
    return att.get_active_sessions(teacher_id)


@app.get("/sessions/{session_id}", tags=["Sessions"])
def get_session(session_id: str):
    s = att.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


# ── Attendance routes ─────────────────────────────────────────────────────────

@app.post("/attendance/mark", tags=["Attendance"])
def mark_attendance(req: MarkAttendanceRequest):
    return att.mark_attendance(req)


# ── Report routes ─────────────────────────────────────────────────────────────

@app.get("/reports/session/{session_id}", tags=["Reports"])
def session_report(session_id: str):
    return att.session_attendance_report(session_id)


@app.get("/reports/student/{roll_no}", tags=["Reports"])
def student_report(roll_no: str):
    return att.student_attendance_report(roll_no)


@app.get("/reports/subject/{subject_id}/summary", tags=["Reports"])
def subject_summary(subject_id: int):
    return att.subject_summary_report(subject_id)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "Smart Attendance API"}
