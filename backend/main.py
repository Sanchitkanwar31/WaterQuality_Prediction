from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
from utils.wqi import calculate_wqi
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Water Quality API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "model", "pollution_model.pkl"))
columns = joblib.load(os.path.join(BASE_DIR, "model", "model_columns.pkl"))
targets = joblib.load(os.path.join(BASE_DIR, "model", "target_names.pkl"))

# Request schema
class WaterInput(BaseModel):
    temperature: float
    ph: float
    turbidity: float
    conductivity: float

@app.get("/")
def home():
    return {"message": "Water Quality Prediction API Running 🚀"}

@app.post("/predict")
def predict(data: WaterInput):
    try:
        # Convert input to array
        input_data = np.array([[data.temperature, data.ph, data.turbidity, data.conductivity]])

        # Prediction
        prediction = model.predict(input_data)[0]

        # Convert to dict
        result = {targets[i]: float(prediction[i]) for i in range(len(targets))}

        # Calculate WQI
        wqi_score, category = calculate_wqi(result)

        return {
            "prediction": result,
            "wqi_score": wqi_score,
            "quality": category
        }

    except Exception as e:
        return {"error": str(e)}