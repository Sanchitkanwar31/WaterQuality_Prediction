# backend/utils/ai_insights.py

WHO_LIMITS = {
    "NH4": 0.5, "BSK5": 3, "Suspended": 25,
    "O2": 4, "NO3": 50, "NO2": 3,
    "SO4": 250, "PO4": 0.5, "CL": 250
}


# ================= SEVERITY =================
def classify_severity(param, value):
    limit = WHO_LIMITS[param]

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


# ================= PRIORITY ISSUES =================
def get_top_issues(pred):
    issues = []

    for k, v in pred.items():
        sev = classify_severity(k, v)

        if sev != "safe":
            issues.append((k, v, sev))

    # sort by severity (danger first)
    issues.sort(key=lambda x: 0 if x[2] == "danger" else 1)

    return issues[:3]  # top 3


# ================= SUMMARY =================
def summarize_water(pred):
    issues = get_top_issues(pred)

    if not issues:
        return "✅ Water quality is within safe WHO limits."

    if any(sev == "danger" for _, _, sev in issues):
        return "🚨 Water is unsafe due to critical parameter violations."

    return "⚠ Water quality is moderate and requires treatment."


# ================= HEALTH =================
def health_analysis(pred):
    issues = get_top_issues(pred)

    messages = []

    for k, v, sev in issues:
        if k == "NO3":
            messages.append("High nitrate may cause oxygen deficiency in infants.")
        elif k == "BSK5":
            messages.append("High BOD indicates organic pollution and bacterial growth.")
        elif k == "NO2":
            messages.append("Nitrite toxicity affects blood oxygen transport.")
        elif k == "Suspended":
            messages.append("Suspended particles may carry harmful microbes.")
        elif k == "CL":
            messages.append("Excess chloride may impact taste and blood pressure.")
        elif k == "O2":
            messages.append("Low oxygen harms aquatic life and indicates poor quality.")

    if not messages:
        return ["No major health risks detected."]

    return messages


# ================= TREATMENT =================
def treatment_advice(pred):
    issues = get_top_issues(pred)

    advice = []

    for k, v, sev in issues:
        if k == "NO3":
            advice.append("Apply Reverse Osmosis (RO) to remove nitrates.")
        elif k == "BSK5":
            advice.append("Use biological treatment or aeration.")
        elif k == "Suspended":
            advice.append("Use filtration or sedimentation.")
        elif k == "NO2":
            advice.append("Use ion exchange or bio-filtration.")
        elif k == "CL":
            advice.append("Use RO or demineralization.")
        elif k == "O2":
            advice.append("Increase aeration to improve oxygen levels.")

    if not advice:
        advice.append("Basic filtration and boiling are sufficient.")

    return advice


# ================= EXPLANATION =================
def explanation(pred):
    text = "📊 Water Quality Breakdown:\n\n"

    for k, v in pred.items():
        limit = WHO_LIMITS[k]
        status = classify_severity(k, v)

        if k == "O2":
            text += f"- {k}: {v:.2f} (min required {limit}) → {status}\n"
        else:
            text += f"- {k}: {v:.2f} (max allowed {limit}) → {status}\n"

    text += "\nThis analysis is based on WHO drinking water standards."

    return text


# ================= TREND =================
def trend_analysis(pred):
    issues = get_top_issues(pred)

    if not issues:
        return "Water quality is stable with no concerning trends."

    if any(k in ["NO3", "NO2"] for k, _, _ in issues):
        return "Possible agricultural runoff increasing chemical contamination."

    if any(k == "BSK5" for k, _, _ in issues):
        return "Organic pollution trend suggests waste discharge nearby."

    if any(k == "O2" for k, _, _ in issues):
        return "Low oxygen levels indicate ecosystem stress."

    return "Moderate fluctuations observed in water quality."


# ================= MAIN AI =================
def generate_ai_insight(pred, query_type="health"):

    summary = summarize_water(pred)
    issues = get_top_issues(pred)

    issue_text = "\n".join([f"- {k}: {v:.2f} ({sev})" for k, v, sev in issues])

    if query_type == "health":
        risks = health_analysis(pred)
        return f"""{summary}

🔍 Key Issues:
{issue_text}

🧠 Health Impact:
- """ + "\n- ".join(risks)

    elif query_type == "treatment":
        steps = treatment_advice(pred)
        return f"""{summary}

🔧 Recommended Actions:
- """ + "\n- ".join(steps)

    elif query_type == "explanation":
        return explanation(pred)

    elif query_type == "trend":
        return trend_analysis(pred)

    else:
        return f"""{summary}

🔍 Key Issues:
{issue_text}
"""