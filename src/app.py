import pandas as pd
import numpy as np
import joblib
import pickle
import streamlit as st
import sklearn

model=joblib.load("pollution_model.pkl")
model_cols = joblib.load("model_columns.pkl")

st.title('Water Impurity Prediction')
st.write("Please enter the following details to predict water impurity:")

year_input=st.number_input("Enter Year", min_value=2000, max_value=2100, value=2022)
station_id=st.text_input("Enter Station ID", value='1')


#encode then Predict
if st.button('Predict'):
    if not station_id:
        st.warning('Please enter the station ID')
    else:
        # get the input and it will encode id+year
        input_df = pd.DataFrame({'year': [year_input], 'id':[station_id]})
        input_encoded = pd.get_dummies(input_df, columns=['id'])

        # align with model cols
        for col in model_cols:
            if col not in input_encoded.columns:
                input_encoded[col] = 0
        input_encoded = input_encoded[model_cols]

        # Predict
        predicted_pollutants = model.predict(input_encoded)[0]
        pollutants = ['O2', 'NO3', 'NO2', 'SO4', 'PO4', 'CL']
        safe_thresholds = {
    'O2': 4,         # > 4 mg/L is safe (indicator only)
    'NO3': 50,
    'NO2': 3,
    'SO4': 250,
    'PO4': 0.5,      # Using tolerable limit
    'CL': 250
}

        st.subheader(f"Predicted pollutant levels for the station '{station_id}' in {year_input}:")
        # predicted_values = {}
        # for p, val in zip(pollutants, predicted_pollutants):
        #     st.write(f'{p}: &nbsp;{val:.2f}')

        predicted_values = {}
        is_impure = False

        for p, val in zip(pollutants, predicted_pollutants):
            predicted_values[p] = val
            #compare with threshold
            if p == 'O2':
                if val < safe_thresholds[p]:
                    is_impure = True
            else:
                if val > safe_thresholds[p]:
                    is_impure = True
            st.write(f"**{p}**: {val:.2f} mg/L")

        # final water quality verdict
        st.markdown("---")
        if is_impure:
            st.error(" **Water is Impure to Drink** 🚱")
        else:
            st.success("  **Water is Pure to Drink** 💧")
