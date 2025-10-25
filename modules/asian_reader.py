# ==============================================
# ASIAN READER v8.8 – Smart Money Detector (TheOddsAPI)
# ==============================================
import os
import requests
from datetime import datetime

# ==============================================
# Ρυθμίσεις & Λίγκες
# ==============================================
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")

# Αν ο χρήστης δεν έχει ορίσει κλειδί στο .env
if not THEODDS_API_KEY:
    print("[ASIAN READER] ⚠️  THEODDS_API_KEY missing in .env – running in DEMO MODE.")
    DEMO_MODE = True
else:
    DEMO_MODE = False

# Λίστα λιγκών (TheOddsAPI sport keys)
LEAGUES = [
    # Αγγλία
    "soccer_epl", "soccer_eng_championship", "soccer_eng_league1",
    "soccer_eng_league2", "soccer_eng_national", "soccer_eng_north",
    "soccer_eng_south",

    # Γερμανία
    "soccer_germany_bundesliga", "soccer_germany_bundesliga2", "soccer_germany_liga3",

    # Ελλάδα
    "soccer_greece_super_league", "soccer_greece_super_league_2", "soccer_greece_league3",

    # Υπόλοιπη Ευρώπη (1–2)
    "soccer_spain_la_liga", "soccer_spain_segunda_division",
    "soccer_italy_serie_a", "soccer_italy_serie_b",
    "soccer_france_ligue_1", "soccer_france_ligue_2",
    "soccer_netherlands_eredivisie", "soccer_netherlands_eerste_divisie",
    "soccer_portugal_primeira_liga", "soccer_portugal_liga2",
    "soccer_belgium_first_div", "soccer_belgium_first_div_b",
    "soccer_turkey_super_lig", "soccer_turkey_1_lig"
]

# Αποθήκευση προηγούμενων αποδόσεων
previous_odds = {}

# Κατώφλι % για alert
THRESHOLD = 5.0

# ==============================================
# Ανάκτηση αποδόσεων
# ==============================================
def fetch_odds(league_key):
    """
    Ανάκτηση live αποδόσεων από το TheOddsAPI για συγκεκριμένη λίγκα.
    """
    if DEMO_MODE:
        # Δοκιμαστικά δεδομένα
        return [
            {
                "home_team": "Demo FC",
                "away_team": "Smart United",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Demo FC", "price": 1.85},
                    {"name": "Draw", "price": 3.60},
                    {"name": "Smart United", "price": 4.20}
                ]}]
            }
        ]

    try:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/"
        params = {
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "apiKey": THEODDS_API_KEY
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            print(f"[ASIAN READER] ❌ Error fetching {league_key}: {r.status_code}")
            return []
        return r.json()
    except Exception as e:
        print(f"[ASIAN READER] ⚠️  Exception in fetch_odds({league_key}):", e)
        return []

# ==============================================
# Ανίχνευση μεταβολών Smart Money
# ==============================================
def detect_smart_money():
    """
    Ανιχνεύει έντονες μεταβολές αποδόσεων/γραμμών από TheOddsAPI.
    Επιστρέφει λίστα από νέα alerts.
    """
    alerts = []
    print("[ASIAN READER] 🔍 Checking Smart Money movements...")

    for league_key in LEAGUES:
        data = fetch_odds(league_key)
        if not data:
            continue

        for match in data:
            home = match.get("home_team")
            away = match.get("away_team")
            mid = f"{home} vs {away}"
            markets = match.get("markets", [])

            for market in markets:
                if market.get("key") != "h2h":
                    continue
                outcomes = market.get("outcomes", [])
                for outcome in outcomes:
                    name = outcome.get("name")
                    price = outcome.get("price")

                    if not price or not name:
                        continue

                    key = f"{league_key}_{mid}_{name}"
                    old_price = previous_odds.get(key)
                    if old_price:
                        try:
                            diff_pct = ((old_price - price) / old_price) * 100
                        except ZeroDivisionError:
                            diff_pct = 0

                        if diff_pct >= THRESHOLD:
                            alert = {
                                "alert_type": "smartmoney",
                                "message": f"💰 Smart Money on {mid} ({name}) dropped {diff_pct:.1f}% in {league_key}",
                                "timestamp": datetime.now().isoformat()
                            }
                            print(f"[SMART MONEY] 💰 {alert['message']}")
                            alerts.append(alert)

                    previous_odds[key] = price

    if not alerts:
        print("[ASIAN READER] No significant Smart Money movements found.")
    return alerts

# ==============================================
# Quick test
# ==============================================
if __name__ == "__main__":
    results = detect_smart_money()
    print(f"Found {len(results)} Smart Money alerts.")
