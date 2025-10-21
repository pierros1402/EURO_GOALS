# ==============================================
# AUTO MODE MODULE – Smart Money Alerts Filter
# EURO_GOALS v6f – Final Enhanced Edition
# ==============================================

from datetime import datetime
from asian_reader import get_smart_money_data
import random

AUTO_ALERTS_CACHE = {
    "last_update": None,
    "alerts": []
}

# Κατώφλι μεταβολής για "ισχυρά σήματα"
SIGNAL_THRESHOLD = 0.20  # 20%

def get_alerts():
    """
    Δημιουργεί alerts με βάση τις μεταβολές Smart Money
    και φιλτράρει τα σήματα που ξεπερνούν το όριο (π.χ. 20%)
    """
    data = get_smart_money_data()
    matches = data.get("results", [])
    strong_alerts = []

    for m in matches:
        try:
            home = float(m["odds"]["Home"])
            away = float(m["odds"]["Away"])
            diff = abs(home - away) / ((home + away) / 2)
            if diff >= SIGNAL_THRESHOLD:
                strong_alerts.append({
                    "match": m["match"],
                    "signal": f"Δυνατό Σήμα ({int(diff*100)}%)",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
        except Exception:
            continue

    AUTO_ALERTS_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    AUTO_ALERTS_CACHE["alerts"] = strong_alerts

    print(f"[AUTO MODE] ✅ {len(strong_alerts)} Smart Money signals detected (>{int(SIGNAL_THRESHOLD*100)}%)")
    return AUTO_ALERTS_CACHE
