# ============================================================
# modules/api_reader.py
# Manual League Updater – fixtures/βασικά ανά λίγκα (API-Football)
# ============================================================

from datetime import datetime, timedelta
import requests

SUPPORTED_LEAGUES = {
    # England
    "ENG1": {"id": 39,  "name": "Premier League", "country": "England", "tier": 1},
    "ENG2": {"id": 40,  "name": "Championship",   "country": "England", "tier": 2},
    "ENG3": {"id": 41,  "name": "League One",     "country": "England", "tier": 3},
    "ENG4": {"id": 42,  "name": "League Two",     "country": "England", "tier": 4},
    # Germany
    "GER1": {"id": 78,  "name": "Bundesliga",     "country": "Germany", "tier": 1},
    "GER2": {"id": 79,  "name": "2. Bundesliga",  "country": "Germany", "tier": 2},
    "GER3": {"id": 80,  "name": "3. Liga",        "country": "Germany", "tier": 3},
    # Greece
    "GRE1": {"id": 197, "name": "Super League 1", "country": "Greece", "tier": 1},
    "GRE2": {"id": 566, "name": "Super League 2", "country": "Greece", "tier": 2},
    # Spain
    "ESP1": {"id": 140, "name": "LaLiga",         "country": "Spain", "tier": 1},
    "ESP2": {"id": 141, "name": "LaLiga 2",       "country": "Spain", "tier": 2},
    # Italy
    "ITA1": {"id": 135, "name": "Serie A",        "country": "Italy", "tier": 1},
    "ITA2": {"id": 136, "name": "Serie B",        "country": "Italy", "tier": 2},
    # France
    "FRA1": {"id": 61,  "name": "Ligue 1",        "country": "France", "tier": 1},
    "FRA2": {"id": 62,  "name": "Ligue 2",        "country": "France", "tier": 2},
    # Netherlands
    "NED1": {"id": 88,  "name": "Eredivisie",     "country": "Netherlands", "tier": 1},
    "NED2": {"id": 89,  "name": "Eerste Divisie", "country": "Netherlands", "tier": 2},
    # Portugal
    "POR1": {"id": 94,  "name": "Primeira Liga",  "country": "Portugal", "tier": 1},
    "POR2": {"id": 95,  "name": "Liga Portugal 2","country": "Portugal", "tier": 2},
    # Belgium
    "BEL1": {"id": 144, "name": "Jupiler Pro League", "country": "Belgium", "tier": 1},
    "BEL2": {"id": 145, "name": "Challenger Pro League", "country": "Belgium", "tier": 2},
    # Switzerland
    "SUI1": {"id": 207, "name": "Super League",   "country": "Switzerland", "tier": 1},
    "SUI2": {"id": 208, "name": "Challenge League", "country": "Switzerland", "tier": 2},
    # Austria
    "AUT1": {"id": 218, "name": "Bundesliga",     "country": "Austria", "tier": 1},
    "AUT2": {"id": 219, "name": "2. Liga",        "country": "Austria", "tier": 2},
    # Denmark
    "DEN1": {"id": 13,  "name": "Superliga",      "country": "Denmark", "tier": 1},
    "DEN2": {"id": 14,  "name": "1st Division",   "country": "Denmark", "tier": 2},
    # Norway
    "NOR1": {"id": 103, "name": "Eliteserien",    "country": "Norway", "tier": 1},
    "NOR2": {"id": 104, "name": "OBOS-ligaen",    "country": "Norway", "tier": 2},
    # Sweden
    "SWE1": {"id": 119, "name": "Allsvenskan",    "country": "Sweden", "tier": 1},
    "SWE2": {"id": 120, "name": "Superettan",     "country": "Sweden", "tier": 2},
    # Poland
    "POL1": {"id": 106, "name": "Ekstraklasa",    "country": "Poland", "tier": 1},
    "POL2": {"id": 107, "name": "I Liga",         "country": "Poland", "tier": 2},
    # Romania
    "ROM1": {"id": 283, "name": "Liga I",         "country": "Romania", "tier": 1},
    "ROM2": {"id": 284, "name": "Liga II",        "country": "Romania", "tier": 2},
    # Serbia
    "SRB1": {"id": 285, "name": "SuperLiga",      "country": "Serbia", "tier": 1},
    "SRB2": {"id": 286, "name": "Prva Liga",      "country": "Serbia", "tier": 2},
    # Turkey
    "TUR1": {"id": 203, "name": "Super Lig",      "country": "Turkey", "tier": 1},
    "TUR2": {"id": 204, "name": "1. Lig",         "country": "Turkey", "tier": 2},
}

def _safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _iso_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _apifootball_fixtures(league_id: int, apikey: str):
    if not apikey:
        return {"count": 0, "fixtures": []}

    headers = {"x-apisports-key": apikey}
    season = datetime.now().year
    to_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    try:
        r = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=headers,
            params={"league": league_id, "season": season, "to": to_date, "status": "NS"},
            timeout=12
        )
        if r.status_code != 200:
            print(f"[API_READER] ⚠️ API-Football fixtures {league_id} HTTP {r.status_code}")
            return {"count": 0, "fixtures": []}
        fixtures = []
        for it in r.json().get("response") or []:
            fixtures.append({
                "fixture_id": _safe_get(it, "fixture", "id"),
                "utc_date": _safe_get(it, "fixture", "date"),
                "home": _safe_get(it, "teams", "home", "name"),
                "away": _safe_get(it, "teams", "away", "name"),
                "league_id": league_id,
            })
        return {"count": len(fixtures), "fixtures": fixtures}
    except Exception as e:
        print("[API_READER] ❌ API-Football fixtures error:", e)
        return {"count": 0, "fixtures": []}

def _footballdata_meta(league_code: str, apikey: str):
    return {"ok": bool(apikey), "note": "Football-Data enrichment placeholder"}

def _sportmonks_meta(league_code: str, apikey: str):
    return {"ok": bool(apikey), "note": "SportMonks enrichment placeholder"}

def _thesportsdb_meta(league_code: str, apikey: str):
    return {"ok": bool(apikey), "note": "TheSportsDB enrichment placeholder"}

def update_single_league(
    league_code: str,
    meta: dict,
    apifootball_key: str,
    footballdata_key: str = "",
    sportmonks_key: str = "",
    thesportsdb_key: str = ""
):
    print(f"[API_READER] 🔎 Updating {league_code} – {meta['name']} ({meta['country']})")
    league_id = meta["id"]

    fixtures_info = _apifootball_fixtures(league_id, apifootball_key)
    fd_info = _footballdata_meta(league_code, footballdata_key)
    sm_info = _sportmonks_meta(league_code, sportmonks_key)
    ts_info = _thesportsdb_meta(league_code, thesportsdb_key)

    summary = {
        "league_code": league_code,
        "league_name": meta["name"],
        "updated_at": _iso_now(),
        "fixtures_count": fixtures_info["count"],
        "sources": {
            "api_football": fixtures_info["count"] > 0,
            "football_data": fd_info.get("ok", False),
            "sportmonks": sm_info.get("ok", False),
            "thesportsdb": ts_info.get("ok", False),
        }
    }
    print(f"[API_READER] ✅ {league_code} updated – fixtures: {fixtures_info['count']}")
    return summary
