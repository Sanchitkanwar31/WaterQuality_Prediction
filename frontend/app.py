import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import folium
from streamlit_folium import st_folium

# ================= CONFIG =================
st.set_page_config(page_title="Water Quality AI", layout="wide", page_icon="💧")

API_URL = "https://water-quality-api-j65z.onrender.com"

# ================= GLOBAL CSS =================
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg:        #04111f;
    --surface:   rgba(255,255,255,0.035);
    --border:    rgba(0,180,255,0.13);
    --border-hi: rgba(0,220,255,0.35);
    --accent:    #00cfff;
    --accent2:   #00ffbb;
    --text:      #cde8f5;
    --muted:     #4d7a94;
    --danger:    #ff4e6a;
    --warn:      #ffb74d;
    --ok:        #00e5a0;
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background: var(--bg) !important;
    font-family: 'Outfit', sans-serif !important;
    color: var(--text) !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container          { padding: 0 !important; max-width: 100% !important; }
section.main > div        { padding-top: 0 !important; }

/* ── Animated background ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 70% 55% at 15% 25%, rgba(0,140,255,.11) 0%, transparent 65%),
        radial-gradient(ellipse 55% 45% at 85% 75%, rgba(0,255,180,.08) 0%, transparent 65%),
        radial-gradient(ellipse 40% 35% at 55%  5%, rgba(0,60,140,.18)  0%, transparent 60%);
    animation: bgPulse 14s ease-in-out infinite alternate;
}
@keyframes bgPulse {
    0%   { opacity: .8; }
    100% { opacity: 1;  }
}

/* ── Particle dots ── */
[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
        radial-gradient(circle, rgba(0,200,255,.3) 1px, transparent 1px),
        radial-gradient(circle, rgba(0,255,180,.2) 1px, transparent 1px);
    background-size: 55px 55px, 85px 85px;
    background-position: 0 0, 27px 27px;
    animation: drift 22s linear infinite;
    opacity: .35;
}
@keyframes drift {
    0%   { transform: translateY(0); }
    100% { transform: translateY(-55px); }
}

/* Ensure content sits above bg layers */
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
.element-container, .stTabs, iframe {
    position: relative; z-index: 1;
}

/* ══════════════════════════════════
   HERO
══════════════════════════════════ */
.hero {
    padding: 52px clamp(20px,6vw,90px) 38px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 28px; flex-wrap: wrap;
    background: linear-gradient(180deg, rgba(0,120,255,.06) 0%, transparent 100%);
    position: relative; overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute; right: -60px; top: -60px;
    width: 380px; height: 380px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,200,255,.07) 0%, transparent 70%);
    pointer-events: none;
}
.hero-icon {
    font-size: 60px; line-height: 1;
    animation: dropFloat 4s ease-in-out infinite;
    filter: drop-shadow(0 0 24px rgba(0,200,255,.55));
    flex-shrink: 0;
}
@keyframes dropFloat {
    0%,100% { transform: translateY(0)     scale(1);    }
    50%      { transform: translateY(-12px) scale(1.07); }
}
.hero-text h1 {
    font-size: clamp(26px,4vw,50px);
    font-weight: 800; letter-spacing: -1.5px; line-height: 1.08;
    background: linear-gradient(120deg, #ffffff 0%, var(--accent) 55%, var(--accent2) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0 0 8px;
}
.hero-text p {
    color: var(--muted); font-size: 15px; font-weight: 400;
    line-height: 1.65; max-width: 520px; margin: 0;
}
.hero-pills {
    display: flex; gap: 9px; flex-wrap: wrap; margin-top: 18px;
}
.pill {
    background: rgba(0,200,255,.08);
    border: 1px solid rgba(0,200,255,.2);
    border-radius: 100px; padding: 5px 14px;
    font-size: 12px; font-weight: 600; letter-spacing: .4px;
    color: var(--accent);
}

/* ══════════════════════════════════
   MAP SECTION HEADER
══════════════════════════════════ */
.map-section-header {
    padding: 28px clamp(20px,6vw,90px) 16px;
}
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: var(--accent2); margin-bottom: 6px;
}
.map-card {
    border: 1px solid var(--border);
    border-radius: 18px; overflow: hidden;
    box-shadow: 0 8px 40px rgba(0,0,0,.4);
}

