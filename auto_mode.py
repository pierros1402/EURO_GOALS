# ==============================================
# AUTO MODE MODULE – Smart Money Alert Engine
# EURO_GOALS v6f – Combines Odds + Stake Volumes
# ==============================================

import threading
import time
from datetime import datetime
from asian_reader import detect_smart_money
from market_reader import detect_market_volumes, MARKET_CACHE

SMART_ALERTS_CACHE = {
    "last_update": None,
    "alerts": []
}


def analyze_smart_money():
    """
    Συνδυάζει αποδόσεις (asian_reader) και volumes (market_reader)
    για να εντοπίσει ύποπτες κινήσεις “Smart Money”.
    """
    print("[AUTO MODE] 🔍 Analyzing odds & stake volumes...")

    try:
        # 1️⃣ Λήψη νέων δεδομένων
        odds_data = detect_smart_money("epl")  # προσωρινά EPL
        volumes_data = detect_market_volumes()

        alerts = []
        for v in volumes_data:
            match_name = v["match"]

            # Αναζήτηση αντίστοιχου match στα odds
            o_match = next((o for o in odds_data if o["match"] == match_name), None)
            if not o_match:
                continue

            # Υπολογισμός ποσοστιαίας διαφοράς μεταξύ odds & volume
            home_odds = o_match["odds"].get("Home", 0)
            away_odds = o_match["odds"].get("Away", 0)

            total_volume = v.get("total_volume", 0)
            dominant = v.get("dominant_side", "-")

            # Εύρεση κατεύθυνσης (π.χ. έπεσε απόδοση στο Home και αυξήθηκε volume)
            if dominant == "1" and home_odds < 2.0:
                alerts.append({
                    "match": match_name,
                    "signal": "Smart Money on HOME",
                    "odds": home_odds,
                    "volume": total_volume,
                    "time": datetime.now().strftime("%H:%M:%S")
                })
            elif dominant == "2" and away_odds < 3.0:
                alerts.append({
                    "match": match_name,
                    "signal": "Smart Money on AWAY",
                    "odds": away_odds,
                    "volume": total_volume,
                    "time": datetime.now().strftime("%H:%M:%S")
                })

        SMART_ALERTS_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SMART_ALERTS_CACHE["alerts"] = alerts

        print(f"[AUTO MODE] ✅ {len(alerts)} Smart Money signals detected.")
        return alerts

    except Exception as e:
        print("[AUTO MODE] ❌ Error:", e)
        return []


def get_alerts():
    return SMART_ALERTS_CACHE


def auto_refresh(interval_minutes=5):
    def loop():
        while True:
            analyze_smart_money()
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[AUTO MODE] 🔁 Smart Money Auto Mode active (every {interval_minutes} min)")


# Εκκίνηση αυτόματα
auto_refresh(5)
