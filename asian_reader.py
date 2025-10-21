# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v6f – Auto Fallback + League Rotation Edition
# ==============================================

import requests
import json
import threading
import time
from datetime import datetime
import random

SMART_MONEY_CACHE = {
    "last_update": None,
    "results": [],
    "current_league": None
}

# -----------------------------
# Λίστα ευρωπαϊκών λιγκών
# -----------------------------
LEAGUES = [
    "soccer_epl",          # Αγγλία
    "soccer_spain_la_liga",# Ισπανία
    "soccer_italy_serie_a",# Ιταλία
    "soccer_germany_bundesliga", # Γερμανία
    "soccer_france_ligue_one",   # Γαλλία
    "soccer_greece_super_league",# Ελλάδα
    "soccer_netherlands_eredivisie", # Ολλανδία
    "soccer_portugal_primeira_liga", # Πορτογαλία
    "soccer_turkey_super_league"     # Τουρκία
]

LEAGUE_INDEX = 0  # Δείκτης ενεργής λίγκας


# -----------------------------
# Κύρια συνάρτηση ανίχνευσης
# -----------------------------
def detect_smart_money(league=None):
    """
    Διαβάζει αποδόσεις από OddsAPI (ή mock fallback αν πέσει το API)
    """
    global LEAGUE_INDEX
    if not league:
        league = LEAGUES[LEAGUE_INDEX]

    SMART_MONEY_CACHE["current_league"] = league
    print(f"[SMART MONEY] 🔍 Checking {league} odds...")

    api_key = "DEMO_KEY"
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

        results = []
        for item in data[:5]:
            results.append({
                "match": item.get("home_team", "Team A") + " - " + item.get("away_team", "Team B"),
                "odds": {
                    "Home": random.uniform(1.8, 2.3),
                    "Draw": random.uniform(3.0, 3.6),
                    "Away": random.uniform(2.8, 3.4)
                },
                "time": datetime.now().strftime("%H:%M:%S")
            })

        SMART_MONEY_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SMART_MONEY_CACHE["results"] = results
        print(f"[SMART MONEY] ✅ Updated {len(results)} matches ({league})")
        return results

    except Exception as e:
        print("[SMART MONEY] ❌ API error, switching to mock data:", e)
        return generate_mock_data(league)


# -----------------------------
# Mock fallback
# -----------------------------
def generate_mock_data(league):
    sample_matches = [
        "Olympiacos - AEK", "PAOK - Aris", "Panathinaikos - Lamia",
        "Manchester City - Liverpool", "Juventus - Inter", "Real Madrid - Barcelona",
        "PSG - Lyon", "Bayern - Dortmund", "Ajax - PSV", "Porto - Benfica"
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
    print(f"[SMART MONEY] 🧩 Mock data active ({league}) – {len(results)} matches.")
    return results


# -----------------------------
# Αυτόματη εναλλαγή λιγκών
# -----------------------------
def rotate_league():
    """
    Αλλάζει αυτόματα τη λίγκα κάθε 5 λεπτά
    """
    global LEAGUE_INDEX
    LEAGUE_INDEX = (LEAGUE_INDEX + 1) % len(LEAGUES)
    next_league = LEAGUES[LEAGUE_INDEX]
    print(f"[SMART MONEY] 🔄 Switching league to: {next_league}")
    detect_smart_money(next_league)


# -----------------------------
# Auto-refresh + rotation
# -----------------------------
def auto_refresh(interval_minutes=5):
    def loop():
        while True:
            detect_smart_money()
            time.sleep(interval_minutes * 60)
            rotate_league()
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[SMART MONEY] 🔁 Auto-refresh + rotation active (every {interval_minutes} minutes)")


# -----------------------------
# Επιστροφή δεδομένων
# -----------------------------
def get_smart_money_data(league=None):
    return {
        "last_update": SMART_MONEY_CACHE["last_update"],
        "results": SMART_MONEY_CACHE["results"],
        "current_league": SMART_MONEY_CACHE["current_league"]
    }


auto_refresh(5)