/* ══════════════════════════════════
   STATION BAR
══════════════════════════════════ */
.station-bar {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    padding: 14px clamp(20px,6vw,90px);
    background: rgba(0,0,0,.28);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
    backdrop-filter: blur(18px);
}
.station-badge {
    display: flex; align-items: center; gap: 10px;
    background: rgba(0,200,255,.06);
    border: 1px solid var(--border-hi);
    border-radius: 12px; padding: 10px 16px;
    font-size: 14px;
}
.sbadge-label { color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
.sbadge-value { color: #fff; font-weight: 700; font-size: 15px; margin-top: 2px; }
.sbadge-sub   { color: var(--accent2); font-size: 12px; margin-top: 1px; }

/* ══════════════════════════════════
   TABS
══════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(0,0,0,.3) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 clamp(20px,6vw,90px) !important;
    gap: 0 !important;
    backdrop-filter: blur(14px);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 16px 26px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    letter-spacing: .6px !important; text-transform: uppercase !important;
    transition: all .22s ease !important;
}
.stTabs [data-baseweb="tab"]:hover  { color: var(--accent) !important; }
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 34px clamp(20px,6vw,90px) 56px !important;
    background: transparent !important;
}

/* ══════════════════════════════════
   WIDGETS
══════════════════════════════════ */
label,
.stSlider label,
.stSelectbox label,
[data-testid="stWidgetLabel"] p {
    font-family: 'Outfit', sans-serif !important;
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: .9px !important; text-transform: uppercase !important;
    color: var(--muted) !important;
}
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"]   input {
    background: rgba(0,180,255,.05) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    transition: border-color .2s !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"]   input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,200,255,.12) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: rgba(0,180,255,.05) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: #fff !important;
}
[data-testid="stSlider"] > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
}
[data-testid="stSlider"] [role="slider"] {
    background: var(--accent) !important;
    border: 2px solid #fff !important;
    box-shadow: 0 0 12px rgba(0,200,255,.5) !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #04111f !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 12px 30px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important; font-size: 14px !important;
    box-shadow: 0 0 22px rgba(0,200,255,.22) !important;
    transition: all .22s ease !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 0 42px rgba(0,200,255,.42) !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important; overflow: hidden;
}
[data-testid="stDataFrame"] th {
    background: rgba(0,180,255,.1) !important;
    color: var(--accent) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 11px !important; letter-spacing: .8px !important;
    text-transform: uppercase !important;
}
[data-testid="stDataFrame"] td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important; color: var(--text) !important;
}
[data-testid="stMetric"] {
    background: rgba(0,180,255,.06) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important; padding: 20px 24px !important;
}
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: 12px !important; }
[data-testid="stMetricValue"]   { color: var(--accent) !important; font-size: 32px !important; font-weight: 800 !important; }
[data-testid="stAlert"]         { border-radius: 12px !important; font-family: 'Outfit', sans-serif !important; }
div[data-testid="stAlert"][kind="success"] {
    background: rgba(0,229,160,.08) !important;
    border-color: var(--ok) !important; color: var(--ok) !important;
}
h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important; letter-spacing: -.4px !important;
    color: #fff !important;
}
hr { border-color: var(--border) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text); }

/* ── Chat bubbles ── */
.chat-user { display:flex; justify-content:flex-end; margin-bottom:14px; }
.chat-ai   { display:flex; justify-content:flex-start; margin-bottom:14px; }
.bubble { max-width:75%; padding:12px 18px; border-radius:18px; font-size:14px; line-height:1.65; }
.bubble-user {
    background: rgba(0,200,255,.14);
    border: 1px solid rgba(0,200,255,.25);
    border-top-right-radius: 4px; color: #fff; text-align: right;
}
.bubble-ai {
    background: rgba(255,255,255,.05);
    border: 1px solid var(--border);
    border-top-left-radius: 4px; color: var(--text);
}
.chat-lbl      { font-size:10px; font-weight:700; letter-spacing:1px; text-transform:uppercase; margin-bottom:5px; }
.chat-lbl-ai   { color: var(--accent2); }
.chat-lbl-user { color: var(--accent); text-align:right; }

