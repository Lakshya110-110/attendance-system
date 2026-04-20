"""
app.py - Smart Attendance System — Streamlit Frontend
Redesigned: Dark glassmorphism + animated neon-accent control-room aesthetic
Run: streamlit run app.py
"""

import streamlit as st
import requests
import base64
import random
import math
from datetime import datetime

API_BASE = "http://localhost:8000"
EMBEDDING_DIM = 128

st.set_page_config(page_title="AttendAI", page_icon="🎓", layout="wide",
                   initial_sidebar_state="collapsed")

# ── Helpers ───────────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    try:
        r = getattr(requests, method)(f"{API_BASE}{path}", timeout=10, **kwargs)
        if r.status_code >= 400:
            st.error(f"⚠ {r.json().get('detail', r.text)}")
            return None
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠ Backend offline — run: `uvicorn main:app --reload --port 8000`")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def fake_embedding(seed=None):
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(EMBEDDING_DIM)]
    mag = math.sqrt(sum(x * x for x in vec))
    return [x / mag for x in vec] if mag else vec

for k, v in {"user": None, "active_session": None, "active_session_qr": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --bg:        #020b18;
    --bg2:       #061220;
    --cyan:      #00f5ff;
    --cyan-dim:  #00a8b5;
    --green:     #00ff88;
    --green-dim: #00b35f;
    --amber:     #ffb300;
    --red:       #ff3860;
    --purple:    #bd00ff;
    --glass:     rgba(0,245,255,0.04);
    --border:    rgba(0,245,255,0.18);
    --border2:   rgba(0,245,255,0.38);
    --text:      #c8e6f0;
    --text-dim:  #5a8a9f;
}

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
header[data-testid="stHeader"] { display:none !important; }
#MainMenu, footer, .stDeployButton { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; }

.stApp::before {
    content:'';
    position:fixed;
    inset:0;
    background-image:
        linear-gradient(rgba(0,245,255,0.025) 1px,transparent 1px),
        linear-gradient(90deg,rgba(0,245,255,0.025) 1px,transparent 1px);
    background-size:44px 44px;
    pointer-events:none;
    z-index:0;
}

::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--cyan-dim); border-radius:2px; }

/* NAV */
.top-nav {
    display:flex; align-items:center; justify-content:space-between;
    padding:1rem 2.5rem;
    background:linear-gradient(135deg,rgba(0,20,40,0.97),rgba(0,10,25,0.99));
    border-bottom:1px solid var(--border2);
    box-shadow:0 0 40px rgba(0,245,255,0.08);
    position:relative; z-index:100;
}
.top-nav::after {
    content:''; position:absolute; bottom:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg,transparent,var(--cyan),var(--purple),transparent);
    animation:scanline 3s linear infinite;
}
@keyframes scanline { 0%,100%{opacity:.3} 50%{opacity:1} }

