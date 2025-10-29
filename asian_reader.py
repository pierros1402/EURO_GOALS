# ============================================================
# ASIAN READER MODULE – EURO_GOALS v8.9g
# Σύνδεση με AsianOdds / AsianConnect API + Smart Money Detection
# ============================================================

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# 1️⃣ Περιβάλλον & Global μεταβλητές
# ------------------------------------------------------------
ASIAN_API_KEY = os.getenv("ASIANCONNECT_API_KEY", "demo-key")
ASIAN_BASE_URL = os.getenv("ASIANCONNECT_BASE_URL", "https://api.asianconnect88.com")
USE_MOCK = os.getenv("ASIANCONNECT_MOCK_MODE", "True").lower() == "true"

LOG_FILE = "asian_reader_log.txt"

# ------------------------------------------------------------
# 2️⃣ Mock data (αν δεν έχουμε ακόμα πραγματικό API)
# ------------------------------------------------------------
MOCK_RESPONSE = {
    "status": "success",
    "timestamp": str(datetime.now()),
    "matches": [
        {
            "league": "Premier League",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "market": "Asian Handicap",
            "odds_home": 1.87,
            "odds_away": 2.05,
            "bookmaker": "Pinnacle",
            "last_update": str(datetime.now())
        },
        {
            "league": "La Liga",
            "home_team": "Real Madrid",
            "away_team": "Sevilla",
            "market": "Over/Under 2.5",
            "odds_over": 1.92,
            "odds_under": 1.89,
            "bookmaker": "SBOBET",
            "last_update": str(datetime.now())
        }
    ]
}

# ------------------------------------------------------------
# 3️⃣ Συνάρτηση για ανάκτηση δεδομένων από API
# ------------------------------------------------------------
def get_asian_odds():
    """Επιστρέφει Asian market δεδομένα (API ή mock)."""
    try:
        if USE_MOCK:
            log_event("Mock mode active – returning sample data.")
            return MOCK_RESPONSE

        headers = {"Authorization": f"Bearer {ASIAN_API_KEY}"}
        url = f"{ASIAN_BASE_URL}/v1/odds"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            log_event(f"✅ Data fetched successfully: {len(data.get('matches', []))} matches")
            return data
        else:
            log_event(f"⚠️ API returned {response.status_code}")
            return {"status": "error", "code": response.status_code}

    except Exception as e:
        log_event(f"❌ Error in get_asian_odds: {e}")
        return {"status": "error", "message": str(e)}

# ------------------------------------------------------------
# 4️⃣ Smart Money detection logic
# ------------------------------------------------------------
def detect_smart_money(threshold: float = 0.05):
    """
    Ανιχνεύει απότομες μεταβολές στις αποδόσεις (> threshold).
    """
    data = get_asian_odds()
    suspicious = []

    if data.get("status") != "success":
        return suspicious

    for match in data.get("matches", []):
        if "odds_home" in match and "odds_away" in match:
            diff = abs(match["odds_home"] - match["odds_away"])
            if diff > threshold:
                suspicious.append(match)

    log_event(f"Smart Money check complete: {len(suspicious)} suspicious matches found.")
    return suspicious

# ------------------------------------------------------------
# 5️⃣ Logging utility
# ------------------------------------------------------------
def log_event(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(f"[ASIAN_READER] {msg}")

# ------------------------------------------------------------
# 6️⃣ Manual test
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Running Asian Reader test...\n")
    data = detect_smart_money()
    print(json.dumps(data, indent=2))