/* ── WHO info box ── */
.who-info {
    background: rgba(0,180,255,.05);
    border: 1px solid var(--border);
    border-radius: 14px; padding: 18px 22px; margin-bottom: 22px;
    font-size: 14px; color: var(--muted); line-height: 1.7;
}
.who-info strong { color: var(--text); }

/* ── WQI Legend box ── */
.legend-box {
    background: rgba(0,180,255,.05);
    border: 1px solid var(--border);
    border-radius: 14px; padding: 18px 20px;
    display: flex; flex-direction: column; gap: 10px;
}
.legend-item { display:flex; align-items:center; gap:10px; font-size:13px; color:var(--text); }
.dot { width:11px;height:11px;border-radius:50%;flex-shrink:0; }
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stations_path = os.path.join(BASE_DIR, "data", "stations.csv")

if not os.path.exists(stations_path):
    st.error("stations.csv missing")
    st.stop()

stations_df = pd.read_csv(stations_path)

# ================= WHO LIMITS =================
WHO_LIMITS = {
    "NH4": 0.5, "BSK5": 3, "Suspended": 25,
    "O2": 4, "NO3": 50, "NO2": 3,
    "SO4": 250, "PO4": 0.5, "CL": 250
}

# ================= UTILS =================
def get_color(wqi):
    return "green" if wqi < 50 else "orange" if wqi < 100 else "red"

def get_nearest_station(lat, lon):
    df = stations_df.copy()
    df["dist"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2) ** 0.5
    return df.loc[df["dist"].idxmin()]

def compute_quality(pred):
    score = 0
    compliance = {}
    for k, v in pred.items():
        limit = WHO_LIMITS[k]
        ok = v >= limit if k == "O2" else v <= limit
        compliance[k] = ok
        score += int(ok)
    return (score / len(pred)) * 100, compliance

def generate_ai(pred):
    if pred["NO3"] > 50:
        return "⚠ High nitrate → harmful for infants."
    if pred["BSK5"] > 3:
        return "⚠ Organic pollution detected."
    return "✅ Water is within acceptable limits."

# ================= HEATMAP DATA =================
@st.cache_data
def load_heatmap():
    data = []
    for _, row in stations_df.iterrows():
        try:
            res = requests.post(
                f"{API_URL}/predict",
                json={"year": 2022, "station_id": str(row["id"])},
                timeout=3
            )
            if res.status_code == 200:
                wqi = res.json()["wqi_score"]
                data.append({
                    "lat": row["lat"], "lon": row["lon"],
                    "name": row["name"], "id": row["id"], "wqi": wqi
                })
        except:
            pass
    return pd.DataFrame(data)

heatmap_df = load_heatmap()

# ═══════════════════════════════════════
#  HERO
# ═══════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-icon">💧</div>
    <div class="hero-text">
        <h1>Water Quality Intelligence</h1>
        <p>
            Select a monitoring station on the map, run ML predictions, explore pollutant
            trends, get AI-powered health insights, and check WHO compliance — all in one place.
        </p>
        <div class="hero-pills">
            <span class="pill">🗺 Live Station Map</span>
            <span class="pill">🔬 ML Prediction</span>
            <span class="pill">📈 Trend Analysis</span>
            <span class="pill">🤖 AI Insights</span>
            <span class="pill">🌍 WHO Standards</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
#  MAP
# ═══════════════════════════════════════
st.markdown("""
<div class="map-section-header">
    <p class="section-label">🗺 Station Network — click a station on the map</p>
</div>
""", unsafe_allow_html=True)

