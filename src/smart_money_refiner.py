# ==============================================
# SMART MONEY REFINER MODULE (EURO_GOALS v8)
# ==============================================
# Ανιχνεύει μεταβολές αποδόσεων/ασιατικών γραμμών
# από γνωστές πηγές (Pinnacle, SBOBET, 188BET, κ.λπ.)
# και επιστρέφει δομημένα alerts
# ==============================================

import requests
import random
from datetime import datetime

# ------------------------------------------------
# Εσωτερική συνάρτηση απλής εκτύπωσης alert
# ------------------------------------------------
def send_alert(msg):
    """Προσωρινή αντικατάσταση της add_alert_direct"""
    print(f"[ALERT] 🔔 {msg}")

# ------------------------------------------------
# Κύρια συνάρτηση ανίχνευσης Smart Money
# ------------------------------------------------
def detect_smart_money():
    """
    Ελέγχει τις τελευταίες αποδόσεις από πηγές (dummy mode)
    και επιστρέφει λίστα alerts για ύποπτες μεταβολές.
    """

    print("[SMART MONEY] 🔍 Checking Asian market data...")

    try:
        # Προσωρινές εικονικές τιμές
        sample_games = [
            ("Chelsea vs Arsenal", 1.92, 1.78, "Pinnacle"),
            ("Bayern vs Dortmund", 2.10, 1.95, "SBOBET"),
            ("PAOK vs AEK", 2.35, 2.10, "188BET"),
        ]

        alerts = []

        for match, old, new, source in sample_games:
            delta = round(old - new, 2)
            if abs(delta) >= 0.10:
                msg = f"Smart Money Detected – {source}: {match} odds moved {old} → {new} (Δ{delta:+.2f})"
                alerts.append({
                    "match": match,
                    "source": source,
                    "old": old,
                    "new": new,
                    "delta": delta,
                    "message": msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                send_alert(msg)

        print(f"[SMART MONEY] ✅ Completed ({len(alerts)} signals found)")
        return {"status": "ok", "count": len(alerts), "alerts": alerts}

    except Exception as e:
        print("[SMART MONEY] ❌ Error:", e)
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Εκτέλεση δοκιμής (αν τρέξει απευθείας το αρχείο)
# ------------------------------------------------
if __name__ == "__main__":
    print("Running Smart Money Refiner test mode...")
    result = detect_smart_money()
    print(result)
