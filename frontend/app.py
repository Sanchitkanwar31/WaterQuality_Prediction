import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import folium
from streamlit_folium import st_folium

# ================= CONFIG =================
st.set_page_config(page_title="Water Quality AI", layout="wide")
API_URL = "https://water-quality-api-j65z.onrender.com"

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

# ================= HEATMAP =================
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
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "name": row["name"],
                    "id": row["id"],
                    "wqi": wqi
                })
        except:
            pass

    return pd.DataFrame(data)

heatmap_df = load_heatmap()

# ================= TITLE =================
st.title("💧 Water Quality Intelligence System")

# ================= MAP =================
st.subheader("🌍 Interactive Water Map")

m = folium.Map(location=[22.5, 78.9], zoom_start=5)

for _, row in heatmap_df.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=8,
        color=get_color(row["wqi"]),
        fill=True,
        fill_color=get_color(row["wqi"]),
        popup=f"{row['name']} | WQI: {row['wqi']:.1f}"
    ).add_to(m)

map_data = st_folium(m, width=900, height=500)

# ================= SESSION =================
if "station" not in st.session_state:
    st.session_state.station = str(stations_df.iloc[0]["id"])

# click handling
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    nearest = get_nearest_station(lat, lon)
    st.session_state.station = str(nearest["id"])

    st.success(f"Selected: {nearest['name']} ({nearest['city']})")

selected_station = st.session_state.station

# ================= SELECT =================
selected_label = st.selectbox(
    "Select Station",
    stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1)
)

selected_row = stations_df[
    stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1) == selected_label
].iloc[0]

if st.button("Use Station"):
    st.session_state.station = str(selected_row["id"])

row = stations_df[stations_df["id"] == int(selected_station)].iloc[0]

st.markdown(f"""
📍 **{row['city']}, {row['state']}**  
🌊 {row['river']}
""")

# ================= TABS =================
tabs = st.tabs(["📊 Predict", "📈 Analysis", "🤖 AI Insight", "📚 WHO"])

# ================= PREDICT =================
with tabs[0]:

    year = st.slider("Year", 2010, 2025, 2022)

    if st.button("Run Prediction"):
        res = requests.post(f"{API_URL}/predict", json={
            "year": year,
            "station_id": selected_station
        })

        if res.status_code == 200:
            data = res.json()
            pred = data["prediction"]

            st.session_state["pred"] = pred

            # TABLE
            df = pd.DataFrame(pred.items(), columns=["Pollutant", "Value"])
            st.dataframe(df)

            # BAR
            st.plotly_chart(px.bar(df, x="Pollutant", y="Value"))

            # SCORE
            score, comp = compute_quality(pred)
            st.metric("Quality Score", f"{score:.2f}/100")

            comp_df = pd.DataFrame({
                "Pollutant": comp.keys(),
                "Safe": comp.values()
            })
            st.dataframe(comp_df)

        else:
            st.error("API error")

# ================= ANALYSIS =================
with tabs[1]:

    st.subheader("Trend")

    if st.button("Show Trend"):
        years = range(2015, 2025)
        trend = []

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
        st.plotly_chart(px.line(df, x="Year", y="WQI", markers=True))

# ================= AI =================
with tabs[2]:

    if "pred" in st.session_state:

        query = st.selectbox(
    "Select Insight Type",
    ["health", "treatment", "explanation", "trend"])
    

    if st.button("Generate AI Insight"):

        res = requests.post(
            f"{API_URL}/ai-insight",
            json={
                "prediction": st.session_state["pred"],
                "type": query
            }
        )

        if res.status_code == 200:
            st.success(res.json()["insight"])

# ================= WHO =================
with tabs[3]:

    if "pred" in st.session_state:
        pred = st.session_state["pred"]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=list(pred.values()),
            theta=list(pred.keys()),
            fill='toself',
            name='Your Water'
        ))

        fig.add_trace(go.Scatterpolar(
            r=list(WHO_LIMITS.values()),
            theta=list(WHO_LIMITS.keys()),
            fill='toself',
            name='WHO Limits'
        ))

        st.plotly_chart(fig)
    else:
        st.info("Run prediction first")