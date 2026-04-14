

import os
import numpy as np
import pandas as pd
import streamlit as st
import joblib
import plotly.express as px

st.set_page_config(page_title="Water Impurity Prediction", page_icon="💧")

@st.cache_resource(show_spinner=False)
def load_artifacts():
    try:
        model = joblib.load("pollution_model.pkl")
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        st.stop()

    try:
        model_cols = joblib.load("model_columns.pkl")
        if isinstance(model_cols, (pd.Index, np.ndarray)):
            model_cols = list(model_cols)
        elif not isinstance(model_cols, list):
            model_cols = list(model_cols)
    except Exception as e:
        st.error(f"Failed to load model columns: {e}")
        st.stop()

    target_names = None
    if os.path.exists("target_names.pkl"):
        try:
            target_names = joblib.load("target_names.pkl")
            if isinstance(target_names, (pd.Index, np.ndarray)):
                target_names = list(target_names)
        except Exception:
            target_names = None

    return model, model_cols, target_names

model, model_cols, target_names = load_artifacts()

# Load dataset 
try:
    df_full = pd.read_csv("water_quality.csv")
    df_full["id"] = df_full["id"].astype(str)
    all_stations = sorted(df_full["id"].unique())
except Exception:
    all_stations = ["1"]  # fallback if dataset not available

# EXACT training target order (9 outputs)
DEFAULT_TARGETS = ['NH4','BSK5','Suspended','O2','NO3','NO2','SO4','PO4','CL']
pollutants = target_names if (target_names and len(target_names) > 0) else DEFAULT_TARGETS

# Sidebar: Thresholds
st.sidebar.header("Thresholds (mg/L)")
st.sidebar.caption("Only enforced values affect the final verdict.")

# Defaults (commonly used guide values). None = not enforced.
defaults = {
    'NH4': None,      # e.g., 0.5 if you want to enforce
    'BSK5': None,     # (BOD5) e.g., 3.0
    'Suspended': None,# e.g., 25
    'O2': 4.0,        # min
    'NO3': 50.0,      # max
    'NO2': 3.0,       # max
    'SO4': 250.0,     # max
    'PO4': 0.5,       # max
    'CL': 250.0       # max
}

# UI to optionally enforce NH4/BSK5/Suspended
enf_nh4 = st.sidebar.checkbox("Enforce NH4 max", value=False)
enf_bod = st.sidebar.checkbox("Enforce BSK5 (BOD5) max", value=False)
enf_ss  = st.sidebar.checkbox("Enforce Suspended Solids max", value=False)

SAFE_THRESHOLDS = {
    'NH4': st.sidebar.number_input("NH4 max", min_value=0.0, value=0.5, step=0.1) if enf_nh4 else None,
    'BSK5': st.sidebar.number_input("BSK5 (BOD5) max", min_value=0.0, value=3.0, step=0.1) if enf_bod else None,
    'Suspended': st.sidebar.number_input("Suspended Solids max", min_value=0.0, value=25.0, step=1.0) if enf_ss else None,
    'O2': defaults['O2'],
    'NO3': defaults['NO3'],
    'NO2': defaults['NO2'],
    'SO4': defaults['SO4'],
    'PO4': defaults['PO4'],
    'CL': defaults['CL'],
}

# For display: min for O2 else max
def threshold_type(p): return "min" if p == "O2" else "max"

# UI (main)
st.title("💧 Water Impurity Prediction (9-parameter)")
st.write("Predict nine water quality indicators and determine drinkability based on enforced thresholds.")

