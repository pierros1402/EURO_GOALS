# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v6f – Auto Fallback Edition
# ==============================================

import requests
import json
import threading
import time
from datetime import datetime
import random

SMART_MONEY_CACHE = {
    "last_update": None,
    "results": []
}

def detect_smart_money(league="epl"):
    """
    Διαβάζει αποδόσεις από OddsAPI (ή mock fallback αν πέσει το API)
    """
    print(f"[SMART MONEY] 🔍 Checking {league.upper()} odds...")

    api_key = "DEMO_KEY"  # <-- το placeholder key
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={api_key}&regions=eu"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 401 or "Usage quota" in response.text:
            print("[SMART MONEY] ⚠️ API quota reached — switching to mock data.")
            return generate_mock_data(league)

        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            print("[SMART MONEY] ⚠️ Empty API data — using mock fallback.")
            return generate_mock_data(league)

        # Mock μετατροπή δεδομένων API
        results = []
        for item in data[:5]:
            results.append({
                "match": item.get("home_team", "Team A") + " - " + item.get("away_team", "Team B"),
                "odds": {"Home": random.uniform(1.8, 2.3), "Draw": random.uniform(3.0, 3.6), "Away": random.uniform(2.8, 3.4)},
                "time": datetime.now().strftime("%H:%M:%S")
            })

        SMART_MONEY_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SMART_MONEY_CACHE["results"] = results
        print(f"[SMART MONEY] ✅ Updated {len(results)} matches.")
        return results

    except Exception as e:
        print("[SMART MONEY] ❌ API error, switching to mock data:", e)
        return generate_mock_data(league)


def generate_mock_data(league):
    """
    Δημιουργεί εικονικά δεδομένα όταν δεν υπάρχει API ή quota.
    """
    sample_matches = [
        "Olympiacos - AEK",
        "PAOK - Aris",
        "Panathinaikos - Lamia",
        "Manchester City - Liverpool",
        "Juventus - Inter"
    ]

    results = []
    for m in random.sample(sample_matches, k=3):
        results.append({
            "match": m,
            "odds": {
                "Home": round(random.uniform(1.75, 2.40), 2),
                "Draw": round(random.uniform(3.00, 3.70), 2),
                "Away": round(random.uniform(2.80, 3.60), 2)
            },
            "time": datetime.now().strftime("%H:%M:%S")
        })

    SMART_MONEY_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SMART_MONEY_CACHE["results"] = results
    print(f"[SMART MONEY] 🧩 Mock data active ({league.upper()}) – {len(results)} matches.")
    return results


def auto_refresh(interval_minutes=5):
    """
    Εκτελεί το detect_smart_money() κάθε Χ λεπτά στο παρασκήνιο
    """
    def loop():
        while True:
            detect_smart_money()
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[SMART MONEY] 🔁 Auto-refresh active (every {interval_minutes} minutes)")


def get_smart_money_data(league="epl"):
    return {
        "last_update": SMART_MONEY_CACHE["last_update"],
        "results": SMART_MONEY_CACHE["results"]
    }


auto_refresh(5)
