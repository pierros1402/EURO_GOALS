# ==============================================
# EURO_GOALS – Football-Data.org Reader
# ==============================================
# Ανάκτηση fixtures, αποτελεσμάτων και στατιστικών
# από το Football-Data.org API.
# Περιλαμβάνει δοκιμή εγκυρότητας API key.
# ==============================================

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# --------------------------------------------------
# Ενεργοποίηση path ώστε να βρίσκει το modules package
# --------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modules.health_check import log_message

# --------------------------------------------------
# 1. Φόρτωση .env και API key
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("FOOTBALLDATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}


# --------------------------------------------------
# 2. Έλεγχος εγκυρότητας API key
# --------------------------------------------------
def check_api_key_valid():
    """Ελέγχει αν το FOOTBALLDATA_API_KEY είναι έγκυρο."""
    test_url = f"{BASE_URL}/competitions/PL/matches"
    try:
        response = requests.get(test_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            log_message("[FOOTBALLDATA] ✅ API key is valid and active.")
            return True
        elif response.status_code == 403:
            log_message("[FOOTBALLDATA] ❌ API key is invalid or expired (403 Forbidden).")
        elif response.status_code == 429:
            log_message("[FOOTBALLDATA] ⚠️ Rate limit exceeded (429 Too Many Requests).")
        else:
            log_message(f"[FOOTBALLDATA] ⚠️ API key test returned status {response.status_code}.")
        return False
    except Exception as e:
        log_message(f"[FOOTBALLDATA] ❌ API key check failed: {e}")
        return False


# --------------------------------------------------
# 3. Λήψη fixtures (SCHEDULED / FINISHED / LIVE)
# --------------------------------------------------
def get_fixtures(competition="PL", status="SCHEDULED"):
    """
    Αντλεί αγώνες (π.χ. Premier League) με βάση την κατάστασή τους.
    status μπορεί να είναι: SCHEDULED, FINISHED, LIVE.
    """
    url = f"{BASE_URL}/competitions/{competition}/matches?status={status}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        matches = []
        for m in data.get("matches", []):
            matches.append({
                "match_id": m["id"],
                "utc_date": m["utcDate"],
                "status": m["status"],
                "home_team": m["homeTeam"]["name"],
                "away_team": m["awayTeam"]["name"],
                "score_home": m["score"]["fullTime"]["home"],
                "score_away": m["score"]["fullTime"]["away"],
                "competition": m["competition"]["name"]
            })

        log_message(f"[FOOTBALLDATA] ✅ Retrieved {len(matches)} matches ({competition} - {status})")
        return matches

    except requests.exceptions.RequestException as e:
        log_message(f"[FOOTBALLDATA] ❌ Request error: {e}")
        return []


# --------------------------------------------------
# 4. Λήψη διαθέσιμων διοργανώσεων
# --------------------------------------------------
def get_competitions():
    """Επιστρέφει λίστα διαθεσίμων διοργανώσεων."""
    try:
        response = requests.get(f"{BASE_URL}/competitions", headers=HEADERS, timeout=10)
        response.raise_for_status()
        comps = [c["code"] for c in response.json().get("competitions", [])]
        log_message(f"[FOOTBALLDATA] ✅ Competitions loaded ({len(comps)} total)")
        return comps
    except Exception as e:
        log_message(f"[FOOTBALLDATA] ⚠️ Error loading competitions: {e}")
        return []


# --------------------------------------------------
# 5. Εκτέλεση δοκιμής
# --------------------------------------------------
if __name__ == "__main__":
    print("🔍 Checking Football-Data API key...")
    if check_api_key_valid():
        comps = get_competitions()
        if "PL" in comps:
            data = get_fixtures("PL", status="SCHEDULED")
            print(f"✅ Retrieved {len(data)} fixtures from Premier League.")
        else:
            print("⚠️ Premier League not found in competitions list.")
    else:
        print("❌ Invalid or expired Football-Data.org API key.")
