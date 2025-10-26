# =======================================================
# ASIAN READER v8.9 – Smart Money Detector (TheOddsAPI)
# =======================================================

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Φόρτωση .env (τοπικά). Στο Render μπαίνει από Environment.
load_dotenv()
THEODDS_API_KEY = os.getenv("THEODDS_API_KEY")
DEMO_MODE = not bool(THEODDS_API_KEY)

if DEMO_MODE:
    print("[ASIAN READER] ⚠️ THEODDS_API_KEY missing – running in DEMO mode.")
else:
    print("[ASIAN READER] ✅ API key loaded.")

# TheOddsAPI sport keys (EU only, χωρίς κύπελλα)
EURO_LEAGUES = [
    # Αγγλία
    "soccer_epl",
    "soccer_eng_championship",
    "soccer_eng_league1",
    "soccer_eng_league2",
    # Γερμανία
    "soccer_germany_bundesliga",
    "soccer_germany_bundesliga2",
    "soccer_germany_liga3",
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
    "soccer_netherlands_eerste_divisie",
    # Πορτογαλία
    "soccer_portugal_primeira_liga",
    "soccer_portugal_liga2",
    # Τουρκία
    "soccer_turkey_super_lig",
    "soccer_turkey_1_lig",
]

LOG_JSON = "smartmoney_log.json"

def detect_smart_money():
    """
    Ελέγχει τις λίγκες και επιστρέφει λίστα alerts.
    Τώρα απλός κανόνας: αν διαφορά H2H τιμών > 0.5 → alert (demo heuristic).
    """
    print("[ASIAN READER] 🔍 Checking Smart Money movements...")
    alerts = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if DEMO_MODE:
        alerts.append({
            "league": "DEMO",
            "match": "Demo FC vs Smart United",
            "movement": "price diff 0.7",
            "timestamp": now
        })
        _append_log(now, alerts)
        print(f"[ASIAN READER] ✅ Found {len(alerts)} demo alerts.")
        return alerts

    base = "https://api.the-odds-api.com/v4/sports"
    for league in EURO_LEAGUES:
        try:
            url = f"{base}/{league}/odds"
            params = {
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "apiKey": THEODDS_API_KEY
            }
            r = requests.get(url, params=params, timeout=12)
            if r.status_code != 200:
                print(f"[ASIAN READER] ⚠️ {league}: status {r.status_code}")
                continue
            data = r.json()
            for match in data:
                home = match.get("home_team")
                away = match.get("away_team")
                for book in match.get("bookmakers", []):
                    for m in book.get("markets", []):
                        if m.get("key") != "h2h":
                            continue
                        outcomes = m.get("outcomes", [])
                        if len(outcomes) >= 2:
                            try:
                                p1 = float(outcomes[0]["price"])
                                p2 = float(outcomes[1]["price"])
                                if abs(p1 - p2) > 0.5:
                                    alerts.append({
                                        "league": league,
                                        "match": f"{home} vs {away}",
                                        "movement": f"{p1} / {p2}",
                                        "timestamp": now
                                    })
                                    # first useful alert per bookmaker is enough
                                    break
                            except Exception:
                                pass
        except Exception as e:
            print(f"[ASIAN READER] ❌ {league}: {e}")

    _append_log(now, alerts)
    print(f"[ASIAN READER] ✅ Found {len(alerts)} alerts.")
    return alerts

def _append_log(ts, alerts):
    """Προσθέτει τα αποτελέσματα σε smartmoney_log.json"""
    entry = {"timestamp": ts, "alerts": alerts}
    try:
        data = []
        if os.path.exists(LOG_JSON):
            with open(LOG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append(entry)
        with open(LOG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[ASIAN READER] 💾 Log updated.")
    except Exception as e:
        print("[ASIAN READER] ⚠️ Log write failed:", e)

if __name__ == "__main__":
    print(json.dumps(detect_smart_money(), indent=2, ensure_ascii=False))