.nav-logo {
    font-family:'Orbitron',monospace; font-size:1.5rem; font-weight:900;
    color:var(--cyan); text-shadow:0 0 20px var(--cyan),0 0 40px rgba(0,245,255,.3);
    letter-spacing:.1em;
}
.nav-logo span { color:#fff; }
.nav-right { display:flex; align-items:center; gap:1.5rem; }
.nav-user { font-family:'Share Tech Mono',monospace; font-size:.75rem; color:var(--cyan-dim); }
.nav-role {
    font-family:'Orbitron',monospace; font-size:.6rem; padding:3px 10px;
    border:1px solid var(--cyan); color:var(--cyan); border-radius:2px;
    letter-spacing:.15em; text-transform:uppercase;
    box-shadow:0 0 10px rgba(0,245,255,.2),inset 0 0 10px rgba(0,245,255,.05);
    animation:pulse-b 2s ease-in-out infinite;
}
@keyframes pulse-b {
    0%,100%{box-shadow:0 0 10px rgba(0,245,255,.2)} 50%{box-shadow:0 0 20px rgba(0,245,255,.5)}
}

/* CARDS */
.glass-card {
    background:var(--glass); border:1px solid var(--border); border-radius:4px;
    padding:1.5rem; margin-bottom:1rem; position:relative;
    transition:border-color .3s,box-shadow .3s;
}
.glass-card:hover { border-color:var(--border2); box-shadow:0 0 20px rgba(0,245,255,.06); }
.glass-card::before {
    content:''; position:absolute; top:0; left:1.5rem; right:1.5rem; height:1px;
    background:linear-gradient(90deg,transparent,rgba(0,245,255,.25),transparent);
}

/* SECTION HEADERS */
.sec-hdr {
    font-family:'Orbitron',monospace; font-size:.62rem; font-weight:700;
    letter-spacing:.28em; text-transform:uppercase; color:var(--cyan-dim);
    margin-bottom:1rem; padding-bottom:.5rem;
    border-bottom:1px solid var(--border);
    display:flex; align-items:center; gap:.6rem;
}
.sec-hdr::before { content:'//'; color:var(--cyan); opacity:.6; }

/* BADGES */
.badge {
    font-family:'Share Tech Mono',monospace; font-size:.65rem; padding:2px 10px;
    border-radius:2px; letter-spacing:.1em; text-transform:uppercase; border:1px solid;
    display:inline-block;
}
.badge-live   { color:var(--green);  border-color:var(--green-dim); background:rgba(0,255,136,.07); box-shadow:0 0 8px rgba(0,255,136,.2); }
.badge-closed { color:var(--red);    border-color:var(--red);       background:rgba(255,56,96,.07); }
.badge-info   { color:var(--cyan);   border-color:var(--cyan-dim);  background:rgba(0,245,255,.07); }
.badge-warn   { color:var(--amber);  border-color:var(--amber);     background:rgba(255,179,0,.07); }

/* SESSION ID */
.session-id {
    font-family:'Share Tech Mono',monospace; font-size:.78rem; color:var(--green);
    background:rgba(0,255,136,.04); border:1px solid rgba(0,255,136,.18);
    border-radius:3px; padding:.7rem 1rem; word-break:break-all;
    letter-spacing:.04em; text-shadow:0 0 8px rgba(0,255,136,.35);
    margin:.5rem 0;
}

/* STEP INDICATOR */
.step-indicator { display:flex; align-items:center; gap:.8rem; margin:1.2rem 0 .5rem; }
.step-num {
    width:28px; height:28px; border:1px solid var(--cyan); border-radius:2px;
    display:flex; align-items:center; justify-content:center;
    font-family:'Orbitron',monospace; font-size:.62rem; font-weight:700;
    color:var(--cyan); background:rgba(0,245,255,.07); flex-shrink:0;
    box-shadow:0 0 8px rgba(0,245,255,.2);
}
.step-label {
    font-family:'Rajdhani',sans-serif; font-size:.8rem; font-weight:600;
    color:var(--text-dim); letter-spacing:.12em; text-transform:uppercase;
}

/* METRICS */
.metric-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:1rem; margin:1rem 0; }
.metric-panel {
    background:var(--glass); border:1px solid var(--border); border-radius:3px;
    padding:1.2rem 1rem; text-align:center; position:relative; overflow:hidden;
}
.metric-panel::after { content:''; position:absolute; bottom:0; left:0; right:0; height:2px; background:var(--cyan); opacity:.35; }
.metric-val { font-family:'Orbitron',monospace; font-size:2rem; font-weight:900; line-height:1; text-shadow:0 0 15px currentColor; }
.metric-lbl { font-family:'Share Tech Mono',monospace; font-size:.6rem; letter-spacing:.2em; text-transform:uppercase; color:var(--text-dim); margin-top:.4rem; }

/* TABLE */
.att-table { width:100%; border-collapse:collapse; font-family:'Rajdhani',sans-serif; font-size:.88rem; }
.att-table thead th {
    font-family:'Orbitron',monospace; font-size:.55rem; font-weight:700; letter-spacing:.25em;
    text-transform:uppercase; color:var(--cyan-dim); padding:.7rem 1rem;
    border-bottom:1px solid var(--border2); text-align:left; background:rgba(0,245,255,.03);
}
.att-table tbody td { padding:.6rem 1rem; border-bottom:1px solid rgba(0,245,255,.06); color:var(--text); }
.att-table tbody tr:hover td { background:rgba(0,245,255,.035); }
.roll-code { font-family:'Share Tech Mono',monospace; font-size:.78rem; color:var(--cyan-dim); }

/* BAR */
.att-bar-bg { background:rgba(0,245,255,.1); border-radius:2px; height:5px; overflow:hidden; margin-top:5px; }
.att-bar-fill { height:100%; border-radius:2px; background:linear-gradient(90deg,var(--cyan),var(--green)); }

/* ONLINE DOT */
.online-dot {
    width:7px; height:7px; background:var(--green); border-radius:50%;
    display:inline-block; box-shadow:0 0 7px var(--green);
    animation:blink 1.5s ease-in-out infinite; margin-right:5px;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.25} }

