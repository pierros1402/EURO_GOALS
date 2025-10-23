# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v7.9e – with Browser Notifications
# ==============================================

import requests
import json
from datetime import datetime
import time

# ----------------------------------------------
# CONFIG
# ----------------------------------------------
RENDER_NOTIFY_URL = "https://euro-goalsv7-9.onrender.com/notify"
CHECK_INTERVAL = 90  # seconds between checks

# ----------------------------------------------
# Notification sender
# ----------------------------------------------
def send_browser_notification(title, body, tag="smart-money"):
    """
    Στέλνει browser notification μέσω του FastAPI endpoint /notify
    """
    try:
        payload = {
            "title": title,
            "body": body,
            "url": "/live",
            "tag": tag
        }
        requests.post(RENDER_NOTIFY_URL, json=payload, timeout=5)
        print(f"[NOTIFY] 🔔 {title} → {body}")
    except Exception as e:
        print("[NOTIFY] ❌ Error sending notification:", e)

# ----------------------------------------------
# Smart Money Detector
# ----------------------------------------------
def detect_smart_money():
    """
    Ανιχνεύει έντονες μεταβολές αποδόσεων/ασιατικών γραμμών
    από γνωστές πηγές (π.χ. Pinnacle, SBOBET, 188BET).
    Επιστρέφει μια λίστα με ύποπτα παιχνίδια και στέλνει ειδοποιήσεις.
    """

    print("[ASIAN READER] 🔍 Checking Smart Money movements...")

    try:
        # --- Προσωρινά δεδομένα (θα αντικατασταθούν με API feeds) ---
        sources = {
            "Pinnacle": [
                {"match": "Chelsea vs Arsenal", "old_odds": 1.92, "new_odds": 1.78},
                {"match": "Bayern vs Dortmund", "old_odds": 2.01, "new_odds": 1.97}
            ],
            "SBOBET": [
                {"match": "AC Milan vs Inter", "old_odds": 1.88, "new_odds": 1.74},
                {"match": "PSG vs Lyon", "old_odds": 1.90, "new_odds": 1.89}
            ]
        }

        alerts = []

        # --- Έλεγχος μεταβολών ---
        for source, matches in sources.items():
            for m in matches:
                old_odds = m["old_odds"]
                new_odds = m["new_odds"]
                diff = round(abs(new_odds - old_odds), 2)

                if diff >= 0.10:  # μεταβολή άνω του 0.10
                    alert = {
                        "source": source,
                        "match": m["match"],
                        "from": old_odds,
                        "to": new_odds,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    alerts.append(alert)

                    # --- Ειδοποίηση στον browser ---
                    body_text = f"{source}: {m['match']} odds moved {old_odds:.2f} → {new_odds:.2f}"
                    send_browser_notification("Smart Money Detected", body_text)

        if alerts:
            print(f"[ASIAN READER] ⚠️ {len(alerts)} Smart Money signals detected.")
        else:
            print("[ASIAN READER] ✅ No major odds movement detected.")

        return alerts

    except Exception as e:
        print("[ASIAN READER] ❌ Error:", e)
        return []

# ----------------------------------------------
# Manual test run
# ----------------------------------------------
if __name__ == "__main__":
    print("[ASIAN READER] ▶ Manual run started.")
    while True:
        detect_smart_money()
        time.sleep(CHECK_INTERVAL)
