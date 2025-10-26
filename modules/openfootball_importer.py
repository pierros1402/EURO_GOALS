# ==============================================
# OPENFOOTBALL IMPORTER v8.3 (3-level fallback)
# ==============================================
import os
import requests
import json

DATA_DIR = os.path.join("data", "openfootball_cache")
os.makedirs(DATA_DIR, exist_ok=True)

LEAGUES = {
    "england": "Premier League",
    "germany": "Bundesliga",
    "greece": "Super League",
    "italy": "Serie A",
    "spain": "La Liga",
    "france": "Ligue 1",
    "netherlands": "Eredivisie",
    "portugal": "Primeira Liga",
    "turkey": "Super Lig",
    "belgium": "Jupiler Pro League",
    "austria": "Bundesliga",
    "switzerland": "Super League",
    "poland": "Ekstraklasa",
    "denmark": "Superliga",
    "scotland": "Premiership"
}

SEASONS = ["2024-25", "2023-24", "2022-23"]

def import_league(league, season):
    """Προσπάθεια λήψης δεδομένων για συγκεκριμένη σεζόν"""
    base_url = f"https://raw.githubusercontent.com/openfootball/{league}/master/{season}/en.1.json"
    print(f"[OPENFOOTBALL] 🌍 {league} {season} ...", end=" ")

    try:
        res = requests.get(base_url, timeout=10)
        if res.status_code == 404:
            print("(404 not found)")
            return None
        elif res.status_code != 200:
            print(f"(error {res.status_code})")
            return None

        data = res.json()
        filepath = os.path.join(DATA_DIR, f"{league}_{season}.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(data.get('matches', []))} matches")
        return len(data.get("matches", []))

    except Exception as e:
        print(f"(error: {e})")
        return None


def main():
    print("[OPENFOOTBALL] 🚀 Starting import...")
    total = 0

    for league in LEAGUES.keys():
        matches = None
        for season in SEASONS:
            matches = import_league(league, season)
            if matches:
                break  # αν βρει, σταματά
        if matches:
            total += matches

    print(f"[OPENFOOTBALL] ✅ Imported {total} matches total.")


if __name__ == "__main__":
    main()
