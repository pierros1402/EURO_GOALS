# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v6f – Auto Refresh Edition
# ==============================================

import requests
import json
import threading
import time
from datetime import datetime

# -----------------------------
# Global cache (τελευταία δεδομένα)
# -----------------------------
SMART_MONEY_CACHE = {
    "last_update": None,
    "results": []
}

# -----------------------------
# Κύρια συνάρτηση ανίχνευσης
# -----------------------------
def detect_smart_money():
    """
    Ανιχνεύει έντονες μεταβολές αποδόσεων/ασιατικών γραμμών.
    Προς το παρόν χρησιμοποιεί mock δεδομένα.
    """
    print("[SMART MONEY] 🔍 Checking Asian market data...")

    try:
        # (Προσωρινά URLs / placeholder APIs)
        sources = [
            "https://example-asian-api.com/odds_feed",
            "https://example-sbo-api.com/data"
        ]

        results = []
        for src in sources:
            # Εικονικά δεδομένα (μέχρι να μπουν πραγματικά API)
            sample = {
                "match": "Olympiacos - AEK",
                "change": "-0.25",
                "time": str(datetime.now().strftime("%H:%M:%S"))
            }
            results.append(sample)
            results.append({
                "match": "PAOK - Aris",
                "change": "+0.5",
                "time": str(datetime.now().strftime("%H:%M:%S"))
            })

        # Αποθήκευση στο global cache
        SMART_MONEY_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SMART_MONEY_CACHE["results"] = results

        print(f"[SMART MONEY] ✅ Updated {len(results)} market moves.")
        return results

    except Exception as e:
        print("[SMART MONEY] ❌ Error:", e)
        return []

# -----------------------------
# Συνάρτηση για αυτόματη ανανέωση
# -----------------------------
def auto_refresh(interval_minutes=5):
    """
    Εκτελεί το detect_smart_money() κάθε X λεπτά αυτόματα.
    Τρέχει σε ξεχωριστό thread στο παρασκήνιο.
    """
    def loop():
        while True:
            detect_smart_money()
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[SMART MONEY] 🔁 Auto-refresh active (every {interval_minutes} minutes)")

# -----------------------------
# Συνάρτηση για ανάγνωση cache
# -----------------------------
def get_smart_money_data():
    """
    Επιστρέφει τα τελευταία αποθηκευμένα δεδομένα Smart Money
    χωρίς να ξανακαλέσει APIs (χρησιμοποιείται από το route).
    """
    return {
        "last_update": SMART_MONEY_CACHE["last_update"],
        "results": SMART_MONEY_CACHE["results"]
    }

# -----------------------------
# Εκκίνηση background auto-refresh
# -----------------------------
auto_refresh(5)  # κάθε 5 λεπτά
