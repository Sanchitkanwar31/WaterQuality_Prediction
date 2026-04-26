import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pickle, os, warnings
warnings.filterwarnings("ignore")

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaGuard | Water Quality AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global CSS / Styles ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [data-testid="stAppViewContainer"] {
    background: #020b18 !important;
    color: #d4eaf7;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section.main > div { padding-top: 0 !important; }

/* ── Animated water background ── */
body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
        radial-gradient(ellipse 80% 60% at 20% 30%, rgba(0,120,200,.18) 0%, transparent 70%),
        radial-gradient(ellipse 60% 50% at 80% 70%, rgba(0,200,180,.12) 0%, transparent 70%),
        radial-gradient(ellipse 40% 40% at 60% 10%, rgba(30,60,120,.25) 0%, transparent 70%),
        #020b18;
    animation: bgPulse 12s ease-in-out infinite alternate;
}
@keyframes bgPulse {
    0%  { background-position: 0% 50%; }
    100%{ background-position: 100% 50%; }
}

/* Floating particle layer */
body::after {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
        radial-gradient(circle, rgba(0,180,255,.35) 1px, transparent 1px),
        radial-gradient(circle, rgba(0,255,200,.25) 1px, transparent 1px);
    background-size: 60px 60px, 90px 90px;
    background-position: 0 0, 30px 30px;
    animation: particleDrift 20s linear infinite;
    opacity: .4;
}
@keyframes particleDrift {
    0%   { transform: translateY(0) translateX(0); }
    100% { transform: translateY(-60px) translateX(20px); }
}

/* ── Layout wrapper ── */
.aq-wrap { position: relative; z-index: 1; }

