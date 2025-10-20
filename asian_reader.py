# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v6f – OddsAPI Live Data Edition
# ==============================================

import os, requests, json, threading, time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")
API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"

SMART_MONEY_CACHE = {
    "last_update": None,
    "results": []
}

def detect_smart_money():
    """
    Λήψη πραγματικών αποδόσεων από OddsAPI
    και απλή ανίχνευση μεταβολών (demo).
    """
    print("[SMART MONEY] 🔍 Checking real market data...")

    try:
        params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        res = requests.get(API_URL, params=params, timeout=10)

        if res.status_code != 200:
            print(f"[SMART MONEY] ⚠️ API error: {res.status_code}")
            return []

        data = res.json()
        results = []

        for match in data[:5]:  # δείξε μόνο 5 πρώτους αγώνες για demo
            home = match["home_team"]
            away = match["away_team"]
            bookmaker = match["bookmakers"][0]
            odds = bookmaker["markets"][0]["outcomes"]

            entry = {
                "match": f"{home} - {away}",
                "bookmaker": bookmaker["title"],
                "odds": {o["name"]: o["price"] for o in odds},
                "time": datetime.now().strftime("%H:%M:%S")
            }
            results.append(entry)

        SMART_MONEY_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SMART_MONEY_CACHE["results"] = results

        print(f"[SMART MONEY] ✅ Updated {len(results)} live matches.")
        return results

    except Exception as e:
        print("[SMART MONEY] ❌ Error:", e)
        return []

def auto_refresh(interval_minutes=5):
    def loop():
        while True:
            detect_smart_money()
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[SMART MONEY] 🔁 Auto-refresh active (every {interval_minutes} minutes)")

def get_smart_money_data():
    return {
        "last_update": SMART_MONEY_CACHE["last_update"],
        "results": SMART_MONEY_CACHE["results"]
    }

auto_refresh(5)
