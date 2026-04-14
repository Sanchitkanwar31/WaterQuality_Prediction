import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import folium
from streamlit_folium import st_folium

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Water Quality AI", layout="wide")

API_URL = "https://water-quality-api-j65z.onrender.com"

# =========================
# LOAD DATA
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stations_path = os.path.join(BASE_DIR, "data", "stations.csv")

if not os.path.exists(stations_path):
    st.error(f"stations.csv not found at {stations_path}")
    st.stop()

stations_df = pd.read_csv(stations_path)

# =========================
# UTILS
# =========================
def get_color(wqi):
    if wqi < 50:
        return "green"
    elif wqi < 100:
        return "orange"
    else:
        return "red"

def get_nearest_station(lat, lon):
    df = stations_df.copy()
    df["distance"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2) ** 0.5
    return df.loc[df["distance"].idxmin()]

# =========================
# LOAD HEATMAP DATA
# =========================
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
            continue

    return pd.DataFrame(data)

heatmap_df = load_heatmap()

# =========================
# TITLE
# =========================
st.title("💧 Water Quality Intelligence System")

# =========================
# CLICKABLE MAP
# =========================
st.markdown("## 🌍 Clickable Water Quality Map")

m = folium.Map(location=[22.5, 78.9], zoom_start=5)

for _, row in heatmap_df.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=8,
        color=get_color(row["wqi"]),
        fill=True,
        fill_color=get_color(row["wqi"]),
        popup=f"{row['name']} | WQI: {row['wqi']:.2f}"
    ).add_to(m)

map_data = st_folium(m, width=900, height=500)

# =========================
# SESSION STATE
# =========================
if "selected_station" not in st.session_state:
    st.session_state.selected_station = str(stations_df.iloc[0]["id"])

# Handle click
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    nearest = get_nearest_station(lat, lon)
    st.session_state.selected_station = str(nearest["id"])

    st.success(f"📍 Selected: {nearest['name']} ({nearest['city']})")

selected_station = st.session_state.selected_station

# =========================
# DROPDOWN (SYNCED)
# =========================
selected_label = st.selectbox(
    "Or select station manually",
    stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1)
)

selected_row = stations_df[
    stations_df.apply(lambda x: f"{x['name']} ({x['city']})", axis=1) == selected_label
].iloc[0]

# Override if dropdown used
if st.button("Use Selected Station"):
    st.session_state.selected_station = str(selected_row["id"])
    selected_station = st.session_state.selected_station

# Show details
row = stations_df[stations_df["id"] == int(selected_station)].iloc[0]

st.markdown(f"""
📍 **City:** {row['city']}, {row['state']}  
🌊 **Water Body:** {row['river']}  
""")

st.markdown("---")

# =========================
# MODE SWITCH
# =========================
mode = st.radio(
    "Mode",
    ["📊 Prediction", "🧪 Sensor Analysis"],
    horizontal=True
)

# =========================
# PREDICTION MODE
# =========================
if "Prediction" in mode:

    year = st.number_input("Year", 2000, 2100, 2022)

    if st.button("Predict"):

        payload = {
            "year": int(year),
            "station_id": selected_station
        }

        res = requests.post(f"{API_URL}/predict", json=payload)

        if res.status_code == 200:
            data = res.json()

            prediction = data["prediction"]
            wqi = data["wqi_score"]
            quality = data["quality"]

            color = "green" if wqi < 50 else "orange" if wqi < 100 else "red"

            st.markdown(f"### WQI: :{color}[{wqi:.2f}] ({quality})")

            df = pd.DataFrame({
                "Pollutant": list(prediction.keys()),
                "Value": list(prediction.values())
            })

            st.dataframe(df)

            fig = px.bar(df, x="Pollutant", y="Value")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("API Error")

    # =========================
    # TREND
    # =========================
    if st.button("Show Trend 📈"):

        years = list(range(2015, 2025))
        trend_data = []

        for y in years:
            try:
                res = requests.post(
                    f"{API_URL}/predict",
                    json={"year": y, "station_id": selected_station},
                    timeout=3
                )

                if res.status_code == 200:
                    trend_data.append({
                        "Year": y,
                        "WQI": res.json()["wqi_score"]
                    })
            except:
                continue

        trend_df = pd.DataFrame(trend_data)

        if not trend_df.empty:
            fig = px.line(trend_df, x="Year", y="WQI", markers=True)
            st.plotly_chart(fig, use_container_width=True)

# =========================
# SENSOR MODE
# =========================
else:

    col1, col2, col3 = st.columns(3)

    with col1:
        NH4 = st.number_input("NH4", value=0.3)
        BSK5 = st.number_input("BSK5", value=2.5)
        Suspended = st.number_input("Suspended", value=20.0)

    with col2:
        O2 = st.number_input("O2", value=5.0)
        NO3 = st.number_input("NO3", value=30.0)
        NO2 = st.number_input("NO2", value=1.0)

    with col3:
        SO4 = st.number_input("SO4", value=200.0)
        PO4 = st.number_input("PO4", value=0.3)
        CL = st.number_input("CL", value=150.0)

    if st.button("Analyze"):

        payload = {
            "NH4": NH4,
            "BSK5": BSK5,
            "Suspended": Suspended,
            "O2": O2,
            "NO3": NO3,
            "NO2": NO2,
            "SO4": SO4,
            "PO4": PO4,
            "CL": CL
        }

        res = requests.post(f"{API_URL}/analyze", json=payload)

        if res.status_code == 200:
            data = res.json()

            wqi = data["wqi_score"]
            quality = data["quality"]

            color = "green" if wqi < 50 else "orange" if wqi < 100 else "red"

            st.markdown(f"### WQI: :{color}[{wqi:.2f}] ({quality})")

            df = pd.DataFrame({
                "Parameter": list(payload.keys()),
                "Value": list(payload.values())
            })

            fig = px.bar(df, x="Parameter", y="Value")
            st.plotly_chart(fig, use_container_width=True)