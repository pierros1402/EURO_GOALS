# odds_reader.py
# -------------------------------------------------------------
# EURO_GOALS Odds Reader (TheOddsAPI + SofaScore combined)
# -------------------------------------------------------------
import os, time, json, requests
from datetime import datetime, timedelta

CACHE = {}
CACHE_EXPIRY = timedelta(minutes=5)  # 5 λεπτά caching

THEODDS_KEY = os.environ.get("THEODDS_API_KEY")

def log(msg):
    print(f"[odds_reader] {msg}")

# ==============================================================
# Helper: read cached data
# ==============================================================
def get_cached(sport_key, mode):
    now = datetime.now()
    if (sport_key, mode) in CACHE:
        item = CACHE[(sport_key, mode)]
        if now - item["time"] < CACHE_EXPIRY:
            log(f"Cache hit for {sport_key} ({mode})")
            return item["data"]
    return None

def set_cache(sport_key, mode, data):
    CACHE[(sport_key, mode)] = {"time": datetime.now(), "data": data}

# ==============================================================
# 1️⃣ Fetch from TheOddsAPI
# ==============================================================
def fetch_theoddsapi(sport_key):
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        params = {"regions": "eu", "markets": "h2h", "apiKey": THEODDS_KEY}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            log(f"TheOddsAPI error {r.status_code}: {r.text}")
            return []
        return r.json()
    except Exception as e:
        log(f"TheOddsAPI exception: {e}")
        return []

# ==============================================================
# 2️⃣ Fetch from SofaScore (public prediction vote)
# ==============================================================
def fetch_sofascore_votes(team_home, team_away):
    try:
        # Very simple public endpoint pattern:
        query = f"{team_home}-{team_away}".lower().replace(" ", "-")
        url = f"https://api.sofascore.com/api/v1/search/{query}"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        # Simulate pseudo-vote (demo)
        votes = {"1": 0.6, "X": 0.2, "2": 0.2}
        return votes
    except Exception as e:
        log(f"SofaScore exception: {e}")
        return None

# ==============================================================
# 3️⃣ Compute trend index
# ==============================================================
def compute_trend(odds):
    try:
        inv = {k: 1/v for k, v in odds.items() if v > 0}
        total = sum(inv.values())
        return {k: round(v/total, 2) for k, v in inv.items()}
    except Exception:
        return {"1": 0.0, "X": 0.0, "2": 0.0}

# ==============================================================
# 4️⃣ Main function
# ==============================================================
def get_odds(sport_key: str, mode: str = "simple"):
    # Check cache
    cached = get_cached(sport_key, mode)
    if cached:
        return cached

    log(f"Fetching odds for {sport_key} in mode {mode}...")

    data = fetch_theoddsapi(sport_key)
    results = []
    for ev in data[:10]:  # limit for demo
        if "bookmakers" not in ev: continue
        home = ev.get("home_team", "?")
        away = ev.get("away_team", "?")
        odds_data = {}
        try:
            markets = ev["bookmakers"][0]["markets"][0]["outcomes"]
            for o in markets:
                name = o["name"]
                if name == home: odds_data["1"] = o["price"]
                elif name == "Draw": odds_data["X"] = o["price"]
                elif name == away: odds_data["2"] = o["price"]
        except Exception:
            continue

        trend = compute_trend(odds_data)

        if mode == "combined":
            votes = fetch_sofascore_votes(home, away)
            if votes:
                # merge vote influence 50/50
                for k in trend.keys():
                    trend[k] = round((trend[k] + votes.get(k, 0)) / 2, 2)

        results.append({
            "match": f"{home} - {away}",
            "odds": odds_data,
            "trend_index": trend,
            "mode": mode,
            "sources": ["TheOddsAPI"] + (["SofaScore"] if mode == "combined" else [])
        })

    final = {"count": len(results), "events": results}
    set_cache(sport_key, mode, final)
    return final
