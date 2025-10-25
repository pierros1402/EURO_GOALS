# ==============================================
# ASIAN READER v8.8 – Smart Money Detector (TheOddsAPI)
# ==============================================

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Φόρτωση .env από τον εξωτερικό φάκελο EURO_GOALS
load_dotenv()

THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")
DEMO_MODE = False if THEODDS_API_KEY else True

print("[ASIAN READER] 🧩 Module active")
if DEMO_MODE:
    print("[ASIAN READER] ⚠️  THEODDS_API_KEY missing – running in DEMO mode.")
else:
    print("[ASIAN READER] ✅ API key loaded successfully.")


# ==============================================
# 1️⃣  Λίγκες προς παρακολούθηση
# ==============================================
LEAGUES = {
    "england": ["premier_league", "championship", "league_one", "league_two"],
    "germany": ["bundesliga", "2_bundesliga", "3_liga"],
    "greece": ["super_league", "super_league_2", "football_league"],
    "spain": ["la_liga", "la_liga2"],
    "italy": ["serie_a", "serie_b"],
    "france": ["ligue_1", "ligue_2"],
    "netherlands": ["eredivisie", "eerste_divisie"],
    "portugal": ["primeira_liga", "segunda_liga"]
}

# ==============================================
# 2️⃣  Κύρια συνάρτηση Smart Money Detection
# ==============================================
def detect_smart_money():
    print("[ASIAN READER] 🔍 Checking Smart Money movements...")

    movements = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if DEMO_MODE:
        # Δείγμα για επίδειξη
        movements.append({
            "league": "Premier League",
            "match": "Liverpool vs Chelsea",
            "movement": "-0.35 Asian line drift (Liverpool)",
            "timestamp": now
        })
        print("[ASIAN READER] 🧪 DEMO mode sample movement added.")
    else:
        try:
            for country, leagues in LEAGUES.items():
                for league in leagues:
                    url = f"https://api.the-odds-api.com/v4/sports/{country}-{league}/odds"
                    params = {"apiKey": THEODDS_API_KEY, "regions": "eu", "markets": "h2h,spreads"}
                    r = requests.get(url, params=params)
                    if r.status_code == 200:
                        data = r.json()
                        for game in data:
                            home = game["home_team"]
                            away = game["away_team"]
                            bookmakers = game.get("bookmakers", [])
                            for b in bookmakers:
                                if "Asian Handicap" in b.get("title", ""):
                                    # placeholder rule
                                    movements.append({
                                        "league": league,
                                        "match": f"{home} vs {away}",
                                        "movement": "Asian line shift detected",
                                        "timestamp": now
                                    })
                    else:
                        print(f"[ASIAN READER] ⚠️ League {league} skipped (status {r.status_code})")

        except Exception as e:
            print("[ASIAN READER] ❌ Error:", e)

    # ==============================================
    # 3️⃣  Αποθήκευση σε log αρχείο
    # ==============================================
    log_entry = {"timestamp": now, "alerts": movements}
    log_path = os.path.join(os.getcwd(), "smartmoney_log.json")

    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(log_entry)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[ASIAN READER] 💾 Log updated ({len(movements)} alerts).")

    except Exception as e:
        print("[ASIAN READER] ⚠️ Could not save log:", e)

    print(f"[ASIAN READER] ✅ Scan complete at {now}")
    return movements


# ==============================================
# 4️⃣  Test Execution
# ==============================================
if __name__ == "__main__":
    results = detect_smart_money()
    print(json.dumps(results, indent=2, ensure_ascii=False))
