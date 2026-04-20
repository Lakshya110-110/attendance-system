"""
models.py - Pydantic request/response schemas
"""

from pydantic import BaseModel
from typing import Optional, List


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    password: str
    role: str  # 'teacher' | 'student'

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    email: str
    role: str
    message: str


# ── Student ───────────────────────────────────────────────────────────────────

class StudentRegisterRequest(BaseModel):
    user_id: int
    name: str
    roll_no: str
    face_embedding: Optional[List[float]] = None  # 128-dim vector

class StudentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    roll_no: str
    has_embedding: bool


# ── Subject ───────────────────────────────────────────────────────────────────

class SubjectCreateRequest(BaseModel):
    name: str
    code: str
    teacher_id: int

class EnrollRequest(BaseModel):
    student_id: int
    subject_id: int


# ── Session ───────────────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    teacher_id: int
    subject_id: int
    lat: float
    lon: float

class SessionResponse(BaseModel):
    session_id: str
    qr_base64: str
    subject_name: str
    started_at: str


# ── Attendance ────────────────────────────────────────────────────────────────

class MarkAttendanceRequest(BaseModel):
    session_id: str
    student_roll_no: str
    face_embedding: List[float]
    lat: float
    lon: float

class AttendanceResult(BaseModel):
    success: bool
    message: str
    face_score: Optional[float] = None
    distance_m: Optional[float] = None