# import pandas as pd
# import numpy as np
# import joblib
# import pickle
# import streamlit as st
# import sklearn

# model=joblib.load("pollution_model.pkl")
# model_cols = joblib.load("model_columns.pkl")

# st.title('Water Impurity Prediction')
# st.write("Please enter the following details to predict water impurity:")

# year_input=st.number_input("Enter Year", min_value=2000, max_value=2100, value=2022)
# station_id=st.text_input("Enter Station ID", value='1')


# #encode then Predict
# if st.button('Predict'):
#     if not station_id:
#         st.warning('Please enter the station ID')
#     else:
#         # get the input and it will encode id+year
#         input_df = pd.DataFrame({'year': [year_input], 'id':[station_id]})
#         input_encoded = pd.get_dummies(input_df, columns=['id'])

#         # align with model cols
#         for col in model_cols:
#             if col not in input_encoded.columns:
#                 input_encoded[col] = 0
#         input_encoded = input_encoded[model_cols]

#         # Predict
#         predicted_pollutants = model.predict(input_encoded)[0]
#         pollutants = ['O2', 'NO3', 'NO2', 'SO4', 'PO4', 'CL']
#         safe_thresholds = {
#     'O2': 4,         
#     'NO3': 50,
#     'NO2': 3,
#     'SO4': 250,
#     'PO4': 0.5,      # Using tolerable limit
#     'CL': 250
# }

#         st.subheader(f"Predicted pollutant levels for the station '{station_id}' in {year_input}:")
#         # predicted_values = {}
#         # for p, val in zip(pollutants, predicted_pollutants):
#         #     st.write(f'{p}: &nbsp;{val:.2f}')

#         predicted_values = {}
#         is_impure = False

#         for p, val in zip(pollutants, predicted_pollutants):
#             predicted_values[p] = val
#             #compare with threshold
#             if p == 'O2':
#                 if val < safe_thresholds[p]:
#                     is_impure = True
#             else:
#                 if val > safe_thresholds[p]:
#                     is_impure = True
#             st.write(f"**{p}**: {val:.2f} mg/L")

#         # final water quality verdict
#         st.markdown("---")
#         if is_impure:
#             st.error(" **Water is Impure to Drink** 🚱")
#         else:
#             st.success("  **Water is Pure to Drink** 💧")


import os
import numpy as np
import pandas as pd
import streamlit as st
import joblib

st.set_page_config(page_title="Water Impurity Prediction", page_icon="💧")

# ---------------------------
# Load model & metadata
# ---------------------------
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

# EXACT training target order (9 outputs)
DEFAULT_TARGETS = ['NH4','BSK5','Suspended','O2','NO3','NO2','SO4','PO4','CL']
pollutants = target_names if (target_names and len(target_names) > 0) else DEFAULT_TARGETS

# ---------------------------
# Sidebar: Thresholds
# ---------------------------
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

# ---------------------------
# UI (main)
# ---------------------------
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
