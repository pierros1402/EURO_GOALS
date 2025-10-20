# ==============================================
# ASIAN READER MODULE (Smart Money Detector)
# EURO_GOALS v6f – OddsAPI Multi-League Edition
# ==============================================

import os, requests, json, threading, time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 🔑 OddsAPI settings
API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# -----------------------------
# Διαθέσιμες λίγκες (codes για API)
# -----------------------------
LEAGUE_URLS = {
    # 🇬🇧 Αγγλία
    "eng1": "soccer_epl",                      # Premier League
    "eng2": "soccer_england_championship",     # Championship
    "eng3": "soccer_england_league1",          # League One
    "eng4": "soccer_england_league2",          # League Two

    # 🇩🇪 Γερμανία
    "ger1": "soccer_germany_bundesliga",
    "ger2": "soccer_germany_bundesliga2",
    "ger3": "soccer_germany_3_liga",

    # 🇬🇷 Ελλάδα
    "gr1": "soccer_greece_super_league",
    "gr2": "soccer_greece_super_league_2",

    # 🇪🇸 Ισπανία
    "es1": "soccer_spain_la_liga",
    "es2": "soccer_spain_segunda_division",

    # 🇮🇹 Ιταλία
    "it1": "soccer_italy_serie_a",
    "it2": "soccer_italy_serie_b",

    # 🇫🇷 Γαλλία
    "fr1": "soccer_france_ligue_one",
    "fr2": "soccer_france_ligue_two",

    # 🇳🇱 Ολλανδία
    "nl1": "soccer_netherlands_eredivisie",
    "nl2": "soccer_netherlands_eerste_divisie",

    # 🇧🇪 Βέλγιο
    "be1": "soccer_belgium_first_div",
    "be2": "soccer_belgium_first_div_b",

    # 🇨🇭 Ελβετία
    "ch1": "soccer_switzerland_superleague",
    "ch2": "soccer_switzerland_challenge_league",

    # 🇦🇹 Αυστρία
    "at1": "soccer_austria_bundesliga",
    "at2": "soccer_austria_2_liga",

    # 🇩🇰 Δανία
    "dk1": "soccer_denmark_superliga",
    "dk2": "soccer_denmark_1st_division",

    # 🇳🇴 Νορβηγία
    "no1": "soccer_norway_eliteserien",
    "no2": "soccer_norway_1st_division",

    # 🇸🇪 Σουηδία
    "se1": "soccer_sweden_allsvenskan",
    "se2": "soccer_sweden_superettan",

    # 🇫🇮 Φινλανδία
    "fi1": "soccer_finland_veikkausliiga",
    "fi2": "soccer_finland_ykkonen",

    # 🇮🇪 Ιρλανδία
    "ie1": "soccer_ireland_premier_division",
    "ie2": "soccer_ireland_first_division",

    # 🇮🇸 Ισλανδία
    "is1": "soccer_iceland_urvalsdeild",
    "is2": "soccer_iceland_1st_division",

    # 🇵🇹 Πορτογαλία
    "pt1": "soccer_portugal_primeira_liga",
    "pt2": "soccer_portugal_2nd_division",

    # 🇵🇱 Πολωνία
    "pl1": "soccer_poland_ekstraklasa",
    "pl2": "soccer_poland_1_liga",

    # 🇨🇿 Τσεχία
    "cz1": "soccer_czech_republic_fnl",
    "cz2": "soccer_czech_republic_2_liga",

    # 🇭🇺 Ουγγαρία
    "hu1": "soccer_hungary_nb_i",
    "hu2": "soccer_hungary_nb_ii",

    # 🇷🇴 Ρουμανία
    "ro1": "soccer_romania_liga_1",
    "ro2": "soccer_romania_liga_2",

    # 🌍 Ευρωπαϊκές Διοργανώσεις
    "ucl": "soccer_uefa_champs_league",
    "uel": "soccer_uefa_europa_league",
    "uecl": "soccer_uefa_europa_conf_league"
}
}

# -----------------------------
# Cache για το Smart Money
# -----------------------------
SMART_MONEY_CACHE = {
    "last_update": None,
    "results": [],
    "league": "epl"
}


# -----------------------------
# Κύρια συνάρτηση
# -----------------------------
def detect_smart_money(league="epl"):
    """
    Λήψη πραγματικών αποδόσεων από OddsAPI
    για τη συγκεκριμένη λίγκα.
    """
    sport = LEAGUE_URLS.get(league, "soccer_epl")
    API_URL = f"{BASE_URL}/{sport}/odds/"

    print(f"[SMART MONEY] 🔍 Checking {league.upper()} odds from OddsAPI...")

    try:
        params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        res = requests.get(API_URL, params=params, timeout=10)

        if res.status_code != 200:
            print(f"[SMART MONEY] ⚠️ API error {res.status_code}: {res.text}")
            return []

        data = res.json()
        results = []

        for match in data[:6]:  # δείχνουμε max 6 αγώνες για καθαρότητα
            home = match.get("home_team", "-")
            away = match.get("away_team", "-")
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
        SMART_MONEY_CACHE["league"] = league

        print(f"[SMART MONEY] ✅ Updated {len(results)} matches ({league.upper()}).")
        return results

    except Exception as e:
        print("[SMART MONEY] ❌ Error:", e)
        return []


# -----------------------------
# Συνάρτηση ανάγνωσης cache
# -----------------------------
def get_smart_money_data(league="epl"):
    """
    Επιστρέφει τα τελευταία αποθηκευμένα δεδομένα Smart Money.
    Αν ζητηθεί διαφορετική λίγκα, κάνει νέο fetch.
    """
    if SMART_MONEY_CACHE["league"] != league:
        detect_smart_money(league)
    return {
        "last_update": SMART_MONEY_CACHE["last_update"],
        "results": SMART_MONEY_CACHE["results"]
    }


# -----------------------------
# Αυτόματη ανανέωση κάθε 5’
# -----------------------------
def auto_refresh(interval_minutes=5):
    def loop():
        while True:
            detect_smart_money(SMART_MONEY_CACHE["league"])
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[SMART MONEY] 🔁 Auto-refresh active (every {interval_minutes} minutes)")


# -----------------------------
# Εκκίνηση background thread
# -----------------------------
auto_refresh(5)