/* ── HERO ── */
.hero {
    min-height: 100vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center;
    padding: 60px 24px;
    position: relative; overflow: hidden;
}
.hero-drop {
    font-size: clamp(80px,15vw,160px); line-height: 1;
    animation: dropFloat 4s ease-in-out infinite;
    display: block; margin-bottom: 8px;
}
@keyframes dropFloat {
    0%,100%{ transform: translateY(0) scale(1); filter: drop-shadow(0 0 30px rgba(0,180,255,.6)); }
    50%    { transform: translateY(-18px) scale(1.05); filter: drop-shadow(0 0 60px rgba(0,255,200,.8)); }
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(36px,6vw,88px); font-weight: 800;
    letter-spacing: -2px; line-height: 1.05;
    background: linear-gradient(135deg, #00d4ff 0%, #00ffcc 40%, #4facfe 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 16px;
}
.hero-sub {
    font-size: clamp(15px,2vw,20px); font-weight: 300; color: #7db8d4;
    max-width: 580px; line-height: 1.7; margin: 0 auto 40px;
    font-style: italic;
}
.hero-stats {
    display: flex; gap: 40px; justify-content: center; flex-wrap: wrap;
    margin-bottom: 52px;
}
.stat-pill {
    background: rgba(0,180,255,.08);
    border: 1px solid rgba(0,180,255,.25);
    border-radius: 100px; padding: 10px 28px;
    backdrop-filter: blur(12px);
    font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 600;
    color: #00d4ff; letter-spacing: .5px;
    transition: all .3s ease;
}
.stat-pill:hover {
    background: rgba(0,180,255,.18);
    border-color: rgba(0,255,200,.5);
    transform: translateY(-3px);
}
.hero-cta {
    display: inline-block;
    padding: 16px 48px; border-radius: 100px;
    background: linear-gradient(135deg, #00d4ff, #00ffcc);
    color: #020b18; font-family: 'Syne', sans-serif;
    font-weight: 700; font-size: 17px; letter-spacing: .5px;
    text-decoration: none; cursor: pointer; border: none;
    box-shadow: 0 0 40px rgba(0,212,255,.35);
    transition: all .3s ease;
}
.hero-cta:hover {
    transform: translateY(-4px) scale(1.03);
    box-shadow: 0 0 70px rgba(0,212,255,.55);
}

/* Scroll chevron */
.scroll-hint {
    position: absolute; bottom: 36px; left: 50%; transform: translateX(-50%);
    animation: bounce 2s infinite;
    color: rgba(0,212,255,.5); font-size: 28px;
}
@keyframes bounce {
    0%,100%{ transform: translateX(-50%) translateY(0); }
    50%    { transform: translateX(-50%) translateY(10px); }
}

/* ── NAV TABS ── */
.tab-nav {
    display: flex; gap: 0; overflow-x: auto;
    background: rgba(2,11,24,.85);
    border-bottom: 1px solid rgba(0,180,255,.15);
    position: sticky; top: 0; z-index: 100;
    backdrop-filter: blur(20px);
    padding: 0 24px;
}
.tab-nav::-webkit-scrollbar { display: none; }
.tab-btn {
    padding: 18px 28px; border: none; background: none;
    color: #7db8d4; font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 600; letter-spacing: .8px;
    text-transform: uppercase; cursor: pointer; white-space: nowrap;
    border-bottom: 2px solid transparent;
    transition: all .3s ease; position: relative;
}
.tab-btn:hover  { color: #00d4ff; }
.tab-btn.active { color: #00d4ff; border-bottom-color: #00d4ff; }
.tab-btn .tab-icon { margin-right: 8px; }

/* ── Section wrapper ── */
.section {
    padding: 72px clamp(16px,5vw,80px);
    position: relative; z-index: 1;
}
.section-tag {
    font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 700;
    letter-spacing: 3px; color: #00ffcc; text-transform: uppercase;
    margin-bottom: 12px;
}
.section-title {
    font-family: 'Syne', sans-serif; font-size: clamp(28px,4vw,52px);
    font-weight: 800; line-height: 1.1;
    background: linear-gradient(135deg, #d4eaf7 30%, #00d4ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 12px;
}
.section-lead {
    color: #7db8d4; font-size: 17px; max-width: 560px;
    line-height: 1.7; margin-bottom: 48px; font-weight: 300;
}

/* ── CARDS ── */
.card-grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); }
.card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(0,180,255,.12);
    border-radius: 20px; padding: 28px 28px 32px;
    backdrop-filter: blur(12px);
    transition: all .35s ease; position: relative; overflow: hidden;
}
.card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #00d4ff, transparent);
    opacity: 0; transition: opacity .35s;
}
.card:hover { transform: translateY(-6px); border-color: rgba(0,180,255,.35); box-shadow: 0 20px 60px rgba(0,0,0,.4); }
.card:hover::before { opacity: 1; }
.card-icon { font-size: 36px; margin-bottom: 16px; display: block; }
.card h3 { font-family:'Syne',sans-serif; font-size:18px; font-weight:700; color:#d4eaf7; margin-bottom:8px; }
.card p  { color:#7db8d4; font-size:14px; line-height:1.7; font-weight:300; }

/* ── FORM CARD ── */
.form-card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(0,180,255,.15);
    border-radius: 24px; padding: 40px;
    backdrop-filter: blur(16px);
    max-width: 900px;
}

/* Streamlit widget overrides */
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label {
    color: #7db8d4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important; letter-spacing: .3px;
}
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: rgba(0,180,255,.06) !important;
    border: 1px solid rgba(0,180,255,.2) !important;
    border-radius: 10px !important;
    color: #d4eaf7 !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: rgba(0,212,255,.6) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,.15) !important;
}
div[data-testid="stSlider"] > div > div > div {
    background: linear-gradient(90deg,#00d4ff,#00ffcc) !important;
}
.stButton > button {
    background: linear-gradient(135deg,#00d4ff,#00ffcc) !important;
    color: #020b18 !important; border: none !important;
    border-radius: 100px !important; padding: 14px 36px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 15px !important;
    transition: all .3s ease !important;
    box-shadow: 0 0 30px rgba(0,212,255,.25) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 0 55px rgba(0,212,255,.45) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: rgba(0,180,255,.06) !important;
    border: 1px solid rgba(0,180,255,.2) !important;
    border-radius: 10px !important;
    color: #d4eaf7 !important;
}

/* ── RESULT BADGE ── */
.result-safe {
    display: inline-flex; align-items: center; gap: 12px;
    background: linear-gradient(135deg, rgba(0,255,150,.12), rgba(0,200,120,.06));
    border: 1px solid rgba(0,255,150,.3);
    border-radius: 16px; padding: 20px 32px;
    font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700;
    color: #00ff96; margin: 20px 0;
    animation: glowSafe 2s ease-in-out infinite alternate;
}
.result-unsafe {
    display: inline-flex; align-items: center; gap: 12px;
    background: linear-gradient(135deg, rgba(255,80,80,.12), rgba(200,40,40,.06));
    border: 1px solid rgba(255,80,80,.3);
    border-radius: 16px; padding: 20px 32px;
    font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700;
    color: #ff5555; margin: 20px 0;
    animation: glowUnsafe 2s ease-in-out infinite alternate;
}
@keyframes glowSafe   { 0%{box-shadow:0 0 20px rgba(0,255,150,.2)} 100%{box-shadow:0 0 40px rgba(0,255,150,.45)} }
@keyframes glowUnsafe { 0%{box-shadow:0 0 20px rgba(255,80,80,.2)} 100%{box-shadow:0 0 40px rgba(255,80,80,.45)} }

/* ── METRIC PILL ── */
.metric-row { display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }
.metric-pill {
    flex: 1; min-width: 140px;
    background: rgba(0,180,255,.07);
    border: 1px solid rgba(0,180,255,.15);
    border-radius: 14px; padding: 18px 20px; text-align: center;
}
.metric-pill .val { font-family:'Syne',sans-serif; font-size:26px; font-weight:800; color:#00d4ff; }
.metric-pill .lbl { font-size:11px; color:#7db8d4; letter-spacing:1px; text-transform:uppercase; margin-top:4px; }

/* ── WHO TABLE ── */
.who-table { width:100%; border-collapse:collapse; }
.who-table th {
    background: rgba(0,180,255,.12);
    color: #00d4ff; font-family:'Syne',sans-serif; font-size:12px;
    letter-spacing:1px; text-transform:uppercase;
    padding: 14px 20px; text-align:left;
    border-bottom: 1px solid rgba(0,180,255,.2);
}
.who-table td {
    padding: 13px 20px; font-size:14px; color:#b0cce0;
    border-bottom: 1px solid rgba(0,180,255,.07);
}
.who-table tr:hover td { background: rgba(0,180,255,.05); color:#d4eaf7; }
.who-ok   { color:#00ff96 !important; font-weight:600; }
.who-warn { color:#ffcc00 !important; font-weight:600; }
.who-bad  { color:#ff5555 !important; font-weight:600; }
.badge {
    display: inline-block; padding: 3px 12px; border-radius: 100px;
    font-size: 11px; font-weight: 700; letter-spacing: .5px;
}
.badge-ok   { background:rgba(0,255,150,.15); color:#00ff96; }
.badge-warn { background:rgba(255,200,0,.15);  color:#ffcc00; }
.badge-bad  { background:rgba(255,80,80,.15);  color:#ff5555; }

/* ── AI CHAT ── */
.ai-msg-user, .ai-msg-bot {
    display:flex; gap:14px; margin-bottom:20px; align-items:flex-start;
}
.ai-msg-user { flex-direction: row-reverse; }
.ai-avatar {
    width:36px; height:36px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center; font-size:16px;
}
.ai-avatar-bot { background: linear-gradient(135deg,#00d4ff,#00ffcc); color:#020b18; }
.ai-avatar-usr { background: rgba(0,180,255,.2); color:#00d4ff; border:1px solid rgba(0,180,255,.3); }
.ai-bubble {
    max-width: 72%; padding: 14px 20px; border-radius: 16px; line-height: 1.65; font-size:14px;
}
.ai-bubble-bot {
    background: rgba(0,180,255,.08); border: 1px solid rgba(0,180,255,.18);
    border-top-left-radius: 4px; color:#d4eaf7;
}
.ai-bubble-usr {
    background: rgba(0,212,255,.13); border: 1px solid rgba(0,212,255,.25);
    border-top-right-radius: 4px; color:#d4eaf7; text-align:right;
}

/* ── FOOTER ── */
.footer {
    text-align:center; padding: 48px 24px;
    border-top: 1px solid rgba(0,180,255,.1);
    color: #3d6278; font-size: 13px; font-weight:300;
    position:relative; z-index:1;
}
.footer span { color:#00d4ff; }

/* ── Streamlit tab overrides ── */
.stTabs [data-baseweb="tab-list"] { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "home"
if "ai_history" not in st.session_state:
    st.session_state.ai_history = []
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

# ─── Helper: load model (graceful fallback) ───────────────────────────────────
@st.cache_resource
def load_model():
    for path in ["model.pkl", "water_quality_model.pkl", "models/model.pkl"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return pickle.load(f)
    return None

model = load_model()

# ─── WHO Compliance Data ──────────────────────────────────────────────────────
WHO_STANDARDS = [
    {"Parameter": "pH", "WHO Limit": "6.5 – 8.5", "Unit": "—", "Health Risk": "Corrosion / scaling"},
    {"Parameter": "Hardness", "WHO Limit": "≤ 500", "Unit": "mg/L", "Health Risk": "Cardiovascular concern at extremes"},
    {"Parameter": "Solids (TDS)", "WHO Limit": "≤ 500", "Unit": "mg/L", "Health Risk": "Palatability, mineral toxicity"},
    {"Parameter": "Chloramines", "WHO Limit": "≤ 4", "Unit": "mg/L", "Health Risk": "Disinfection by-product"},
    {"Parameter": "Sulfate", "WHO Limit": "≤ 250", "Unit": "mg/L", "Health Risk": "Laxative effect"},
    {"Parameter": "Conductivity", "WHO Limit": "≤ 400", "Unit": "µS/cm", "Health Risk": "Indicator of dissolved ions"},
    {"Parameter": "Organic Carbon", "WHO Limit": "≤ 2", "Unit": "mg/L", "Health Risk": "Disinfection by-product precursor"},
    {"Parameter": "Trihalomethanes", "WHO Limit": "≤ 80", "Unit": "µg/L", "Health Risk": "Carcinogenic risk"},
    {"Parameter": "Turbidity", "WHO Limit": "≤ 1", "Unit": "NTU", "Health Risk": "Pathogen indicator"},
]

# ─── Navigation ───────────────────────────────────────────────────────────────
def nav(tab_id):
    st.session_state.active_tab = tab_id

# ─── HERO SECTION ─────────────────────────────────────────────────────────────
def render_hero():
    st.markdown("""
    <div class="aq-wrap">
    <section class="hero">
        <span class="hero-drop">💧</span>
        <h1>AquaGuard</h1>
        <p class="hero-sub">
            AI-powered water quality intelligence. Know what's in your water —
            instantly, accurately, and at scale.
        </p>
        <div class="hero-stats">
            <span class="stat-pill">🧬 ML-Powered Prediction</span>
            <span class="stat-pill">🌍 WHO Compliance Check</span>
            <span class="stat-pill">📊 Deep Analytics</span>
            <span class="stat-pill">🤖 AI Assistant</span>
        </div>
    </section>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("🔬 Run Prediction", use_container_width=True):
            nav("predict")
            st.rerun()
    with col2:
        if st.button("📊 View Analysis", use_container_width=True):
            nav("analysis")
            st.rerun()
    with col3:
        if st.button("🤖 Ask AI", use_container_width=True):
            nav("ai")
            st.rerun()

    # Feature cards
    st.markdown("""
    <div class="aq-wrap section">
        <p class="section-tag">What We Offer</p>
        <h2 class="section-title">Complete Water Intelligence</h2>
        <p class="section-lead">From raw sensor readings to actionable insights — AquaGuard covers the full pipeline.</p>
        <div class="card-grid">
            <div class="card">
                <span class="card-icon">🔬</span>
                <h3>ML Prediction</h3>
                <p>Input 9 physicochemical parameters and get an instant potability verdict powered by a trained machine learning model.</p>
            </div>
            <div class="card">
                <span class="card-icon">📈</span>
                <h3>Parameter Analysis</h3>
                <p>Interactive charts showing parameter distributions, correlations, and risk zones — visualise your data like never before.</p>
            </div>
            <div class="card">
                <span class="card-icon">🤖</span>
                <h3>AI Assistant</h3>
                <p>Ask anything about water quality. Get expert-level answers powered by Claude — your always-on water quality advisor.</p>
            </div>
            <div class="card">
                <span class="card-icon">🌍</span>
                <h3>WHO Compliance</h3>
                <p>Cross-reference your readings against official WHO drinking water guidelines and get a traffic-light compliance report.</p>
            </div>
            <div class="card">
                <span class="card-icon">📋</span>
                <h3>Batch Reports</h3>
                <p>Upload a CSV of samples and get a full compliance report with individual risk flags and summary statistics.</p>
            </div>
            <div class="card">
                <span class="card-icon">⚡</span>
                <h3>Real-time Alerts</h3>
                <p>Threshold-based alert logic highlights parameters that exceed safe limits the moment data is entered.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── PREDICTION TAB ───────────────────────────────────────────────────────────
def render_prediction():
    st.markdown("""
    <div class="aq-wrap section">
        <p class="section-tag">Machine Learning</p>
        <h2 class="section-title">Water Potability Prediction</h2>
        <p class="section-lead">Enter the 9 physicochemical parameters below. Our model will predict whether the water sample is safe to drink.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="aq-wrap" style="padding:0 clamp(16px,5vw,80px) 24px;">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        ph          = st.number_input("⚗️ pH Level",              min_value=0.0, max_value=14.0, value=7.0,    step=0.01, format="%.2f")
        hardness    = st.number_input("🪨 Hardness (mg/L)",        min_value=0.0, max_value=1000.0,value=200.0, step=0.1)
        solids      = st.number_input("🧂 TDS (mg/L)",             min_value=0.0, max_value=70000.0,value=20000.0,step=1.0)
    with col2:
        chloramines = st.number_input("🧪 Chloramines (mg/L)",     min_value=0.0, max_value=20.0, value=7.0,    step=0.01)
        sulfate     = st.number_input("🌋 Sulfate (mg/L)",         min_value=0.0, max_value=500.0,value=333.0,  step=0.1)
        conductivity= st.number_input("⚡ Conductivity (µS/cm)",   min_value=0.0, max_value=1000.0,value=400.0, step=0.1)
    with col3:
        organic_c   = st.number_input("🌿 Organic Carbon (mg/L)", min_value=0.0, max_value=30.0, value=14.0,   step=0.01)
        trihalometh = st.number_input("☣️ Trihalomethanes (µg/L)",min_value=0.0, max_value=130.0,value=66.0,   step=0.01)
        turbidity   = st.number_input("🌊 Turbidity (NTU)",       min_value=0.0, max_value=10.0, value=4.0,    step=0.01)

    st.markdown("</div>", unsafe_allow_html=True)

    input_data = np.array([[ph, hardness, solids, chloramines, sulfate,
                            conductivity, organic_c, trihalometh, turbidity]])

    # Live parameter status alerts
    alerts = []
    if not (6.5 <= ph <= 8.5):      alerts.append(("⚗️ pH", f"{ph:.2f}", "Outside WHO range 6.5–8.5"))
    if hardness > 500:               alerts.append(("🪨 Hardness", f"{hardness:.0f} mg/L", "Exceeds 500 mg/L"))
    if solids > 500:                 alerts.append(("🧂 TDS", f"{solids:.0f} mg/L", "Exceeds 500 mg/L"))
    if chloramines > 4:              alerts.append(("🧪 Chloramines", f"{chloramines:.2f} mg/L", "Exceeds 4 mg/L"))
    if sulfate > 250:                alerts.append(("🌋 Sulfate", f"{sulfate:.0f} mg/L", "Exceeds 250 mg/L"))
    if conductivity > 400:           alerts.append(("⚡ Conductivity", f"{conductivity:.0f} µS/cm", "Exceeds 400 µS/cm"))
    if organic_c > 2:                alerts.append(("🌿 Organic Carbon", f"{organic_c:.2f} mg/L", "Exceeds 2 mg/L"))
    if trihalometh > 80:             alerts.append(("☣️ Trihalomethanes", f"{trihalometh:.2f} µg/L", "Exceeds 80 µg/L"))
    if turbidity > 1:                alerts.append(("🌊 Turbidity", f"{turbidity:.2f} NTU", "Exceeds 1 NTU"))

    if alerts:
        warn_html = "".join([f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,200,0,.1);">'
                             f'<span style="min-width:150px;font-weight:600;color:#d4eaf7">{a[0]}</span>'
                             f'<span style="min-width:110px;color:#ffcc00;font-weight:700">{a[1]}</span>'
                             f'<span style="color:#7db8d4;font-size:13px">{a[2]}</span></div>'
                             for a in alerts])
        st.markdown(f"""
        <div style="background:rgba(255,200,0,.06);border:1px solid rgba(255,200,0,.25);
                    border-radius:14px;padding:20px 24px;margin:20px 0;">
            <p style="font-family:Syne,sans-serif;font-size:13px;font-weight:700;
                      color:#ffcc00;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;">
                ⚠️ {len(alerts)} Parameter{'s' if len(alerts)>1 else ''} Outside WHO Limits
            </p>
            {warn_html}
        </div>
        """, unsafe_allow_html=True)

    if st.button("🔬 Predict Water Quality", use_container_width=True):
        if model is not None:
            pred = model.predict(input_data)[0]
            proba = model.predict_proba(input_data)[0] if hasattr(model, "predict_proba") else [0.5, 0.5]
            st.session_state.prediction_result = {
                "pred": pred, "proba": proba, "inputs": input_data[0].tolist()
            }
        else:
            # Demo fallback when no model file is present
            score = sum([
                1 if 6.5<=ph<=8.5 else 0,
                1 if hardness<=500 else 0,
                1 if solids<=500 else 0,
                1 if chloramines<=4 else 0,
                1 if sulfate<=250 else 0,
                1 if conductivity<=400 else 0,
                1 if organic_c<=2 else 0,
                1 if trihalometh<=80 else 0,
                1 if turbidity<=1 else 0,
            ])
            pred  = 1 if score >= 7 else 0
            safe_p = score / 9
            st.session_state.prediction_result = {
                "pred": pred, "proba": [1-safe_p, safe_p], "inputs": input_data[0].tolist(),
                "demo": True
            }

    res = st.session_state.prediction_result
    if res:
        safe   = res["pred"] == 1
        conf   = res["proba"][1] if safe else res["proba"][0]
        label  = "✅ POTABLE — Safe to Drink" if safe else "❌ NON-POTABLE — Not Safe"
        cls    = "result-safe" if safe else "result-unsafe"
        demo_note = '<span style="font-size:12px;color:#7db8d4;margin-left:12px;">(demo mode – load model.pkl for real predictions)</span>' if res.get("demo") else ""

        st.markdown(f'<div class="{cls}">{label}{demo_note}</div>', unsafe_allow_html=True)

        # Confidence gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(conf*100, 1),
            number={"suffix": "%", "font": {"size": 36, "color": "#00d4ff"}},
            title={"text": "Confidence", "font": {"size": 14, "color": "#7db8d4"}},
            gauge={
                "axis": {"range": [0,100], "tickcolor": "#3d6278"},
                "bar": {"color": "#00ff96" if safe else "#ff5555"},
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": "rgba(0,180,255,.2)",
                "steps": [
                    {"range": [0,50],  "color": "rgba(255,80,80,.08)"},
                    {"range": [50,75], "color": "rgba(255,200,0,.08)"},
                    {"range": [75,100],"color": "rgba(0,255,150,.08)"},
                ],
                "threshold": {"line": {"color":"#00d4ff","width":2}, "thickness":.75,"value": conf*100}
            }
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#d4eaf7", height=240, margin=dict(t=20,b=0,l=20,r=20)
        )
        st.plotly_chart(fig, use_container_width=True, key="gauge")

        # Radar chart of parameter health
        params = ["pH","Hardness","TDS","Chloramines","Sulfate","Conductivity","Org.Carbon","THMs","Turbidity"]
        max_vals = [14, 1000, 70000, 20, 500, 1000, 30, 130, 10]
        norm = [min(v/m, 1.0) for v,m in zip(res["inputs"], max_vals)]
        fig2 = go.Figure(go.Scatterpolar(
            r=norm + [norm[0]], theta=params + [params[0]],
            fill='toself', name='Sample',
            fillcolor='rgba(0,212,255,.12)',
            line=dict(color='#00d4ff', width=2)
        ))
        fig2.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0,1], tickfont=dict(color='#3d6278'), gridcolor='rgba(0,180,255,.1)'),
                angularaxis=dict(tickfont=dict(color='#7db8d4'), gridcolor='rgba(0,180,255,.1)')
            ),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False, height=340, margin=dict(t=20,b=20)
        )
        st.plotly_chart(fig2, use_container_width=True, key="radar")

    st.markdown("</div>", unsafe_allow_html=True)


# ─── ANALYSIS TAB ─────────────────────────────────────────────────────────────
def render_analysis():
    st.markdown("""
    <div class="aq-wrap section">
        <p class="section-tag">Data Analytics</p>
        <h2 class="section-title">Parameter Analysis</h2>
        <p class="section-lead">Explore how water quality parameters are distributed, correlated, and interact with potability outcomes.</p>
    </div>
    """, unsafe_allow_html=True)

    # Generate synthetic representative data for demo
    np.random.seed(42)
    n = 300
    demo_df = pd.DataFrame({
        "pH":            np.random.normal(7.1, 1.0, n).clip(3, 12),
        "Hardness":      np.random.normal(210, 80, n).clip(50, 600),
        "Solids":        np.random.normal(22000, 8000, n).clip(2000, 60000),
        "Chloramines":   np.random.normal(7.1, 2, n).clip(0.5, 14),
        "Sulfate":       np.random.normal(333, 60, n).clip(120, 500),
        "Conductivity":  np.random.normal(426, 70, n).clip(200, 750),
        "OrganicCarbon": np.random.normal(14, 4, n).clip(2, 28),
        "Trihalomethanes":np.random.normal(66, 16, n).clip(10, 125),
        "Turbidity":     np.random.normal(4.0, 1.0, n).clip(1, 8),
        "Potable":       np.random.choice([0,1], n, p=[0.61, 0.39])
    })

    tab_a, tab_b, tab_c = st.tabs(["Distribution", "Correlation", "Potability Breakdown"])

    with tab_a:
        param = st.selectbox("Select Parameter", demo_df.columns[:-1].tolist(), key="dist_param")
        fig = go.Figure()
        for label, color, grp in [(0, "#ff5555","Non-Potable"), (1,"#00ff96","Potable")]:
            sub = demo_df[demo_df["Potable"]==label][param]
            fig.add_trace(go.Histogram(x=sub, name=grp, opacity=.75,
                                       marker_color=color, nbinsx=30))
        fig.update_layout(
            barmode='overlay', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#d4eaf7', legend=dict(bgcolor='rgba(0,0,0,0)'),
            xaxis=dict(gridcolor='rgba(0,180,255,.08)', title=param),
            yaxis=dict(gridcolor='rgba(0,180,255,.08)', title='Count'),
            title=f"Distribution of {param} by Potability",
            height=380, margin=dict(t=40,b=20)
        )
        st.plotly_chart(fig, use_container_width=True, key="hist")

    with tab_b:
        corr = demo_df.corr(numeric_only=True)
        fig2 = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale=[[0,'#ff5555'],[.5,'#020b18'],[1,'#00d4ff']],
            zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate='%{text}', textfont=dict(size=11, color='#d4eaf7'),
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#d4eaf7', height=440, margin=dict(t=20,b=20)
        )
        st.plotly_chart(fig2, use_container_width=True, key="heatmap")

    with tab_c:
        fig3 = make_subplots(rows=3, cols=3, subplot_titles=demo_df.columns[:-1].tolist())
        for i, col in enumerate(demo_df.columns[:-1]):
            r, c = divmod(i, 3)
            for label, color, grp in [(0,'#ff5555','Non-Potable'),(1,'#00ff96','Potable')]:
                fig3.add_trace(go.Box(
                    y=demo_df[demo_df["Potable"]==label][col],
                    name=grp, marker_color=color, showlegend=(i==0)
                ), row=r+1, col=c+1)
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#d4eaf7', height=700,
            margin=dict(t=40,b=20), boxmode='group',
            legend=dict(bgcolor='rgba(0,0,0,0)')
        )
        fig3.update_xaxes(showgrid=False)
        fig3.update_yaxes(gridcolor='rgba(0,180,255,.08)')
        st.plotly_chart(fig3, use_container_width=True, key="boxes")

    # Summary metrics
    pot_pct = demo_df["Potable"].mean()*100
    st.markdown(f"""
    <div class="aq-wrap" style="padding:0 clamp(16px,5vw,80px) 48px;">
    <div class="metric-row">
        <div class="metric-pill"><div class="val">{n}</div><div class="lbl">Samples</div></div>
        <div class="metric-pill"><div class="val">{pot_pct:.1f}%</div><div class="lbl">Potable</div></div>
        <div class="metric-pill"><div class="val">{demo_df["pH"].mean():.2f}</div><div class="lbl">Avg pH</div></div>
        <div class="metric-pill"><div class="val">{demo_df["Turbidity"].mean():.2f}</div><div class="lbl">Avg Turbidity</div></div>
        <div class="metric-pill"><div class="val">{demo_df["Solids"].mean():.0f}</div><div class="lbl">Avg TDS</div></div>
    </div>
    </div>
    """, unsafe_allow_html=True)


# ─── AI TAB ───────────────────────────────────────────────────────────────────
def render_ai():
    st.markdown("""
    <div class="aq-wrap section">
        <p class="section-tag">Intelligent Assistant</p>
        <h2 class="section-title">AI Water Quality Advisor</h2>
        <p class="section-lead">Ask anything about water quality, parameters, health risks, or treatment methods. Powered by Claude.</p>
    </div>
    """, unsafe_allow_html=True)

    # Render chat history
    chat_html = ""
    for msg in st.session_state.ai_history:
        if msg["role"] == "user":
            chat_html += f"""
            <div class="ai-msg-user">
                <div class="ai-avatar ai-avatar-usr">👤</div>
                <div class="ai-bubble ai-bubble-usr">{msg['content']}</div>
            </div>"""
        else:
            chat_html += f"""
            <div class="ai-msg-bot">
                <div class="ai-avatar ai-avatar-bot">💧</div>
                <div class="ai-bubble ai-bubble-bot">{msg['content']}</div>
            </div>"""

    if chat_html:
        st.markdown(f"""
        <div class="aq-wrap" style="padding:0 clamp(16px,5vw,80px);">
        <div style="background:rgba(0,0,0,.2);border:1px solid rgba(0,180,255,.1);
                    border-radius:20px;padding:28px;margin-bottom:24px;max-height:500px;overflow-y:auto;">
            {chat_html}
        </div></div>""", unsafe_allow_html=True)

    # Suggested questions
    st.markdown('<div class="aq-wrap" style="padding:0 clamp(16px,5vw,80px);">', unsafe_allow_html=True)
    suggestions = [
        "What pH is safe for drinking water?",
        "How does turbidity affect water quality?",
        "What are trihalomethanes and why are they harmful?",
        "How can high TDS be reduced?",
    ]
    cols = st.columns(len(suggestions))
    for col, q in zip(cols, suggestions):
        with col:
            if st.button(q, key=f"sug_{q[:20]}"):
                st.session_state.ai_history.append({"role":"user","content":q})
                response = get_ai_response(q)
                st.session_state.ai_history.append({"role":"assistant","content":response})
                st.rerun()

    user_input = st.text_input("Ask about water quality…", key="ai_input",
                               placeholder="e.g. What causes high turbidity?")
    if st.button("Send Message 🚀", use_container_width=True) and user_input.strip():
        st.session_state.ai_history.append({"role":"user","content":user_input})
        with st.spinner("Thinking…"):
            response = get_ai_response(user_input)
        st.session_state.ai_history.append({"role":"assistant","content":response})
        st.rerun()

    if st.button("🗑 Clear Chat"):
        st.session_state.ai_history = []
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def get_ai_response(question: str) -> str:
    """Call Anthropic API with water quality system prompt."""
    try:
        import requests, json
        system_prompt = (
            "You are AquaGuard AI, an expert water quality scientist and public health advisor. "
            "Answer questions about water quality parameters (pH, TDS, turbidity, chloramines, "
            "sulfate, conductivity, organic carbon, trihalomethanes, hardness), WHO guidelines, "
            "health risks, treatment methods, and potability assessment. "
            "Keep answers clear, concise (3-5 sentences), and scientifically accurate. "
            "Use emojis sparingly to aid readability."
        )
        messages = [{"role":"user","content":question}]
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":400,
                  "system":system_prompt,"messages":messages},
            timeout=20
        )
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        return (
            "💧 I'm AquaGuard AI! I can help you understand water quality parameters, "
            "WHO guidelines, health risks, and treatment methods. "
            f"(Note: Connect your Anthropic API key to enable live responses. Error: {e})"
        )


# ─── WHO COMPLIANCE TAB ───────────────────────────────────────────────────────
def render_who():
    st.markdown("""
    <div class="aq-wrap section">
        <p class="section-tag">Regulatory Standards</p>
        <h2 class="section-title">WHO Compliance Check</h2>
        <p class="section-lead">Enter your sample readings and see an instant compliance report against WHO drinking water quality guidelines.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="aq-wrap" style="padding:0 clamp(16px,5vw,80px) 24px;">', unsafe_allow_html=True)

    # Input row
    col1, col2, col3 = st.columns(3)
    with col1:
        w_ph    = st.number_input("pH",                 min_value=0.0,  max_value=14.0,  value=7.2,   step=0.01, key="w_ph")
        w_hard  = st.number_input("Hardness (mg/L)",    min_value=0.0,  max_value=1000.0,value=180.0, step=1.0,  key="w_hard")
        w_tds   = st.number_input("TDS (mg/L)",         min_value=0.0,  max_value=5000.0,value=310.0, step=1.0,  key="w_tds")
    with col2:
        w_chlor = st.number_input("Chloramines (mg/L)", min_value=0.0,  max_value=20.0,  value=3.5,   step=0.01, key="w_chlor")
        w_sulf  = st.number_input("Sulfate (mg/L)",     min_value=0.0,  max_value=500.0, value=240.0, step=0.1,  key="w_sulf")
        w_cond  = st.number_input("Conductivity (µS/cm)",min_value=0.0, max_value=1000.0,value=380.0, step=1.0,  key="w_cond")
    with col3:
        w_oc    = st.number_input("Organic Carbon (mg/L)",min_value=0.0,max_value=30.0,  value=1.8,   step=0.01, key="w_oc")
        w_thm   = st.number_input("Trihalomethanes (µg/L)",min_value=0.0,max_value=130.0,value=75.0,  step=0.1,  key="w_thm")
        w_turb  = st.number_input("Turbidity (NTU)",    min_value=0.0,  max_value=10.0,  value=0.8,   step=0.01, key="w_turb")

    sample = {
        "pH":               (w_ph,    (6.5, 8.5),  lambda v,lo,hi: lo<=v<=hi),
        "Hardness":         (w_hard,  (None, 500), lambda v,lo,hi: v<=hi),
        "TDS":              (w_tds,   (None, 500), lambda v,lo,hi: v<=hi),
        "Chloramines":      (w_chlor, (None, 4),   lambda v,lo,hi: v<=hi),
        "Sulfate":          (w_sulf,  (None, 250), lambda v,lo,hi: v<=hi),
        "Conductivity":     (w_cond,  (None, 400), lambda v,lo,hi: v<=hi),
        "Organic Carbon":   (w_oc,    (None, 2),   lambda v,lo,hi: v<=hi),
        "Trihalomethanes":  (w_thm,   (None, 80),  lambda v,lo,hi: v<=hi),
        "Turbidity":        (w_turb,  (None, 1),   lambda v,lo,hi: v<=hi),
    }

    rows_html = ""
    pass_count = 0
    for param, (val, limits, check) in sample.items():
        lo, hi = limits
        passed = check(val, lo, hi)
        if passed: pass_count += 1
        limit_str = f"{lo}–{hi}" if lo else f"≤ {hi}"
        status    = '<span class="badge badge-ok">✓ PASS</span>' if passed else '<span class="badge badge-bad">✗ FAIL</span>'
        val_cls   = "who-ok" if passed else "who-bad"
        unit_map  = {"pH":"—","Hardness":"mg/L","TDS":"mg/L","Chloramines":"mg/L",
                     "Sulfate":"mg/L","Conductivity":"µS/cm","Organic Carbon":"mg/L",
                     "Trihalomethanes":"µg/L","Turbidity":"NTU"}
        rows_html += f"""
        <tr>
            <td><strong style="color:#d4eaf7">{param}</strong></td>
            <td class="{val_cls}">{val} {unit_map[param]}</td>
            <td style="color:#7db8d4">{limit_str} {unit_map[param]}</td>
            <td>{status}</td>
        </tr>"""

    overall_pct = pass_count / len(sample) * 100
    overall_cls = "badge-ok" if overall_pct == 100 else ("badge-warn" if overall_pct >= 70 else "badge-bad")
    overall_lbl = "FULLY COMPLIANT" if overall_pct==100 else ("PARTIALLY COMPLIANT" if overall_pct>=70 else "NON-COMPLIANT")

    st.markdown(f"""
    <div style="background:rgba(0,180,255,.04);border:1px solid rgba(0,180,255,.15);
                border-radius:20px;padding:32px;margin-top:12px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:16px;">
            <p style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:#d4eaf7;">
                WHO Compliance Report
            </p>
            <span style="font-family:Syne,sans-serif;font-size:13px;font-weight:700;
                         padding:8px 20px;border-radius:100px;"
                  class="badge {overall_cls}">
                {overall_lbl} — {pass_count}/{len(sample)} parameters
            </span>
        </div>
        <table class="who-table">
            <thead><tr>
                <th>Parameter</th><th>Your Value</th><th>WHO Guideline</th><th>Status</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # Score gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_pct,
        number={"suffix":"%","font":{"size":40,"color":"#00d4ff"}},
        title={"text":"Compliance Score","font":{"size":14,"color":"#7db8d4"}},
        gauge={
            "axis":{"range":[0,100],"tickcolor":"#3d6278"},
            "bar":{"color":"#00ff96" if overall_pct==100 else ("#ffcc00" if overall_pct>=70 else "#ff5555")},
            "bgcolor":"rgba(0,0,0,0)","bordercolor":"rgba(0,180,255,.2)",
            "steps":[{"range":[0,70],"color":"rgba(255,80,80,.08)"},
                     {"range":[70,90],"color":"rgba(255,200,0,.08)"},
                     {"range":[90,100],"color":"rgba(0,255,150,.08)"}]
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color="#d4eaf7",height=220,margin=dict(t=20,b=0,l=20,r=20)
    )
    st.plotly_chart(fig, use_container_width=True, key="who_gauge")
    st.markdown("</div>", unsafe_allow_html=True)


# ─── NAVIGATION BAR ───────────────────────────────────────────────────────────
TABS = [
    ("home",     "🏠", "Home"),
    ("predict",  "🔬", "Prediction"),
    ("analysis", "📊", "Analysis"),
    ("ai",       "🤖", "AI Advisor"),
    ("who",      "🌍", "WHO Compliance"),
]

def render_nav():
    active = st.session_state.active_tab
    nav_html = '<nav class="tab-nav">'
    for tid, icon, label in TABS:
        cls = "tab-btn active" if tid == active else "tab-btn"
        nav_html += f'<button class="{cls}" onclick="void(0)"><span class="tab-icon">{icon}</span>{label}</button>'
    nav_html += '</nav>'
    st.markdown(nav_html, unsafe_allow_html=True)

    # Actual clickable buttons hidden behind nav
    cols = st.columns(len(TABS))
    for col, (tid, icon, label) in zip(cols, TABS):
        with col:
            if st.button(f"{icon} {label}", key=f"nav_{tid}", use_container_width=True,
                        help=f"Go to {label}"):
                nav(tid)
                st.rerun()

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    render_nav()

    active = st.session_state.active_tab
    if   active == "home":     render_hero()
    elif active == "predict":  render_prediction()
    elif active == "analysis": render_analysis()
    elif active == "ai":       render_ai()
    elif active == "who":      render_who()

    st.markdown("""
    <div class="footer">
        Built with <span>💧 AquaGuard</span> · Powered by Machine Learning &amp; Claude AI ·
        Data guidelines sourced from <span>WHO</span> drinking water standards
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()