pad_l, pad_r = st.columns([20, 1])          # full-width padding trick
with pad_l:
    col_map, col_side = st.columns([3, 1])

    with col_map:
        st.markdown('<div class="map-card">', unsafe_allow_html=True)
        m = folium.Map(
            location=[22.5, 78.9], zoom_start=5,
            tiles="CartoDB dark_matter"
        )
        for _, row in heatmap_df.iterrows():
            color = get_color(row["wqi"])
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=9, color=color,
                fill=True, fill_color=color, fill_opacity=0.75, weight=2,
                popup=folium.Popup(
                    f"<b style='font-family:sans-serif'>{row['name']}</b><br>WQI: <b>{row['wqi']:.1f}</b>",
                    max_width=160
                )
            ).add_to(m)
        map_data = st_folium(m, width="100%", height=440)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # ── Station selector panel ──
        st.markdown("""
        <div style="background:rgba(0,180,255,.05);border:1px solid rgba(0,180,255,.14);
                    border-radius:16px;padding:20px 18px 16px;">
            <p class="section-label" style="margin-bottom:14px;">Select Station</p>
        """, unsafe_allow_html=True)

        if "station" not in st.session_state:
            st.session_state.station = str(stations_df.iloc[0]["id"])

        # click handling — UNCHANGED
        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            nearest = get_nearest_station(lat, lon)
            st.session_state.station = str(nearest["id"])
            st.success(f"📍 {nearest['name']} ({nearest['city']})")

        selected_station = st.session_state.station

        selected_label = st.selectbox(
            "Station",
            stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1),
            label_visibility="collapsed"
        )
        selected_row = stations_df[
            stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1) == selected_label
        ].iloc[0]

        if st.button("📍 Use This Station", use_container_width=True):
            st.session_state.station = str(selected_row["id"])

        # WQI legend
        st.markdown("""
        <div class="legend-box" style="margin-top:18px;">
            <p class="section-label" style="margin:0 0 6px;">WQI Legend</p>
            <div class="legend-item"><span class="dot" style="background:#00e676"></span>Good — WQI &lt; 50</div>
            <div class="legend-item"><span class="dot" style="background:#ffb74d"></span>Moderate — 50–100</div>
            <div class="legend-item"><span class="dot" style="background:#ff4e6a"></span>Poor — WQI &gt; 100</div>
        </div>
        </div>
        """, unsafe_allow_html=True)

