# 💧 Water Quality Prediction System

AI-driven solution to monitor and predict water quality parameters like O₂, NO₃⁻, NH₄⁺, SO₄²⁻, and more.

---

##  Project Summary

* Predicts O₂, NO₃⁻, NH₄⁺ using ML models
* Trained on historical water quality data
* Detects potential safety issues early
* Enables smarter environmental monitoring
* Helps visualize chemical trends and their correlations
* Aims to support public health and environmental decision-making

---

##  Sample Dataset

| NH₄   | BSK5 | Suspended | O₂    | NO₃   | NO₂  | SO₄ | PO₄  | CL   |
| ----- | ---- | --------- | ----- | ----- | ---- | --- | ---- | ---- |
| 0.33  | 2.77 | 12        | 12.3  | 9.5   | 0.05 | 154 | 0.45 | 289  |
| 0.044 | 3.00 | 51.6      | 14.61 | 17.75 | 0.03 | 352 | 0.09 | 1792 |

---

##  How It Works

1. Clean & encode data
2. Split dataset (80% training, 20% testing)
3. Train ML model (RandomForestRegressor)
4. Predict unknown pollutant levels
5. Evaluate performance (RMSE, MAE, R²)

---

##  Tech Stack

* Python 3.x
* pandas, NumPy
* scikit-learn
* Jupyter Notebook
* matplotlib, seaborn

---

##  Visual Outputs

* Correlation heatmap
* Actual vs Predicted plot
* Feature importance chart

---

##  Use Cases

* Government water quality monitoring
* Rural area water safety alerts
* Industrial wastewater assessment
* Early-warning contamination systems

---

## ▶ Running the App

To run this project using Streamlit:

```bash
cd src
streamlit run app.py
```

Ensure all dependencies are installed and the dataset is present in the correct path.

---


