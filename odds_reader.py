# odds_reader.py
# ==============================================================
# EURO_GOALS Odds Reader (TheOddsAPI + SofaScore combined)
# ==============================================================

import os
import time
import json
import requests
from datetime import datetime, timedelta

# ==============================================================
# Βασικές ρυθμίσεις API
# ==============================================================

THEODDS_KEY = os.environ.get("THEODDS_API_KEY")
BASE = "https://api.the-odds-api.com/v4"
REGIONS = "eu"
MARKETS = "h2h"
ODDS_FMT = "decimal"

# ==============================================================
# Simple in-memory cache (ώστε να μην γίνονται πολλά API calls)
# ==============================================================
CACHE = {}
TTL = timedelta(minutes=5)  # 5 λεπτά caching

def _cache_get(key):
    ent = CACHE.get(key)
    if not ent:
        return None
    if datetime.utcnow() - ent["ts"] > TTL:
        return None
    return ent["data"]

def _cache_set(key, data):
    CACHE[key] = {"data": data, "ts": datetime.utcnow()}

# ==============================================================
# Λειτουργία απλού fetch για 1 πρωτάθλημα
# ==============================================================

def get_odds(sport_key: str, mode: str = "simple"):
    """
    Παίρνει αποδόσεις για συγκεκριμένο πρωτάθλημα (sport_key)
    Παραδείγματα:
      /odds/soccer_epl
      /odds/soccer_greece_super_league
    """
    cached = _cache_get(sport_key)
    if cached:
        return cached

    url = f"{BASE}/sports/{sport_key}/odds/"
    params = {
        "apiKey": THEODDS_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FMT,
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"[get_odds] Error fetching {sport_key}: {e}")
        return {"count": 0, "events": []}

    events = []
    for match in data:
        try:
            home = match["home_team"]
            away = match["away_team"]
            odds = match["bookmakers"][0]["markets"][0]["outcomes"]
            odds_dict = {o["name"]: o["price"] for o in odds}
            events.append({
                "match": f"{home} - {away}",
                "odds": odds_dict,
                "sources": ["TheOddsAPI"]
            })
        except Exception:
            continue

    out = {"sport_key": sport_key, "count": len(events), "events": events}
    _cache_set(sport_key, out)
    return out

# ==============================================================
# Bundle odds fetcher (multiple leagues)
# ==============================================================

def get_odds_bundle(bundle: str):
    """
    Επιστρέφει ενωμένα δεδομένα αποδόσεων για ομάδες διοργανώσεων.
    Π.χ. england_all, greece_1_2_3, germany_1_2_3, europe_1_2
    """
    bundles = {
        "england_all": [
            "soccer_epl",
            "soccer_england_championship",
            "soccer_england_league1",
            "soccer_england_league2"
        ],
        "greece_1_2_3": [
            "soccer_greece_super_league",
            "soccer_greece_league_one",
            "soccer_greece_league_two"
        ],
        "germany_1_2_3": [
            "soccer_germany_bundesliga",
            "soccer_germany_bundesliga2",
            "soccer_germany_bundesliga3"
        ],
        "europe_1_2": [
            "soccer_spain_la_liga",
            "soccer_spain_segunda_division",
            "soccer_italy_serie_a",
            "soccer_italy_serie_b",
            "soccer_france_ligue_one",
            "soccer_france_ligue_two",
            "soccer_portugal_primeira_liga",
            "soccer_belgium_first_div",
            "soccer_netherlands_eredivisie",
            "soccer_austria_bundesliga",
            "soccer_switzerland_superleague",
            "soccer_turkey_super_league",
            "soccer_norway_eliteserien",
            "soccer_sweden_allsvenskan",
            "soccer_denmark_superliga"
        ]
    }

    leagues = bundles.get(bundle, [])
    combined = {"count": 0, "events": []}

    for key in leagues:
        try:
            data = get_odds(key)
            combined["events"].extend(data.get("events", []))
            combined["count"] += data.get("count", 0)
        except Exception as e:
            print(f"[get_odds_bundle] Error fetching {key}: {e}")

    return combined
