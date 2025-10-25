# =======================================================
# ASIAN READER v8.9 – Smart Money Detector (TheOddsAPI)
# =======================================================

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# ===========================================
# Φόρτωση του .env από τον φάκελο EURO_GOALS
# ===========================================
load_dotenv()
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")

if not THEODDS_API_KEY:
    print("[ASIAN READER] ⚠️ THEODDS_API_KEY missing in .env – running in DEMO MODE.")
    DEMO_MODE = True
else:
    DEMO_MODE = False

# ===========================================
# Ευρωπαϊκές Λίγκες (EURO_GOALS Program)
# ===========================================
EURO_LEAGUES = [
    # Αγγλία
    "soccer_epl",
    "soccer_efl_championship",
    "soccer_england_league1",
    "soccer_england_league2",
    # Γερμανία
    "soccer_germany_bundesliga",
    "soccer_germany_bundesliga2",
    "soccer_germany_3_liga",
    # Ελλάδα
    "soccer_greece_super_league",
    "soccer_greece_super_league_2",
    # Ιταλία
    "soccer_italy_serie_a",
    "soccer_italy_serie_b",
    # Ισπανία
    "soccer_spain_la_liga",
    "soccer_spain_segunda_division",
    # Γαλλία
    "soccer_france_ligue_1",
    "soccer_france_ligue_2",
    # Ολλανδία
    "soccer_netherlands_eredivisie",
    # Πορτογαλία
    "soccer_portugal_primeira_liga",
    # Τουρκία
    "soccer_turkey_super_lig",
]

# ===========================================
# Smart Money Detector
# ===========================================
def detect_smart_money():
    """
    Ελέγχει για έντονες μεταβολές αποδόσεων ("Smart Money") σε όλες τις λίγκες του EURO_GOALS.
    """
    print("[ASIAN READER] 🔍 Checking Smart Money movements...")

    if DEMO_MODE:
        return [{"league": "DEMO", "match": "No API key", "movement": "N/A"}]

    alerts = []
    base_url = "https://api.the-odds-api.com/v4/sports"

    for league in EURO_LEAGUES:
        try:
            url = f"{base_url}/{league}/odds?regions=eu&markets=h2h&oddsFormat=decimal&apiKey={THEODDS_API_KEY}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"[ASIAN READER] ⚠️ {league} → API error ({response.status_code})")
                continue

            data = response.json()

            for match in data:
                home = match["home_team"]
                away = match["away_team"]
                bookmakers = match.get("bookmakers", [])

                for book in bookmakers:
                    odds = book.get("markets", [])
                    for market in odds:
                        outcomes = market.get("outcomes", [])
                        if len(outcomes) == 2:
                            try:
                                home_price = float(outcomes[0]["price"])
                                away_price = float(outcomes[1]["price"])

                                # Ενδεικτικό threshold για "Smart Money" alert
                                if abs(home_price - away_price) > 0.5:
                                    alerts.append({
                                        "league": league,
                                        "match": f"{home} vs {away}",
                                        "movement": f"{home_price} / {away_price}",
                                        "timestamp": datetime.now().strftime("%H:%M:%S")
                                    })
                            except:
                                continue

        except Exception as e:
            print(f"[ASIAN READER] ❌ Error in {league}:", e)
            continue

    print(f"[ASIAN READER] ✅ Found {len(alerts)} Smart Money alerts.")
    return alerts
