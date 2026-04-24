# backend/utils/ai_insights.py

def classify_severity(param, value):
    """Return severity level based on threshold"""
    thresholds = {
        "NH4": 0.5, "BSK5": 3, "Suspended": 25,
        "O2": 4, "NO3": 50, "NO2": 3,
        "SO4": 250, "PO4": 0.5, "CL": 250
    }

    limit = thresholds[param]

    if param == "O2":
        if value >= limit:
            return "safe"
        elif value >= limit * 0.7:
            return "moderate"
        else:
            return "danger"

    else:
        if value <= limit:
            return "safe"
        elif value <= limit * 1.5:
            return "moderate"
        else:
            return "danger"


def summarize_water(pred):
    """Overall summary"""
    danger_count = 0
    moderate_count = 0

    for k, v in pred.items():
        sev = classify_severity(k, v)
        if sev == "danger":
            danger_count += 1
        elif sev == "moderate":
            moderate_count += 1

    if danger_count >= 2:
        return "🚨 Water is unsafe and may pose serious health risks."
    elif moderate_count >= 3:
        return "⚠ Water quality is moderate and needs treatment before drinking."
    else:
        return "✅ Water is generally safe within acceptable limits."


def health_analysis(pred):
    messages = []

    if pred["NO3"] > 50:
        messages.append("High nitrate levels can cause methemoglobinemia (blue baby syndrome).")

    if pred["BSK5"] > 3:
        messages.append("Elevated BOD indicates organic pollution and possible microbial contamination.")

    if pred["NO2"] > 3:
        messages.append("Nitrite toxicity can affect oxygen transport in blood.")

    if pred["Suspended"] > 25:
        messages.append("High suspended solids may carry pathogens and reduce water clarity.")

    if pred["CL"] > 250:
        messages.append("Excess chloride may lead to hypertension and taste issues.")

    if not messages:
        messages.append("No significant health risks detected.")

    return messages


def treatment_advice(pred):
    advice = []

    if pred["NO3"] > 50:
        advice.append("Use Reverse Osmosis (RO) to remove nitrates.")

    if pred["BSK5"] > 3:
        advice.append("Apply biological treatment or aeration to reduce organic load.")

    if pred["Suspended"] > 25:
        advice.append("Use filtration (sand/activated carbon) to remove suspended particles.")

    if pred["NO2"] > 3:
        advice.append("Ion exchange or biological filtration recommended.")

    if pred["CL"] > 250:
        advice.append("Use demineralization or RO systems.")

    if not advice:
        advice.append("Basic filtration and boiling are sufficient.")

    return advice


def explanation(pred):
    explanation_text = "This prediction is based on analysis of key water quality indicators:\n\n"

    for k, v in pred.items():
        explanation_text += f"- {k}: {v:.2f}\n"

    explanation_text += "\nThe model evaluates chemical, biological, and physical parameters to determine safety."

    return explanation_text


def trend_analysis(pred):
    """Simple reasoning-based trend insight"""
    if pred["NO3"] > 50 and pred["BSK5"] > 3:
        return "Pollution trend suggests agricultural runoff and organic contamination increasing."

    if pred["O2"] < 4:
        return "Low dissolved oxygen indicates possible ecosystem stress."

    return "Water parameters appear stable with no alarming trend indicators."


def generate_ai_insight(pred, query_type="health"):
    """Main AI router"""

    summary = summarize_water(pred)

    if query_type == "health":
        risks = health_analysis(pred)
        return summary + "\n\nHealth Risks:\n- " + "\n- ".join(risks)

    elif query_type == "treatment":
        steps = treatment_advice(pred)
        return summary + "\n\nRecommended Treatment:\n- " + "\n- ".join(steps)

    elif query_type == "explanation":
        return explanation(pred)

    elif query_type == "trend":
        return trend_analysis(pred)

    else:
        return summary