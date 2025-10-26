# ==============================================
# OPENFOOTBALL IMPORTER v8.2 (GitHub Version)
# ==============================================
# Εισαγωγή δεδομένων από τα GitHub repos του OpenFootball
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

def import_league(league, season):
    """Λήψη δεδομένων από το σωστό repo του GitHub"""
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
    print("[OPENFOOTBALL] 🚀 Starting import for 2024-25...")
    total = 0
    for league in LEAGUES.keys():
        # 1️⃣ Προσπάθησε 2024-25
        matches = import_league(league, "2024-25")

        # 2️⃣ Αν δεν βρεθεί, προσπάθησε 2023-24
        if matches is None:
            matches = import_league(league, "2023-24")

        if matches:
            total += matches

    print(f"[OPENFOOTBALL] ✅ Imported {total} matches total.")


if __name__ == "__main__":
    main()