/* QR */
.qr-wrapper { background:#fff; border-radius:4px; padding:10px; display:inline-block; box-shadow:0 0 30px rgba(0,245,255,.2); border:2px solid var(--cyan-dim); }

/* PAGE HEADER */
.page-header { padding:1.8rem 0 1.2rem; }
.page-title { font-family:'Orbitron',monospace; font-size:1.7rem; font-weight:900; color:#fff; letter-spacing:.05em; line-height:1; text-shadow:0 0 20px rgba(0,245,255,.3); }
.page-title span { color:var(--cyan); }
.page-title-sub { font-family:'Share Tech Mono',monospace; font-size:.68rem; color:var(--text-dim); letter-spacing:.15em; text-transform:uppercase; margin-top:.4rem; }
.cyber-div { height:1px; background:linear-gradient(90deg,transparent,var(--border2),transparent); margin:1.5rem 0; }

/* STREAMLIT OVERRIDES */
.stTextInput>div>div>input,
.stNumberInput>div>div>input {
    background:rgba(0,20,40,.85) !important; border:1px solid var(--border) !important;
    border-radius:3px !important; color:var(--text) !important;
    font-family:'Rajdhani',sans-serif !important; font-size:.95rem !important;
    transition:border-color .2s,box-shadow .2s !important;
}
.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus {
    border-color:var(--cyan-dim) !important; box-shadow:0 0 12px rgba(0,245,255,.15) !important;
}
.stSelectbox>div>div { background:rgba(0,20,40,.85) !important; border:1px solid var(--border) !important; border-radius:3px !important; }
.stSelectbox>div>div>div { color:var(--text) !important; font-family:'Rajdhani',sans-serif !important; }

.stTextInput label,.stNumberInput label,.stSelectbox label,
.stRadio label,[data-testid="stWidgetLabel"] {
    font-family:'Rajdhani',sans-serif !important; font-size:.76rem !important;
    font-weight:600 !important; letter-spacing:.12em !important;
    text-transform:uppercase !important; color:var(--text-dim) !important;
}

.stTabs [data-baseweb="tab-list"] { background:transparent !important; border-bottom:1px solid var(--border) !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] {
    font-family:'Orbitron',monospace !important; font-size:.58rem !important;
    font-weight:600 !important; letter-spacing:.15em !important;
    color:var(--text-dim) !important; background:transparent !important;
    border:none !important; padding:.8rem 1.2rem !important;
    border-bottom:2px solid transparent !important; transition:all .2s !important;
}
.stTabs [aria-selected="true"] { color:var(--cyan) !important; border-bottom:2px solid var(--cyan) !important; background:rgba(0,245,255,.04) !important; }
.stTabs [data-baseweb="tab-panel"] { background:transparent !important; padding:1.5rem 0 !important; }

.stButton>button {
    font-family:'Orbitron',monospace !important; font-size:.62rem !important;
    font-weight:700 !important; letter-spacing:.18em !important; text-transform:uppercase !important;
    background:transparent !important; color:var(--cyan) !important;
    border:1px solid var(--cyan-dim) !important; border-radius:3px !important;
    padding:.65rem 1.5rem !important; transition:all .2s !important;
}
.stButton>button:hover {
    background:rgba(0,245,255,.1) !important; border-color:var(--cyan) !important;
    box-shadow:0 0 20px rgba(0,245,255,.2) !important; transform:translateY(-1px) !important;
}
.stButton>button:active { transform:translateY(0) !important; }

div[data-testid="stNotification"] { border-radius:3px !important; }

.stRadio>div { gap:.4rem !important; }
.stRadio>div>label {
    background:var(--glass) !important; border:1px solid var(--border) !important;
    border-radius:3px !important; padding:4px 14px !important;
    cursor:pointer !important; transition:all .2s !important;
    text-transform:none !important; letter-spacing:0 !important; font-size:.85rem !important;
}
.stRadio>div>label:hover { border-color:var(--cyan-dim) !important; }

/* Login specific */
.login-outer { display:flex; flex-direction:column; align-items:center; padding-top:4vh; }
.login-box {
    width:100%; max-width:430px;
    background:linear-gradient(135deg,rgba(0,30,60,.85),rgba(0,10,25,.92));
    border:1px solid var(--border2); border-radius:4px; padding:2.8rem 2.5rem;
    box-shadow:0 0 60px rgba(0,245,255,.1),0 0 120px rgba(0,245,255,.04);
    position:relative; overflow:hidden;
}
.login-box::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--cyan),var(--purple),var(--cyan),transparent);
}
.login-title { font-family:'Orbitron',monospace; font-size:2.2rem; font-weight:900; text-align:center; color:#fff; text-shadow:0 0 30px var(--cyan); letter-spacing:.05em; margin-bottom:.3rem; }
.login-title span { color:var(--cyan); }
.login-sub { text-align:center; color:var(--text-dim); font-size:.72rem; letter-spacing:.2em; text-transform:uppercase; margin-bottom:2rem; font-family:'Share Tech Mono',monospace; }

/* Orbs */
.orb { position:fixed; border-radius:50%; filter:blur(80px); opacity:.1; pointer-events:none; animation:float 8s ease-in-out infinite; z-index:-1; }
.orb1 { width:400px; height:400px; background:var(--cyan); top:-100px; left:-100px; }
.orb2 { width:300px; height:300px; background:var(--purple); bottom:-50px; right:-50px; animation-delay:3s; }
@keyframes float { 0%,100%{transform:translateY(0) scale(1)} 50%{transform:translateY(-20px) scale(1.04)} }
</style>
""", unsafe_allow_html=True)


# ── NAV ───────────────────────────────────────────────────────────────────────
def render_nav():
    u = st.session_state.user
    st.markdown(f"""
    <div class="top-nav">
      <div class="nav-logo">ATTEND<span>AI</span></div>
      <div class="nav-right">
        <span class="nav-user">⬡ {u['email']}</span>
        <span class="nav-role">{u['role'].upper()}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def page_login():
    st.markdown('<div class="orb orb1"></div><div class="orb orb2"></div>', unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div class="login-box">
          <div class="login-title">ATTEND<span>AI</span></div>
          <div class="login-sub">[ Face · GPS · QR Attendance ]</div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["LOGIN", "CREATE ACCOUNT"])
        with tab1:
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="operator@university.edu", key="li_email")
            pwd   = st.text_input("Password", type="password", placeholder="••••••••", key="li_pwd")
            st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)
            if st.button("⟶  AUTHENTICATE", use_container_width=True, key="btn_login"):
                if email and pwd:
                    with st.spinner("Verifying..."):
                        r = api("post", "/auth/login", json={"email": email, "password": pwd})
                    if r:
                        st.session_state.user = r
                        st.rerun()
                else:
                    st.warning("Enter email and password")

        with tab2:
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
            su_e = st.text_input("Email", key="su_email")
            su_p = st.text_input("Password", type="password", key="su_pwd")
            su_r = st.selectbox("Role", ["student", "teacher"], key="su_role",
                                format_func=lambda x: "👩‍🏫 Teacher" if x == "teacher" else "👨‍🎓 Student")
            st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)
            if st.button("⟶  REGISTER", use_container_width=True, key="btn_signup"):
                if su_e and su_p:
                    with st.spinner("Creating account..."):
                        r = api("post", "/auth/signup", json={"email": su_e, "password": su_p, "role": su_r})
                    if r:
                        st.success("✓ Account created — switch to Login")
                else:
                    st.warning("All fields required")