# ── Active station info bar ──
row = stations_df[stations_df["id"] == int(selected_station)].iloc[0]
st.markdown(f"""
<div class="station-bar">
    <div class="station-badge">
        <span style="font-size:20px;">📍</span>
        <div>
            <div class="sbadge-label">Active Station</div>
            <div class="sbadge-value">{row['name']}, {row['city']}</div>
            <div class="sbadge-sub">🌊 {row['river']} · {row['state']}</div>
        </div>
    </div>
    <div class="station-badge">
        <span style="font-size:20px;">🌐</span>
        <div>
            <div class="sbadge-label">Coordinates</div>
            <div class="sbadge-value">{row['lat']:.4f}°N, {row['lon']:.4f}°E</div>
            <div class="sbadge-sub">Station ID: {row['id']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
#  TABS
# ═══════════════════════════════════════
tabs = st.tabs(["📊 Predict", "📈 Analysis", "🤖 AI Insight", "📚 WHO Compliance"])

# ───────────────────────────────────────
#  TAB 0 — PREDICT  (logic 100% original)
# ───────────────────────────────────────
with tabs[0]:
    st.markdown("""
    <p style="color:#4d7a94;font-size:14px;margin-bottom:24px;line-height:1.7;">
        Choose a year and run the ML model for the selected station.
        Results include predicted pollutant concentrations and a Water Quality Index score.
    </p>
    """, unsafe_allow_html=True)

    year = st.slider("Year", 2010, 2025, 2022)

    if st.button("🔬 Run Prediction"):
        res = requests.post(f"{API_URL}/predict", json={
            "year": year,
            "station_id": selected_station
        })

        if res.status_code == 200:
            data = res.json()
            pred = data["prediction"]
            st.session_state["pred"] = pred

            st.markdown("---")
            st.markdown("#### 🧪 Pollutant Concentrations")

            # Original dataframe — with Status column added for clarity
            df = pd.DataFrame(pred.items(), columns=["Pollutant", "Value"])
            df["WHO Limit"] = df["Pollutant"].map(WHO_LIMITS)
            df["Status"] = df.apply(
                lambda r: "✅ OK" if (
                    r["Value"] >= r["WHO Limit"] if r["Pollutant"] == "O2"
                    else r["Value"] <= r["WHO Limit"]
                ) else "❌ Exceeds",
                axis=1
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Original bar chart — styled colours
            bar_df = pd.DataFrame(pred.items(), columns=["Pollutant", "Value"])
            fig = px.bar(
                bar_df, x="Pollutant", y="Value",
                color="Value",
                color_continuous_scale=[[0,"#00ffbb"],[0.5,"#00cfff"],[1,"#ff4e6a"]],
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cde8f5", coloraxis_showscale=False,
                margin=dict(t=10, b=20)
            )
            fig.update_xaxes(gridcolor="rgba(0,180,255,.08)")
            fig.update_yaxes(gridcolor="rgba(0,180,255,.08)")
            st.plotly_chart(fig, use_container_width=True)

            # Original quality score + compliance
            score, comp = compute_quality(pred)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric("Quality Score", f"{score:.2f}/100")
            with col_b:
                comp_df = pd.DataFrame({
                    "Pollutant": list(comp.keys()),
                    "Safe": list(comp.values())
                })
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
        else:
            st.error("API error")

# ───────────────────────────────────────
#  TAB 1 — ANALYSIS  (logic 100% original)
# ───────────────────────────────────────
with tabs[1]:
    st.markdown("""
    <p style="color:#4d7a94;font-size:14px;margin-bottom:24px;line-height:1.7;">
        Visualise the Water Quality Index trend for the selected station from 2015 to 2024.
    </p>
    """, unsafe_allow_html=True)

    if st.button("Show Trend"):
        years = range(2015, 2025)
        trend = []

        with st.spinner("Fetching historical predictions…"):
            for y in years:
                try:
                    res = requests.post(
                        f"{API_URL}/predict",
                        json={"year": y, "station_id": selected_station},
                        timeout=3
                    )
                    if res.status_code == 200:
                        trend.append({"Year": y, "WQI": res.json()["wqi_score"]})
                except:
                    pass

        df = pd.DataFrame(trend)
        if not df.empty:
            fig = px.line(df, x="Year", y="WQI", markers=True,
                          template="plotly_dark", line_shape="spline",
                          color_discrete_sequence=["#00cfff"])
            fig.update_traces(
                marker=dict(size=9, color="#00ffbb", line=dict(width=2, color="#00cfff")),
                line=dict(width=3)
            )
            fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,78,106,.5)",
                          annotation_text="Poor threshold (100)",
                          annotation_font_color="#ff4e6a", annotation_position="top left")
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,183,77,.4)",
                          annotation_text="Moderate threshold (50)",
                          annotation_font_color="#ffb74d", annotation_position="top left")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#cde8f5",
                xaxis=dict(gridcolor="rgba(0,180,255,.08)", tickmode="linear"),
                yaxis=dict(gridcolor="rgba(0,180,255,.08)", title="WQI Score"),
                margin=dict(t=30, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No trend data returned from API.")

# ───────────────────────────────────────
#  TAB 2 — AI INSIGHT  (logic 100% original)
# ───────────────────────────────────────
with tabs[2]:
    st.markdown("""
    <p style="color:#4d7a94;font-size:14px;margin-bottom:24px;line-height:1.7;">
        Ask the AI assistant anything about the current water quality prediction.
        Run a prediction first to unlock context-aware responses.
    </p>
    """, unsafe_allow_html=True)

    if "pred" not in st.session_state:
        st.info("Run a prediction in the **📊 Predict** tab first to enable AI insights.")
        st.stop()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Suggested prompts — original
    st.markdown("##### 💡 Quick Questions")
    col1, col2, col3 = st.columns(3)
    if col1.button("Health Risk",  use_container_width=True):
        st.session_state.user_input = "Explain health risks"
    if col2.button("Treatment",    use_container_width=True):
        st.session_state.user_input = "Suggest treatment methods"
    if col3.button("Explain Data", use_container_width=True):
        st.session_state.user_input = "Explain this water quality in simple terms"

    user_input = st.text_input(
        "Ask anything about this water",
        value=st.session_state.get("user_input", ""),
        placeholder="e.g. Is this safe to drink? What should I do?"
    )

    if st.button("Send") and user_input:
        st.session_state.chat_history.append(("user", user_input))
        with st.spinner("AI is thinking… 🤖"):
            try:
                res = requests.post(
                    f"{API_URL}/ai-insight",
                    json={"prediction": st.session_state["pred"], "type": user_input}
                )
                ai_reply = res.json()["insight"] if res.status_code == 200 else "AI service error."
            except Exception as e:
                ai_reply = f"Error: {e}"
        st.session_state.chat_history.append(("ai", ai_reply))
        st.session_state.user_input = ""

    # Chat display — styled bubbles
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("##### 💬 Conversation")
        for role, msg in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <div>
                        <div class="chat-lbl chat-lbl-user">You</div>
                        <div class="bubble bubble-user">{msg}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-ai">
                    <div>
                        <div class="chat-lbl chat-lbl-ai">🤖 AI</div>
                        <div class="bubble bubble-ai">{msg}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

# ───────────────────────────────────────
#  TAB 3 — WHO COMPLIANCE  (logic 100% original)
# ───────────────────────────────────────
with tabs[3]:
    if "pred" in st.session_state:
        pred = st.session_state["pred"]

        st.markdown("""
        <div class="who-info">
            <strong>WHO Drinking Water Guidelines.</strong>
            The radar chart overlays your station's predicted pollutant levels against the
            official WHO maximum permissible limits. Areas where your sample extends
            <em>beyond</em> the WHO boundary indicate non-compliance.
        </div>
        """, unsafe_allow_html=True)

        # ── original radar traces, styled layout ──
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(pred.values()),
            theta=list(pred.keys()),
            fill='toself',
            name='Your Water',
            fillcolor='rgba(0,207,255,0.12)',
            line=dict(color='#00cfff', width=2)
        ))
        fig.add_trace(go.Scatterpolar(
            r=list(WHO_LIMITS.values()),
            theta=list(WHO_LIMITS.keys()),
            fill='toself',
            name='WHO Limits',
            fillcolor='rgba(255,78,106,0.08)',
            line=dict(color='#ff4e6a', width=2, dash='dot')
        ))
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, gridcolor='rgba(0,180,255,.12)',
                                tickfont=dict(color='#4d7a94', size=10)),
                angularaxis=dict(gridcolor='rgba(0,180,255,.12)',
                                 tickfont=dict(color='#cde8f5', size=12))
            ),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#cde8f5',
            legend=dict(bgcolor='rgba(0,0,0,.3)', bordercolor='rgba(0,180,255,.2)',
                        borderwidth=1, font=dict(size=13)),
            height=480, margin=dict(t=30, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Compliance summary table
        _, comp = compute_quality(pred)
        rows_html = "".join([
            f"<tr>"
            f"<td style='padding:10px 16px;color:#cde8f5;font-family:JetBrains Mono,monospace;'>{k}</td>"
            f"<td style='padding:10px 16px;color:#4d7a94;font-family:JetBrains Mono,monospace;'>{WHO_LIMITS[k]}</td>"
            f"<td style='padding:10px 16px;color:#4d7a94;font-family:JetBrains Mono,monospace;'>{pred[k]:.3f}</td>"
            f"<td style='padding:10px 16px;'>{'<span style=\"color:#00e5a0;font-weight:700;\">✅ OK</span>' if v else '<span style=\"color:#ff4e6a;font-weight:700;\">❌ Exceeds</span>'}</td>"
            f"</tr>"
            for k, v in comp.items()
        ])
        st.markdown(f"""
        <table style="width:100%;border-collapse:collapse;margin-top:16px;
                      background:rgba(0,180,255,.04);border:1px solid rgba(0,180,255,.13);
                      border-radius:14px;overflow:hidden;">
            <thead>
                <tr style="background:rgba(0,180,255,.1);">
                    <th style="padding:12px 16px;text-align:left;color:#00cfff;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Pollutant</th>
                    <th style="padding:12px 16px;text-align:left;color:#00cfff;font-size:11px;letter-spacing:1px;text-transform:uppercase;">WHO Limit</th>
                    <th style="padding:12px 16px;text-align:left;color:#00cfff;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Predicted</th>
                    <th style="padding:12px 16px;text-align:left;color:#00cfff;font-size:11px;letter-spacing:1px;text-transform:uppercase;">Status</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)
    else:
        st.info("Run a prediction in the **📊 Predict** tab first to see WHO compliance.")

# ═══════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════
st.markdown("""
<div style="text-align:center;padding:40px 24px;margin-top:40px;
            border-top:1px solid rgba(0,180,255,.1);
            color:#2a5068;font-size:13px;font-family:Outfit,sans-serif;">
    💧 <span style="color:#00cfff;">Water Quality Intelligence System</span> ·
    ML predictions via <span style="color:#00cfff;">FastAPI</span> ·
    Guidelines from <span style="color:#00cfff;">WHO</span> drinking water standards
</div>
""", unsafe_allow_html=True)