# odds_reader.py
# EURO_GOALS Odds Reader (TheOddsAPI) — group fetcher with smart key matching

import os, time, requests, re
from datetime import datetime, timedelta

THEODDS_KEY = os.environ.get("THEODDS_API_KEY")
BASE = "https://api.the-odds-api.com/v4"
REGIONS = "eu"
MARKETS = "h2h"
ODDS_FMT = "decimal"

# Απλό in-memory cache για να μη χτυπάμε συνέχεια το API
CACHE = {}
TTL = timedelta(minutes=5)

def _cache_get(key):
    ent = CACHE.get(key)
    if not ent: return None
    if datetime.utcnow() - ent["ts"] > TTL:
        return None
    return ent["data"]

def _cache_put(key, data):
    CACHE[key] = {"ts": datetime.utcnow(), "data": data}

def _get(url, params=None):
    if not params: params = {}
    params.update({"apiKey": THEODDS_KEY})
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def list_sports():
    """Φέρνει τη λίστα με όλα τα διαθέσιμα sport keys και την κρατά 5’ στο cache."""
    ck = "sports_list"
    hit = _cache_get(ck)
    if hit is not None:
        return hit
    data = _get(f"{BASE}/sports")
    _cache_put(ck, data)
    return data

def _norm(s: str) -> str:
    return s.lower().replace("-", "_").replace(" ", "_")

def _filter_keys(country_word: str, tiers: list[str]) -> list[str]:
    """
    Βρίσκει sport_keys για μια χώρα, με προτεραιότητα (tiers) π.χ.:
    tiers = ["epl","championship","league_one","league_two"]
           ή ["bundesliga","bundesliga2","3"]
           ή ["super","super_2","3"]
    """
    sports = list_sports()
    keys = []
    for tier in tiers:
        # βρίσκουμε το πρώτο key που ταιριάζει στη χώρα ΚΑΙ στον tier
        pat_country = re.compile(country_word, re.I)
        pat_tier = re.compile(tier, re.I)
        found = None
        for s in sports:
            key = s.get("key","")
            if pat_country.search(key) and pat_tier.search(key):
                found = key
                break
        if found:
            keys.append(found)
    # αφαιρούμε duplicates κρατώντας σειρά
    dedup = []
    for k in keys:
        if k not in dedup:
            dedup.append(k)
    return dedup

def resolve_bundle(bundle_name: str) -> list[str]:
    """
    Επιστρέφει λίστα από sport_keys ανά bundle.
    - england_all: EPL, Championship, League One, League Two
    - greece_1_2_3: Super League, Super League 2, 3η κατηγορία (αν υπάρχει)
    - germany_1_2_3: Bundesliga, Bundesliga 2, 3. Liga
    - europe_1_2: top-2 κατηγορίες για πολλές χώρες
    """
    name = _norm(bundle_name)

    if name == "england_all":
        return _filter_keys("england|epl", ["epl","championship","league_?one","league_?two"])

    if name == "greece_1_2_3":
        # super league + super league 2 + 3ο επίπεδο αν υφίσταται
        keys = _filter_keys("greece", ["super", "super.*2", "3|third|gamma"])
        return keys

    if name == "germany_1_2_3":
        # bundesliga + 2. bundesliga + 3. liga
        return _filter_keys("germany", ["bundesliga(?!2)$", "bundesliga2|2", "3|dritte|liga"])

    if name == "europe_1_2":
        countries = [
            ("spain",   ["la[_ ]?liga(?!2)$","liga2|segunda"]),
            ("italy",   ["serie[_ ]?a$","serie[_ ]?b$"]),
            ("france",  ["ligue[_ ]?1$","ligue[_ ]?2$"]),
            ("nether|neth|holland", ["eredivisie","eerste|keuken"]),
            ("belg",    ["first[_ ]?division[_ ]?a","first[_ ]?division[_ ]?b|challenger|proximus|deux"]),
            ("portugal",["primeira|liga(?!2)$","segunda|liga[_ ]?2"]),
            ("scotland",["premiership|premier","championship"]),
            ("austria", ["bundesliga(?!2)$","2[_ ]?liga"]),
            ("norway",  ["eliteserien","1(?!.*liga)|first|obos"]),
            ("denmark", ["superliga","1st|first"]),
            ("sweden",  ["allsvenskan","superettan"]),
            ("switzer", ["super[_ ]?league","challenge"]),
            ("turkey",  ["super[_ ]?lig","1[_ ]?lig"]),
            ("poland",  ["ekstraklasa","i[_ ]?liga|1"]),
            ("croat",   ["hnl$","2[_ ]?hnl|druga"]),
            ("cyprus",  ["first|division|protathlima","second|b$"]),
        ]
        keys = []
        for country, tiers in countries:
            keys += _filter_keys(country, tiers)
        # dedup
        out = []
        for k in keys:
            if k not in out:
                out.append(k)
        return out

    # Αν δόθηκε κατευθείαν sport_key (π.χ. soccer_epl), το επιστρέφουμε
    return [bundle_name]

def fetch_odds_for_key(sport_key: str):
    """Φέρνει απλές 1Χ2 αποδόσεις για ένα sport_key και τις απλοποιεί."""
    url = f"{BASE}/sports/{sport_key}/odds"
    params = dict(regions=REGIONS, markets=MARKETS, oddsFormat=ODDS_FMT)
    try:
        data = _get(url, params)
    except requests.HTTPError as e:
        return {"sport_key": sport_key, "error": f"{e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"sport_key": sport_key, "error": str(e)}

    events = []
    for ev in data:
        home, away = ev.get("home_team"), ev.get("away_team")
        # παίρνουμε ό,τι 1Χ2 υπάρχει από τον πρώτο διαθέσιμο bookmaker
        price_1 = price_x = price_2 = None
        for bm in ev.get("bookmakers", []):
            for m in bm.get("markets", []):
                outs = m.get("outcomes", [])
                # Map κατά όνομα
                for o in outs:
                    n = o.get("name","").lower()
                    if n in ("home","1",home.lower() if home else ""):
                        price_1 = o.get("price")
                    elif n in ("draw","x"):
                        price_x = o.get("price")
                    elif n in ("away","2",away.lower() if away else ""):
                        price_2 = o.get("price")
            if price_1 and price_x and price_2:
                break

        events.append({
            "match": f"{home} - {away}",
            "odds": {"1": price_1, "X": price_x, "2": price_2},
            "mode": "simple",
            "sources": ["TheOddsAPI"],
        })
    return {"sport_key": sport_key, "count": len(events), "events": events}

def get_odds_bundle(bundle: str):
    """
    Παίρνει ένα bundle όνομα (england_all, greece_1_2_3, germany_1_2_3, europe_1_2)
    -> επιστρέφει ενιαίο JSON με όλα τα παιχνίδια από τα αντίστοιχα sport_keys.
    """
    keys = resolve_bundle(bundle)
    all_events = []
    for k in keys:
        res = fetch_odds_for_key(k)
        if isinstance(res, dict) and res.get("events"):
            all_events.extend(res["events"])
        time.sleep(0.25)  # μικρό cooldown για το rate limit
    return {"bundle": bundle, "count": len(all_events), "events": all_events}