with st.form("prediction_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1:
        year_input = st.number_input("Year", min_value=2000, max_value=2100, value=2022, step=1)
    with c2:
        station_id = st.text_input("Station ID (exact as in training)", value="1")

    submitted = st.form_submit_button("Predict")

if submitted:
    if not str(station_id).strip():
        st.warning("Please enter a Station ID.")
        st.stop()

    # Build raw input
    input_df = pd.DataFrame({'year': [int(year_input)], 'id': [str(station_id)]})

    # One-hot encode station id like training
    input_encoded = pd.get_dummies(input_df, columns=['id'])

    # Align with training columns
    missing_cols = set(model_cols) - set(input_encoded.columns)
    for col in missing_cols:
        input_encoded[col] = 0
    input_encoded = input_encoded.reindex(columns=model_cols, fill_value=0)

    # Warn if unseen station id (no one-hot active)
    id_dummy_cols = [c for c in model_cols if c.startswith("id_")]
    if id_dummy_cols and (input_encoded[id_dummy_cols].sum(axis=1).iloc[0] == 0):
        st.info("Heads up: This Station ID was unseen during training. Prediction may be less accurate.")

    # Predict
    try:
        y_pred = model.predict(input_encoded)
    except Exception as e:
        st.error(f"Prediction failed: {e}")
        st.stop()

    y_pred = np.array(y_pred).reshape(-1).astype(float)

    # HARD STOP if sizes don't match
    if len(y_pred) != len(pollutants):
        st.error(
            f"Target count mismatch: model returned {len(y_pred)} values, "
            f"but {len(pollutants)} target names are configured.\n"
            "Ensure target_names.pkl matches the model's output order."
        )
        st.stop()

    # Map predictions to REAL pollutant names
    vals_by_pollutant = {p: float(v) for p, v in zip(pollutants, y_pred)}

    # Build results table (show if threshold enforced or not)
    enforced = {p: (SAFE_THRESHOLDS[p] is not None) for p in pollutants}
    df_res = pd.DataFrame({
        "Pollutant": pollutants,
        "Predicted (mg/L)": [round(vals_by_pollutant[p], 2) for p in pollutants],
        "Threshold Type": [threshold_type(p) for p in pollutants],
        "Safe Threshold (mg/L)": [SAFE_THRESHOLDS[p] if SAFE_THRESHOLDS[p] is not None else "-" for p in pollutants],
        "Enforced": ["Yes" if enforced[p] else "No" for p in pollutants],
    })

    # Verdict logic: only enforced thresholds affect verdict
    failed, verdict_flags = [], []
    for p in pollutants:
        thr = SAFE_THRESHOLDS[p]
        if thr is None:
            continue
        val = vals_by_pollutant[p]
        if p == "O2":
            ok = (val >= thr)
            if not ok: failed.append(f"- {p}: {val:.2f} < min {thr}")
        else:
            ok = (val <= thr)
            if not ok: failed.append(f"- {p}: {val:.2f} > max {thr}")
        verdict_flags.append(ok)

    is_potable = all(verdict_flags) if verdict_flags else True

    st.subheader(f"Predicted levels for Station '{station_id}' in {year_input}")
    st.dataframe(df_res, use_container_width=True)

    st.bar_chart(pd.DataFrame({"Predicted (mg/L)": [vals_by_pollutant[p] for p in pollutants]}, index=pollutants))

    st.markdown("---")
    if is_potable:
        st.success("**Water is Pure to Drink** 💧")
    else:
        st.error("**Water is Impure to Drink** 🚱")
        st.write("**Reasons:**")
        st.markdown("\n".join(failed))

    st.caption(
        "Note: O2 uses a minimum threshold; all others use maximum thresholds. "
        "Enable thresholds in the sidebar to include NH4/BSK5/Suspended in the verdict."
    )
    
  
    

col1, col2, col3 = st.columns(3)

with col1:
    selected_station = st.text_input("Station ID (exact as in training)", value="1")

with col2:
    start_year = st.number_input("Start Year", min_value=2000, max_value=2100, value=2010)

with col3:
    end_year = st.number_input("End Year", min_value=2000, max_value=2100, value=2025)

generate_trend = st.button("Generate Trend")
if generate_trend:

    if start_year > end_year:
        st.error("Start year must be less than or equal to End year.")
        st.stop()

    years = list(range(int(start_year), int(end_year) + 1))
    trend_predictions = []

    for y in years:

        # Build input
        input_df = pd.DataFrame({
            'year': [int(y)],
            'id': [str(selected_station)]
        })

        # One-hot encode
        input_encoded = pd.get_dummies(input_df, columns=['id'])

        # Align columns with training
        missing_cols = set(model_cols) - set(input_encoded.columns)
        for col in missing_cols:
            input_encoded[col] = 0

        input_encoded = input_encoded.reindex(columns=model_cols, fill_value=0)

        # Predict
        y_pred = model.predict(input_encoded)
        y_pred = np.array(y_pred).reshape(-1).astype(float)

        trend_predictions.append(y_pred)

    # Convert to DataFrame
    trend_array = np.array(trend_predictions)

    trend_df = pd.DataFrame(
        trend_array,
        columns=pollutants
    )

    trend_df["Year"] = years
    trend_df = trend_df.set_index("Year")

    # Show All Pollutants Trend
    st.subheader(f"Trend for Station {selected_station} ({start_year}–{end_year})")
    st.line_chart(trend_df)

    # Individual Pollutant View
    st.subheader("View Specific Pollutant")

    selected_pollutant = st.selectbox(
        "Select Pollutant",
        pollutants
    )

    st.line_chart(trend_df[[selected_pollutant]])

    # Show Table
    st.dataframe(trend_df, use_container_width=True)

    st.success("Trend generated successfully.")