# ── TEACHER ───────────────────────────────────────────────────────────────────
def teacher_dashboard():
    render_nav()
    uid = st.session_state.user["user_id"]
    st.markdown('<div class="page-header"><div class="page-title">CONTROL <span>PANEL</span></div><div class="page-title-sub">Teacher Operations Center</div></div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["SESSION HUB", "SUBJECTS", "REPORTS", "ACCOUNT"])

    # SESSION HUB
    with t1:
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown('<div class="sec-hdr">LAUNCH SESSION</div>', unsafe_allow_html=True)
            subjects = api("get", f"/subjects?teacher_id={uid}") or []
            if not subjects:
                st.markdown('<div class="glass-card" style="text-align:center;padding:2.5rem;color:var(--text-dim)"><div style="font-size:2.5rem;margin-bottom:.5rem">📡</div><div style="font-family:Orbitron,monospace;font-size:.7rem;letter-spacing:.2em">NO SUBJECTS FOUND</div><div style="margin-top:.4rem;font-size:.85rem">Go to SUBJECTS tab first</div></div>', unsafe_allow_html=True)
            else:
                subj_map = {s["name"]: s["id"] for s in subjects}
                chosen = st.selectbox("Select Subject", list(subj_map.keys()))
                st.markdown('<div class="sec-hdr">GPS COORDINATES</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1: lat = st.number_input("Latitude",  value=28.6139, format="%.6f", key="t_lat")
                with c2: lon = st.number_input("Longitude", value=77.2090, format="%.6f", key="t_lon")
                st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
                if st.button("⚡  LAUNCH SESSION", use_container_width=True):
                    with st.spinner("Initialising..."):
                        r = api("post", "/sessions/start", json={"teacher_id": uid, "subject_id": subj_map[chosen], "lat": lat, "lon": lon})
                    if r:
                        st.session_state.active_session = r
                        st.session_state.active_session_qr = r["qr_base64"]
                        st.rerun()

            active = api("get", f"/sessions/active?teacher_id={uid}") or []
            if active:
                st.markdown('<div class="cyber-div"></div><div class="sec-hdr">LIVE SESSIONS</div>', unsafe_allow_html=True)
                for s in active:
                    is_cur = st.session_state.active_session and st.session_state.active_session.get("session_id") == s["id"]
                    bc = "rgba(0,255,136,.35)" if is_cur else "var(--border)"
                    st.markdown(f'<div class="glass-card" style="border-color:{bc}"><div style="display:flex;align-items:center;justify-content:space-between"><div><span class="online-dot"></span><b style="font-size:1rem">{s["subject_name"]}</b></div><span class="badge badge-live">LIVE</span></div><div class="session-id">{s["id"]}</div><div style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--text-dim)">⏱ {s["started_at"][:16]}</div></div>', unsafe_allow_html=True)

        with right:
            if st.session_state.active_session:
                sess = st.session_state.active_session
                st.markdown('<div class="sec-hdr">ACTIVE SESSION</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="glass-card" style="border-color:rgba(0,255,136,.38)"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.8rem"><b style="font-family:Orbitron,monospace;font-size:.9rem;color:#fff">{sess["subject_name"]}</b><span class="badge badge-live"><span class="online-dot"></span>LIVE</span></div><div class="session-id">{sess["session_id"]}</div><div style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--text-dim);margin-top:.5rem">STARTED · {sess["started_at"][:16]} UTC</div></div>', unsafe_allow_html=True)

                if st.session_state.active_session_qr:
                    st.markdown('<div class="sec-hdr">QR CODE</div>', unsafe_allow_html=True)
                    qr_bytes = base64.b64decode(st.session_state.active_session_qr)
                    _, c2, _ = st.columns([1, 2, 1])
                    with c2:
                        st.markdown('<div class="qr-wrapper">', unsafe_allow_html=True)
                        st.image(qr_bytes, use_column_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div style="text-align:center;font-family:Share Tech Mono,monospace;font-size:.62rem;color:var(--text-dim);letter-spacing:.15em;margin-top:.4rem">DISPLAY TO STUDENTS FOR SCANNING</div>', unsafe_allow_html=True)

                st.markdown('<div class="cyber-div"></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("⛔  STOP SESSION", use_container_width=True):
                        api("post", f"/sessions/{sess['session_id']}/stop?teacher_id={uid}")
                        st.session_state.active_session = None
                        st.session_state.active_session_qr = None
                        st.success("Session terminated")
                        st.rerun()
                with c2:
                    if st.button("🔄  REFRESH", use_container_width=True): st.rerun()

                records = api("get", f"/reports/session/{sess['session_id']}") or []
                st.markdown(f'<div class="sec-hdr">ATTENDANCE FEED · {len(records)} PRESENT</div>', unsafe_allow_html=True)
                if records:
                    rows = ""
                    for r in records:
                        sc = r.get("face_score", 0); dist = r.get("distance_m", 0)
                        sc_col = "var(--green)" if sc >= 0.9 else "var(--amber)"
                        rows += f'<tr><td><b>{r["name"]}</b></td><td><span class="roll-code">{r["roll_no"]}</span></td><td><span style="color:{sc_col};font-family:Share Tech Mono,monospace;text-shadow:0 0 6px {sc_col}">{sc:.3f}</span></td><td style="font-family:Share Tech Mono,monospace;font-size:.78rem">{dist}m</td><td style="color:var(--text-dim);font-family:Share Tech Mono,monospace;font-size:.7rem">{r["marked_at"][11:16]}</td></tr>'
                    st.markdown(f'<table class="att-table"><thead><tr><th>Name</th><th>Roll</th><th>Face Score</th><th>Distance</th><th>Time</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align:center;padding:2rem;color:var(--text-dim);font-family:Share Tech Mono,monospace;font-size:.75rem;letter-spacing:.15em">[ AWAITING STUDENT CHECK-INS ]</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="glass-card" style="text-align:center;padding:4rem 2rem"><div style="font-size:4rem;opacity:.3;margin-bottom:1rem">📡</div><div style="font-family:Orbitron,monospace;font-size:.72rem;letter-spacing:.2em;color:var(--text-dim)">NO ACTIVE SESSION</div><div style="font-size:.85rem;color:var(--text-dim);margin-top:.5rem">Launch a session from the left panel</div></div>', unsafe_allow_html=True)

    # SUBJECTS
    with t2:
        ca, cb = st.columns([1, 1], gap="large")
        with ca:
            st.markdown('<div class="sec-hdr">CREATE SUBJECT</div>', unsafe_allow_html=True)
            s_name = st.text_input("Subject Name", placeholder="Machine Learning")
            s_code = st.text_input("Subject Code", placeholder="CS501")
            if st.button("➕  CREATE SUBJECT", use_container_width=True):
                if s_name and s_code:
                    r = api("post", "/subjects", json={"name": s_name, "code": s_code, "teacher_id": uid})
                    if r: st.success(f"✓ {r.get('message','Created')}"); st.rerun()
            st.markdown('<div class="cyber-div"></div><div class="sec-hdr">MY SUBJECTS</div>', unsafe_allow_html=True)
            subjects = api("get", f"/subjects?teacher_id={uid}") or []
            for s in subjects:
                st.markdown(f'<div class="glass-card" style="display:flex;align-items:center;justify-content:space-between;padding:1rem 1.2rem"><div><div style="font-weight:600;font-size:1rem">{s["name"]}</div><div style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--cyan-dim)">{s["code"]}</div></div><span class="badge badge-info">ID:{s["id"]}</span></div>', unsafe_allow_html=True)
            if not subjects: st.info("No subjects yet")

        with cb:
            st.markdown('<div class="sec-hdr">ENROLL STUDENT</div>', unsafe_allow_html=True)
            subjects = api("get", f"/subjects?teacher_id={uid}") or []
            if subjects:
                subj_map = {f"{s['name']} [{s['code']}]": s["id"] for s in subjects}
                enr_subj = st.selectbox("Subject", list(subj_map.keys()), key="enr_subj")
                enr_sid  = st.number_input("Student ID", min_value=1, step=1, key="enr_sid")
                if st.button("✅  ENROLL", use_container_width=True):
                    r = api("post", "/subjects/enroll", json={"student_id": int(enr_sid), "subject_id": subj_map[enr_subj]})
                    if r: st.success(f"✓ {r.get('message','Enrolled')}")
                st.markdown('<div class="cyber-div"></div><div class="sec-hdr">VIEW ROSTER</div>', unsafe_allow_html=True)
                view_subj = st.selectbox("Subject", list(subj_map.keys()), key="view_subj")
                if st.button("🔍  LOAD ROSTER", use_container_width=True):
                    students = api("get", f"/subjects/{subj_map[view_subj]}/students") or []
                    if students:
                        rows = "".join(f'<tr><td>{s["name"]}</td><td><span class="roll-code">{s["roll_no"]}</span></td><td><span class="badge badge-info">ID:{s["id"]}</span></td></tr>' for s in students)
                        st.markdown(f'<table class="att-table"><thead><tr><th>Name</th><th>Roll No</th><th>ID</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
                    else: st.info("No students enrolled")

    # REPORTS
    with t3:
        st.markdown('<div class="sec-hdr">SUBJECT ANALYTICS</div>', unsafe_allow_html=True)
        subjects = api("get", f"/subjects?teacher_id={uid}") or []
        if subjects:
            subj_map = {f"{s['name']} [{s['code']}]": s["id"] for s in subjects}
            rep_subj = st.selectbox("Subject", list(subj_map.keys()), key="rep_subj")
            if st.button("📊  GENERATE REPORT", use_container_width=True):
                with st.spinner("Computing analytics..."): summary = api("get", f"/reports/subject/{subj_map[rep_subj]}/summary") or []
                if summary:
                    avg = sum(s["percentage"] for s in summary) / len(summary)
                    good = sum(1 for s in summary if s["percentage"] >= 75)
                    risk = sum(1 for s in summary if s["percentage"] < 50)
                    st.markdown(f'<div class="metric-grid"><div class="metric-panel"><div class="metric-val" style="color:var(--cyan)">{len(summary)}</div><div class="metric-lbl">Enrolled</div></div><div class="metric-panel"><div class="metric-val" style="color:var(--green)">{avg:.0f}%</div><div class="metric-lbl">Avg Attendance</div></div><div class="metric-panel"><div class="metric-val" style="color:var(--green)">{good}</div><div class="metric-lbl">≥75% Good</div></div><div class="metric-panel"><div class="metric-val" style="color:var(--red)">{risk}</div><div class="metric-lbl">At Risk</div></div></div>', unsafe_allow_html=True)
                    rows = ""
                    for r in summary:
                        p = r["percentage"]
                        bc = "badge-live" if p >= 75 else "badge-warn" if p >= 50 else "badge-closed"
                        fc = "var(--green)" if p >= 75 else "var(--amber)" if p >= 50 else "var(--red)"
                        rows += f'<tr><td><b>{r["name"]}</b></td><td><span class="roll-code">{r["roll_no"]}</span></td><td style="font-family:Share Tech Mono,monospace">{r["attended"]}/{r["total_sessions"]}</td><td><div style="display:flex;align-items:center;gap:.6rem"><span class="badge {bc}">{p}%</span><div class="att-bar-bg" style="flex:1;min-width:60px"><div class="att-bar-fill" style="width:{p}%;background:{fc}"></div></div></div></td></tr>'
                    st.markdown(f'<table class="att-table"><thead><tr><th>Student</th><th>Roll No</th><th>Sessions</th><th>Attendance</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
                else: st.info("No data — start sessions first")
        else: st.info("Create subjects first")

    # ACCOUNT
    with t4:
        st.markdown('<div class="sec-hdr">ACCOUNT INFO</div>', unsafe_allow_html=True)
        u = st.session_state.user
        st.markdown(f'<div class="glass-card"><div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem"><div><div style="font-family:Share Tech Mono,monospace;font-size:.62rem;color:var(--text-dim);letter-spacing:.15em;margin-bottom:.3rem">USER ID</div><div style="font-family:Orbitron,monospace;font-size:1.2rem;color:var(--cyan)">{u["user_id"]}</div></div><div><div style="font-family:Share Tech Mono,monospace;font-size:.62rem;color:var(--text-dim);letter-spacing:.15em;margin-bottom:.3rem">ROLE</div><div style="font-family:Orbitron,monospace;font-size:1.2rem;color:var(--cyan)">{u["role"].upper()}</div></div><div style="grid-column:span 2"><div style="font-family:Share Tech Mono,monospace;font-size:.62rem;color:var(--text-dim);letter-spacing:.15em;margin-bottom:.3rem">EMAIL</div><div style="font-size:1rem">{u["email"]}</div></div></div></div>', unsafe_allow_html=True)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        if st.button("⟶  LOGOUT"):
            st.session_state.user = None
            st.session_state.active_session = None
            st.session_state.active_session_qr = None
            st.rerun()


# ── STUDENT ───────────────────────────────────────────────────────────────────
def student_dashboard():
    render_nav()
    uid = st.session_state.user["user_id"]
    st.markdown('<div class="page-header"><div class="page-title">STUDENT <span>PORTAL</span></div><div class="page-title-sub">Attendance Verification Terminal</div></div>', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["REGISTER PROFILE", "MARK ATTENDANCE", "MY RECORDS"])

    # REGISTER
    with t1:
        cl, cr = st.columns([1, 1], gap="large")
        with cl:
            st.markdown('<div class="sec-hdr">STUDENT REGISTRATION</div>', unsafe_allow_html=True)
            st.markdown('<div class="glass-card"><div style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--text-dim);letter-spacing:.1em;line-height:1.7">Complete once · Face embedding stored · Used for all future sessions</div></div>', unsafe_allow_html=True)
            reg_name = st.text_input("Full Name", placeholder="Aditya Sharma")
            reg_roll = st.text_input("Roll Number", placeholder="2024CS001")
            st.markdown('<div class="sec-hdr">FACE ENROLLMENT</div>', unsafe_allow_html=True)
            face_mode = st.radio("Capture Mode", ["Simulate (Demo)", "Manual"], horizontal=True, key="face_mode_reg")
            face_emb = st.session_state.get("reg_face_emb")
            if face_mode == "Simulate (Demo)":
                if st.button("📷  CAPTURE FACE", use_container_width=True):
                    face_emb = fake_embedding(seed=uid)
                    st.session_state["reg_face_emb"] = face_emb
                if face_emb:
                    st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.72rem;color:var(--green);padding:.5rem 0;letter-spacing:.08em">✓ EMBEDDING CAPTURED · 128 DIMENSIONS</div>', unsafe_allow_html=True)
            if st.button("💾  REGISTER PROFILE", use_container_width=True):
                if reg_name and reg_roll:
                    with st.spinner("Registering..."):
                        r = api("post", "/students/register", json={"user_id": uid, "name": reg_name, "roll_no": reg_roll, "face_embedding": face_emb})
                    if r: st.success(f"✓ {r.get('message','Registered')}")
                else: st.warning("Name and roll number required")

        with cr:
            st.markdown('<div class="sec-hdr">LOOKUP PROFILE</div>', unsafe_allow_html=True)
            chk = st.text_input("Roll Number to Search", key="chk_roll")
            if st.button("🔍  SEARCH", use_container_width=True, key="btn_lk"):
                s = api("get", f"/students/{chk}")
                if s:
                    st.markdown(f'<div class="glass-card" style="border-color:rgba(0,255,136,.3)"><div style="font-family:Orbitron,monospace;font-size:.58rem;letter-spacing:.2em;color:var(--green);margin-bottom:1rem">PROFILE FOUND</div><div style="display:grid;gap:.8rem"><div><div style="font-family:Share Tech Mono,monospace;font-size:.6rem;color:var(--text-dim);letter-spacing:.15em">NAME</div><div style="font-size:1.1rem;font-weight:600">{s["name"]}</div></div><div><div style="font-family:Share Tech Mono,monospace;font-size:.6rem;color:var(--text-dim);letter-spacing:.15em">ROLL NO</div><div class="session-id" style="margin:0;padding:.4rem .8rem">{s["roll_no"]}</div></div><div style="display:flex;justify-content:space-between"><div><div style="font-family:Share Tech Mono,monospace;font-size:.6rem;color:var(--text-dim);letter-spacing:.15em">STUDENT ID</div><div style="font-family:Orbitron,monospace;color:var(--cyan)">{s["id"]}</div></div><div><div style="font-family:Share Tech Mono,monospace;font-size:.6rem;color:var(--text-dim);letter-spacing:.15em">FACE</div><span class="badge badge-live">REGISTERED</span></div></div></div></div>', unsafe_allow_html=True)

    # MARK ATTENDANCE
    with t2:
        cl, cr = st.columns([1, 1], gap="large")
        with cl:
            st.markdown('<div class="sec-hdr">VERIFICATION STEPS</div>', unsafe_allow_html=True)

            st.markdown('<div class="step-indicator"><div class="step-num">01</div><div class="step-label">Session ID</div></div>', unsafe_allow_html=True)
            session_id = st.text_input("Paste session ID or scan QR", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", key="att_sid")

            st.markdown('<div class="step-indicator"><div class="step-num">02</div><div class="step-label">Roll Number</div></div>', unsafe_allow_html=True)
            roll_no = st.text_input("Your Roll Number", placeholder="2024CS001", key="att_roll")

            st.markdown('<div class="step-indicator"><div class="step-num">03</div><div class="step-label">Face Scan</div></div>', unsafe_allow_html=True)
            face_att_mode = st.radio("Mode", ["Simulate (Demo)", "Custom Seed"], horizontal=True, key="face_mode_att")
            captured_emb = st.session_state.get("att_face_emb")
            if face_att_mode == "Simulate (Demo)":
                if st.button("📷  SCAN FACE", use_container_width=True, key="btn_fs"):
                    captured_emb = fake_embedding(seed=uid)
                    st.session_state["att_face_emb"] = captured_emb
            else:
                sv = st.number_input("Seed (use your user_id for a match)", value=uid, step=1, key="sv")
                if st.button("📷  GENERATE", use_container_width=True, key="btn_fg"):
                    captured_emb = fake_embedding(seed=int(sv))
                    st.session_state["att_face_emb"] = captured_emb
            if captured_emb:
                st.markdown('<div style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--green);padding:.4rem 0;letter-spacing:.08em">✓ FACE EMBEDDING READY</div>', unsafe_allow_html=True)

            st.markdown('<div class="step-indicator"><div class="step-num">04</div><div class="step-label">GPS Location</div></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: att_lat = st.number_input("Latitude",  value=28.6139, format="%.6f", key="att_lat")
            with c2: att_lon = st.number_input("Longitude", value=77.2090, format="%.6f", key="att_lon")

        with cr:
            st.markdown('<div class="sec-hdr">SUBMISSION STATUS</div>', unsafe_allow_html=True)

            if session_id and len(session_id) > 10:
                si = api("get", f"/sessions/{session_id}")
                if si:
                    ia = si.get("is_active")
                    sbadge = '<span class="badge badge-live">LIVE</span>' if ia else '<span class="badge badge-closed">CLOSED</span>'
                    bc = "rgba(0,255,136,.3)" if ia else "rgba(255,56,96,.3)"
                    st.markdown(f'<div class="glass-card" style="border-color:{bc}"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem"><span style="font-family:Orbitron,monospace;font-size:.58rem;letter-spacing:.2em;color:var(--text-dim)">SESSION STATUS</span>{sbadge}</div><div style="font-family:Share Tech Mono,monospace;font-size:.72rem;color:var(--text-dim);line-height:1.8">⏱ Started: {str(si.get("started_at",""))[:16]}<br>📍 GPS: {si.get("lat",0):.4f}, {si.get("lon",0):.4f}</div></div>', unsafe_allow_html=True)

            checks = [("Session ID", bool(session_id and len(session_id) > 10)), ("Roll Number", bool(roll_no)), ("Face Scan", bool(captured_emb)), ("GPS", True)]
            cl_html = '<div class="glass-card"><div style="display:grid;gap:.5rem">'
            for label, done in checks:
                ic = "✓" if done else "○"; co = "var(--green)" if done else "var(--text-dim)"
                cl_html += f'<div style="display:flex;align-items:center;gap:.8rem;font-family:Share Tech Mono,monospace;font-size:.75rem"><span style="color:{co};font-size:1rem">{ic}</span><span style="color:{"var(--text)" if done else "var(--text-dim)"}">{label}</span><span style="margin-left:auto;font-size:.62rem;color:{"var(--green)" if done else "var(--text-dim)"}">{"READY" if done else "PENDING"}</span></div>'
            cl_html += "</div></div>"
            st.markdown(cl_html, unsafe_allow_html=True)

            all_ready = all(d for _, d in checks)
            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
            if st.button("🎯  SUBMIT ATTENDANCE", use_container_width=True, disabled=not all_ready, key="btn_mark"):
                with st.spinner("Verifying face + GPS..."):
                    result = api("post", "/attendance/mark", json={"session_id": session_id, "student_roll_no": roll_no, "face_embedding": captured_emb, "lat": att_lat, "lon": att_lon})
                if result:
                    if result.get("success"):
                        fs = result.get("face_score", 0); dm = result.get("distance_m", 0)
                        st.success(result["message"])
                        st.markdown(f'<div class="metric-grid" style="margin-top:1rem"><div class="metric-panel"><div class="metric-val" style="color:var(--green)">{fs:.2f}</div><div class="metric-lbl">Face Score</div></div><div class="metric-panel"><div class="metric-val" style="color:var(--cyan)">{dm}m</div><div class="metric-lbl">Distance</div></div></div>', unsafe_allow_html=True)
                        st.session_state.pop("att_face_emb", None)
                    else:
                        st.error(result.get("message", "Failed"))
                        if result.get("face_score") is not None: st.info(f"Face score: {result['face_score']:.3f}  (threshold: 0.80)")
                        if result.get("distance_m") is not None: st.info(f"Distance: {result['distance_m']} m  (limit: 50 m)")

    # MY RECORDS
    with t3:
        st.markdown('<div class="sec-hdr">ATTENDANCE HISTORY</div>', unsafe_allow_html=True)
        my_roll = st.text_input("Your Roll Number", key="my_roll")
        if st.button("📋  LOAD HISTORY", use_container_width=True, key="btn_hist"):
            with st.spinner("Fetching..."): records = api("get", f"/reports/student/{my_roll}") or []
            if records:
                avg_sc = sum(r.get("face_score", 0) for r in records) / len(records)
                st.markdown(f'<div class="metric-grid"><div class="metric-panel"><div class="metric-val" style="color:var(--cyan)">{len(records)}</div><div class="metric-lbl">Sessions Attended</div></div><div class="metric-panel"><div class="metric-val" style="color:var(--green)">{avg_sc:.2f}</div><div class="metric-lbl">Avg Face Score</div></div></div>', unsafe_allow_html=True)
                rows = ""
                for r in records:
                    sc = r.get("face_score", 0); sc_col = "var(--green)" if sc >= 0.9 else "var(--amber)"
                    rows += f'<tr><td><b>{r["subject"]}</b></td><td style="font-family:Share Tech Mono,monospace;font-size:.75rem;color:var(--text-dim)">{str(r.get("session_date",""))[:10]}</td><td style="color:{sc_col};font-family:Share Tech Mono,monospace;text-shadow:0 0 6px {sc_col}">{sc:.3f}</td><td style="font-family:Share Tech Mono,monospace;font-size:.78rem">{r.get("distance_m",0)}m</td><td style="font-family:Share Tech Mono,monospace;font-size:.7rem;color:var(--text-dim)">{str(r.get("marked_at",""))[:16]}</td></tr>'
                st.markdown(f'<table class="att-table"><thead><tr><th>Subject</th><th>Date</th><th>Face Score</th><th>Distance</th><th>Timestamp</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
            else: st.info("No records found")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("⟶  LOGOUT", key="stu_logout"):
            st.session_state.user = None
            st.rerun()


# ── ROUTER ────────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.user:
        page_login()
    elif st.session_state.user["role"] == "teacher":
        teacher_dashboard()
    else:
        student_dashboard()

if __name__ == "__main__":
    main()