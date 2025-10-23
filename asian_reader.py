# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# ==============================================

import requests
import json
from datetime import datetime

# ----------------------------------------------
# Ρυθμίσεις
# ----------------------------------------------
ALERT_ENDPOINT = "https://euro-goalsv7-9.onrender.com/api/add_alert"

# ----------------------------------------------
# Κύρια συνάρτηση ανίχνευσης Smart Money
# ----------------------------------------------
def detect_smart_money():
    """
    Ανιχνεύει έντονες μεταβολές αποδόσεων/ασιατικών γραμμών
    από γνωστές πηγές (π.χ. Pinnacle, SBOBET, 188BET).
    Επιστρέφει λίστα με ύποπτα παιχνίδια.
    """
    print("[ASIAN READER] 🔍 Checking Smart Money movements...")

    # Προσωρινά δεδομένα mock για επίδειξη
    movements = []
    sources = [
        {
            "bookmaker": "Pinnacle",
            "match": "Chelsea vs Arsenal",
            "old_odds": 1.92,
            "new_odds": 1.78
        },
        {
            "bookmaker": "SBOBET",
            "match": "Real Madrid vs Barcelona",
            "old_odds": 2.15,
            "new_odds": 2.10
        }
    ]

    for src in sources:
        try:
            diff = round(src["old_odds"] - src["new_odds"], 3)
            if abs(diff) >= 0.1:
                alert_message = (
                    f"Smart Money Detected – {src['bookmaker']}: "
                    f"{src['match']} odds moved {src['old_odds']} → {src['new_odds']} 🎯"
                )
                print(f"[SMART MONEY] {alert_message}")
                movements.append(alert_message)

                # ----------------------------------------------
                # Αποστολή ειδοποίησης στο backend (Render)
                # ----------------------------------------------
                try:
                    res = requests.post(
                        ALERT_ENDPOINT,
                        json={
                            "message": alert_message,
                            "source": src["bookmaker"]
                        },
                        timeout=5
                    )
                    if res.status_code == 200:
                        print("[ALERT] 🚀 Smart Money alert sent to backend successfully.")
                    else:
                        print(f"[ALERT] ⚠️ Backend responded with {res.status_code}: {res.text}")
                except requests.exceptions.Timeout:
                    print("[ALERT] ⚠️ Timeout while sending alert to backend.")
                except Exception as e:
                    print(f"[ALERT] ❌ Failed to send alert: {e}")

        except Exception as e:
            print(f"[SMART MONEY] ❌ Error processing source {src}: {e}")

    # ----------------------------------------------
    # Τελική αναφορά
    # ----------------------------------------------
    if movements:
        print(f"[SMART MONEY] ✅ Total movements detected: {len(movements)}")
    else:
        print("[SMART MONEY] ℹ️ No movements detected this round.")

    print("[SMART MONEY] 🔁 Scan completed.")
    return movements


# ----------------------------------------------
# Εκτέλεση για test
# ----------------------------------------------
if __name__ == "__main__":
    detect_smart_money()
