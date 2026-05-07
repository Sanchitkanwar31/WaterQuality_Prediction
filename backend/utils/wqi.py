def calculate_wqi(values):
    """
    Simple WQI calculation based on weights
    """

    weights = {
        "O2": 0.3,
        "NO3": 0.3,
        "NH4": 0.4
    }

    # Normalize (example thresholds)
    standards = {
        "O2": 8,
        "NO3": 10,
        "NH4": 1
    }

    wqi = 0

    for param in values:
        if param in weights:
            quality = (values[param] / standards[param]) * 100
            wqi += quality * weights[param]

    # Classification
    if wqi >= 80:
        category = "Good 🟢"
    elif wqi >= 50:
        category = "Moderate 🟡"
    else:
        category = "Poor 🔴"

    return round(wqi, 2), category