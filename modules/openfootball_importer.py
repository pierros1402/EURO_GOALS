# ==============================================
# OPENFOOTBALL IMPORTER v8.4 (auto-season finder)
# ==============================================
import os
import requests
import json

DATA_DIR = os.path.join("data", "openfootball_cache")
os.makedirs(DATA_DIR, exist_ok=True)

GITHUB_API_BASE = "https://api.github.com/repos/openfootball"
RAW_BASE = "https://raw.githubusercontent.com/openfootball"

LEAGUES = {
    "england": "Premier League",
    "germany": "Bundesliga",
    "italy": "Serie A",
    "spain": "La Liga",
    "france": "Ligue 1",
    "greece": "Super League",
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

def get_latest_season_folder(league):
    """Αναζητά τον πιο πρόσφατο φάκελο season στο GitHub repo του OpenFootball"""
    url = f"{GITHUB_API_BASE}/{league}/contents"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"⚠️  {league}: cannot fetch repo contents ({r.status_code})")
            return None

        folders = [f["name"] for f in r.json() if f["type"] == "dir" and "-" in f["name"]]
        if not folders:
            print(f"⚠️  {league}: no season folders found")
            return None

        # Ταξινόμηση π.χ. ["2019-20","2020-21","2021-22"] → τελευταίο
        folders.sort(reverse=True)
        return folders[0]

    except Exception as e:
        print(f"❌ {league}: error checking seasons -> {e}")
        return None


def import_league(league):
    """Κατεβάζει δεδομένα για την πιο πρόσφατη σεζόν"""
    latest = get_latest_season_folder(league)
    if not latest:
        print(f"❌ {league}: No season folder found")
        return 0

    url = f"{RAW_BASE}/{league}/master/{latest}/en.1.json"
    print(f"[OPENFOOTBALL] ⚽ {league} ({latest}) -> {url}")

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"⚠️  {league}: {r.status_code} not found")
            return 0

        data = r.json()
        matches = data.get("matches", [])
        filepath = os.path.join(DATA_DIR, f"{league}_{latest}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ {league}: Imported {len(matches)} matches from {latest}")
        return len(matches)

    except Exception as e:
        print(f"❌ {league}: Error importing -> {e}")
        return 0


def main():
    print("[OPENFOOTBALL] 🚀 Auto-importing latest data...")
    total = 0
    for league in LEAGUES.keys():
        total += import_league(league)
    print(f"\n[OPENFOOTBALL] ✅ Total matches imported: {total}")


if __name__ == "__main__":
    main()
