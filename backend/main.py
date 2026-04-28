from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import os
from fastapi.middleware.cors import CORSMiddleware
from utils.wqi import calculate_wqi
from utils.ai_insights import generate_ai_insight

app = FastAPI(title="Water Quality API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load model
model = joblib.load(os.path.join(BASE_DIR, "model", "pollution_model.pkl"))
model_cols = joblib.load(os.path.join(BASE_DIR, "model", "model_columns.pkl"))
targets = joblib.load(os.path.join(BASE_DIR, "model", "target_names.pkl"))

# =========================
# SCHEMA 1: Prediction Mode
# =========================
class PredictionInput(BaseModel):
    year: int
    station_id: str

# =========================
# SCHEMA 2: Sensor Mode
# =========================
class SensorInput(BaseModel):
    NH4: float
    BSK5: float
    Suspended: float
    O2: float
    NO3: float
    NO2: float
    SO4: float
    PO4: float
    CL: float


@app.get("/")
def home():
    return {"message": "Water Quality API Running 🚀"}


# =====================================
# 📊 ML Prediction (Year + Station)
# =====================================
@app.post("/predict")
def predict(data: PredictionInput):
    try:
        input_df = pd.DataFrame({
            "year": [data.year],
            "id": [data.station_id]
        })

        input_encoded = pd.get_dummies(input_df, columns=["id"])

        missing_cols = set(model_cols) - set(input_encoded.columns)
        for col in missing_cols:
            input_encoded[col] = 0

        input_encoded = input_encoded.reindex(columns=model_cols, fill_value=0)

        y_pred = model.predict(input_encoded)
        y_pred = np.array(y_pred).reshape(-1)

        result = {targets[i]: float(y_pred[i]) for i in range(len(targets))}

        wqi_score, category = calculate_wqi(result)

        return {
            "mode": "prediction",
            "prediction": result,
            "wqi_score": wqi_score,
            "quality": category
        }

    except Exception as e:
        return {"error": str(e)}


# =====================================
# 🧪 Direct Sensor Analysis
# =====================================
@app.post("/analyze")
def analyze(data: SensorInput):
    try:
        values = {
            "NH4": data.NH4,
            "BSK5": data.BSK5,
            "Suspended": data.Suspended,
            "O2": data.O2,
            "NO3": data.NO3,
            "NO2": data.NO2,
            "SO4": data.SO4,
            "PO4": data.PO4,
            "CL": data.CL
        }

        wqi_score, category = calculate_wqi(values)

        return {
            "mode": "sensor_analysis",
            "input": values,
            "wqi_score": wqi_score,
            "quality": category
        }

    except Exception as e:
        return {"error": str(e)}
@app.post("/ai-insight")
def ai_insight(data: dict):

    prediction = data.get("prediction")
    query_type = data.get("type", "health")

    insight = generate_ai_insight(prediction, query_type)

    return {
        "insight": insight
    }