# ==============================================
# EURO_GOALS – API-FOOTBALL Reader (Final v4)
# ==============================================
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modules.health_check import log_message

# --------------------------------------------------
# 1. Φόρτωση .env και API key
# --------------------------------------------------
load_dotenv()
API_KEY = os.getenv("APIFOOTBALL_API_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "Accept-Encoding": "gzip"}


# --------------------------------------------------
# 2. Έλεγχος εγκυρότητας API key
# --------------------------------------------------
def check_api_key_valid():
    try:
        r = requests.get(f"{BASE_URL}/status", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            log_message("[APIFOOTBALL] ✅ API key is valid and active.")
            return True
        log_message(f"[APIFOOTBALL] ⚠️ Key check returned {r.status_code}")
        return False
    except Exception as e:
        log_message(f"[APIFOOTBALL] ❌ Error: {e}")
        return False


# --------------------------------------------------
# 3. Εύρεση ενεργής σεζόν (με ημερομηνίες)
# --------------------------------------------------
def get_current_season(league_id=39):
    """
    Επιστρέφει τη σωστή σεζόν που περιλαμβάνει την τρέχουσα ημερομηνία.
    Αν δεν υπάρχει, επιλέγει την τελευταία ενεργή completed.
    """
    try:
        resp = requests.get(f"{BASE_URL}/leagues?id={league_id}", headers=HEADERS, timeout=10)
        data = resp.json().get("response", [])
        if not data:
            return None

        seasons = data[0].get("seasons", [])
        if not seasons:
            return None

        today = datetime.now(timezone.utc).date()

        # 🔍 Έλεγχος ημερομηνιών έναρξης/λήξης
        for s in seasons:
            start = s.get("start")
            end = s.get("end")
            if start and end:
                try:
                    start_date = datetime.strptime(start, "%Y-%m-%d").date()
                    end_date = datetime.strptime(end, "%Y-%m-%d").date()
                    if start_date <= today <= end_date:
                        return s.get("year")  # ✅ αυτή είναι η σωστή τρέχουσα
                except Exception:
                    continue

        # Αν δεν βρεθεί τρέχουσα, πάρε την πιο πρόσφατη completed
        if len(seasons) > 1:
            return seasons[-2].get("year")

        return seasons[-1].get("year")

    except Exception as e:
        log_message(f"[APIFOOTBALL] ⚠️ Season fetch error: {e}")
        return None


# --------------------------------------------------
# 4. Fixtures για τη λίγκα
# --------------------------------------------------
def get_fixtures(league_id=39):
    season = get_current_season(league_id) or 2024
    if season == 2025:
        season = 2024  # 🔧 προσωρινό fix – API στέλνει μελλοντική σεζόν

    try:
        url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("response", [])
        log_message(f"[APIFOOTBALL] ✅ Retrieved {len(data)} fixtures (league={league_id}, season={season}).")
        return data
    except Exception as e:
        log_message(f"[APIFOOTBALL] ❌ Fixtures error: {e}")
        return []


# --------------------------------------------------
# 5. Odds για τη λίγκα
# --------------------------------------------------
def get_odds(league_id=39):
    season = get_current_season(league_id) or 2024
    if season == 2025:
        season = 2024  # 🔧 προσωρινό fix – API στέλνει μελλοντική σεζόν

    try:
        url = f"{BASE_URL}/odds?league={league_id}&season={season}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json().get("response", [])
        log_message(f"[APIFOOTBALL] 💰 Retrieved {len(data)} odds entries (league={league_id}, season={season}).")
        return data
    except Exception as e:
        log_message(f"[APIFOOTBALL] ❌ Odds error: {e}")
        return []


# --------------------------------------------------
# 6. Εκτέλεση δοκιμής (όταν τρέχει μόνο του)
# --------------------------------------------------
if __name__ == "__main__":
    print("🔍 Checking API-FOOTBALL connection...")
    if check_api_key_valid():
        fixtures = get_fixtures(league_id=39)
        print(f"📅 Fixtures found: {len(fixtures)}")
        odds = get_odds(league_id=39)
        print(f"💰 Odds entries found: {len(odds)}")
    else:
        print("❌ Invalid API key.")
