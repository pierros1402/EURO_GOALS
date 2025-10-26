# =======================================================
# OPENFOOTBALL IMPORTER v1.0
# Universal Historical Data Loader for EURO_GOALS
# =======================================================

import os
import json
import requests
import sqlite3
from datetime import datetime

# ----------------------------------------------
# GitHub base URL for OpenFootball datasets
# ----------------------------------------------
BASE_URL = "https://raw.githubusercontent.com/openfootball"

# ----------------------------------------------
# Target database
# ----------------------------------------------
DB_PATH = os.getenv("DATABASE_URL", "matches.db")

# ----------------------------------------------
# Countries supported by EURO_GOALS
# ----------------------------------------------
COUNTRIES = [
    "england",
    "germany",
    "greece",
    "italy",
    "spain",
    "france",
    "netherlands",
    "portugal",
    "turkey",
    "belgium",
    "austria",
    "switzerland",
    "poland",
    "denmark",
    "scotland",
]

# ----------------------------------------------
# Local cache directory
# ----------------------------------------------
CACHE_DIR = os.path.join("data", "openfootball_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


# =======================================================
# Utility: download JSON file from OpenFootball GitHub
# =======================================================
def download_league(country, season):
    """
    Downloads league JSON for given country & season.
    Example: england/2024-25/eng.1.json
    """
    season_path = f"{country}/{season}/{country[:2]}.1.json"
    url = f"{BASE_URL}/{country}-football-data/master/{season_path}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            file_path = os.path.join(CACHE_DIR, f"{country}_{season}.json")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[OPENFOOTBALL] ✅ Downloaded {country} {season}")
            return file_path
        else:
            print(f"[OPENFOOTBALL] ⚠️ {country} {season} not found ({response.status_code})")
    except Exception as e:
        print(f"[OPENFOOTBALL] ❌ Error downloading {country} {season}: {e}")
    return None


# =======================================================
# Parse & store into SQLite
# =======================================================
def parse_and_store(file_path):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS historical_matches (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT,
                   country TEXT,
                   league TEXT,
                   home TEXT,
                   away TEXT,
                   score TEXT
               )"""
        )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        country = os.path.basename(file_path).split("_")[0]
        season = os.path.basename(file_path).split("_")[1].replace(".json", "")

        matches = data.get("matches", [])
        for m in matches:
            date = m.get("date")
            home = m.get("team1")
            away = m.get("team2")
            score = m.get("score", "")
            league = data.get("name", season)

            cur.execute(
                "INSERT INTO historical_matches (date, country, league, home, away, score) VALUES (?, ?, ?, ?, ?, ?)",
                (date, country, league, home, away, score),
            )

        conn.commit()
        conn.close()
        print(f"[OPENFOOTBALL] 💾 Stored {len(matches)} matches from {country} {season}")
        return len(matches)

    except Exception as e:
        print(f"[OPENFOOTBALL] ❌ Error storing {file_path}: {e}")
        return 0


# =======================================================
# Import all countries (latest season)
# =======================================================
def import_all_countries(season="2024-25"):
    total = 0
    print(f"[OPENFOOTBALL] 🌍 Starting import for {season}...")
    for country in COUNTRIES:
        file_path = download_league(country, season)
        if file_path:
            total += parse_and_store(file_path)
    print(f"[OPENFOOTBALL] ✅ Imported {total} matches total.")
    return total


# =======================================================
# Main execution (for manual run)
# =======================================================
if __name__ == "__main__":
    import_all_countries("2024-25")
