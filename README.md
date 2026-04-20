# 🎓 AttendAI — Smart Attendance System

Face Recognition + GPS Verification + QR Code Attendance

---

## 📁 Project Structure

```
smart_attendance/
├── backend/
│   ├── main.py          ← FastAPI app & all routes
│   ├── database.py      ← SQLite setup & connection
│   ├── models.py        ← Pydantic schemas
│   ├── auth.py          ← Signup / Login
│   ├── attendance.py    ← Business logic (sessions, GPS, face, reports)
│   ├── face_engine.py   ← Cosine similarity face matching
│   └── qr_service.py   ← QR code generation
├── frontend/
│   └── app.py           ← Streamlit UI
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API
```bash
cd backend
uvicorn main:app --reload --port 8000
```
The API docs are available at: http://localhost:8000/docs

### 3. Start the Frontend (new terminal)
```bash
cd frontend
streamlit run app.py
```
Open: http://localhost:8501

---

## 🧪 Demo Walkthrough

### As Teacher:
1. **Sign up** with role = `teacher`
2. Login → Teacher Dashboard
3. **Create a subject** (e.g. Machine Learning / CS501)
4. **Start Session** — pick subject, set GPS coordinates, click Start
5. A **QR code** and **Session ID** appear on screen

### As Student:
1. **Sign up** with role = `student`
2. Login → Student Dashboard
3. **Register Profile** (name + roll number + simulate face capture)
4. Ask teacher to **enroll you** (teacher uses Student ID shown after registration)
5. Go to **Mark Attendance** tab:
   - Paste the Session ID from teacher
   - Enter your roll number
   - Click **Scan Face** (uses same simulated seed → match succeeds)
   - Enter the same GPS coordinates as the teacher (or within 50 m)
   - Click **Mark Attendance** ✅

---

## 🔬 How Validation Works

| Check | Method | Threshold |
|-------|--------|-----------|
| Face match | Cosine similarity on 128-dim embedding | ≥ 0.80 |
| GPS proximity | Haversine formula | ≤ 50 metres |
| Duplicate | Unique constraint (session_id, student_id) | Prevented |
| Session timeout | UTC timestamp comparison | 120 minutes |

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/signup | Create account |
| POST | /auth/login | Login |
| POST | /students/register | Register student profile + face |
| GET  | /students/{roll_no} | Get student info |
| POST | /subjects | Create subject |
| GET  | /subjects | List subjects |
| POST | /subjects/enroll | Enroll student in subject |
| POST | /sessions/start | Start attendance session |
| POST | /sessions/{id}/stop | Stop session |
| GET  | /sessions/active | List active sessions |
| POST | /attendance/mark | Mark attendance |
| GET  | /reports/session/{id} | Session attendance list |
| GET  | /reports/student/{roll} | Student history |
| GET  | /reports/subject/{id}/summary | Subject summary |

---

## 🔐 Production Notes

- Replace SHA-256 password hashing with **bcrypt**
- Replace simulated embeddings with **DeepFace** or **face_recognition** library
- Add JWT tokens for stateless auth
- Use PostgreSQL instead of SQLite for concurrent access
- HTTPS + CORS whitelist for deployment

---

## 📦 Dependencies

- **FastAPI** — high-performance async API
- **SQLite** — zero-config embedded database
- **qrcode[pil]** — QR generation
- **Streamlit** — interactive UI
- **Pydantic v2** — request validation
