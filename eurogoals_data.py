
import os
import sys
import time
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd

# --- Optional JS-capable HTTP client for Flashscore (falls back if not available)
try:
    from requests_html import HTMLSession
    JS_ENABLED = True
except Exception:
    JS_ENABLED = False

EXCEL_PATH = r"C:\EURO_GOALS\EURO_GOALS_v6d.xlsx"
MATCHES_SHEET = "Matches"

# Countries & leagues to fetch (Flashscore league paths).
# We focus on: England (all), Germany 1-3, Greece 1-3, and Europe 1-2 divisions.
# These are representative paths; you may add/remove as needed.
FLASH_LEAGUES: Dict[str, Dict[str, str]] = {
    # England - main + National
    "ENG1": {"country": "England", "name": "Premier League", "path": "/football/england/premier-league/"},
    "ENG2": {"country": "England", "name": "Championship", "path": "/football/england/championship/"},
    "ENG3": {"country": "England", "name": "League One", "path": "/football/england/league-one/"},
    "ENG4": {"country": "England", "name": "League Two", "path": "/football/england/league-two/"},
    "ENG5": {"country": "England", "name": "National League", "path": "/football/england/national-league/"},
    "ENG6N": {"country": "England", "name": "National League North", "path": "/football/england/national-league-north/"},
    "ENG6S": {"country": "England", "name": "National League South", "path": "/football/england/national-league-south/"},
    # Germany 1-3
    "GER1": {"country": "Germany", "name": "Bundesliga", "path": "/football/germany/bundesliga/"},
    "GER2": {"country": "Germany", "name": "2. Bundesliga", "path": "/football/germany/2-bundesliga/"},
    "GER3": {"country": "Germany", "name": "3. Liga", "path": "/football/germany/3-liga/"},
    # Greece 1-3
    "GRE1": {"country": "Greece", "name": "Super League 1", "path": "/football/greece/super-league/"},
    "GRE2": {"country": "Greece", "name": "Super League 2", "path": "/football/greece/super-league-2/"},
    "GRE3": {"country": "Greece", "name": "Gamma Ethniki", "path": "/football/greece/gamma-ethniki/"},
    # Popular Europe 1-2 examples (you can extend freely)
    "ESP1": {"country": "Spain", "name": "LaLiga", "path": "/football/spain/laliga/"},
    "ESP2": {"country": "Spain", "name": "Segunda División", "path": "/football/spain/laliga2/"},
    "ITA1": {"country": "Italy", "name": "Serie A", "path": "/football/italy/serie-a/"},
    "ITA2": {"country": "Italy", "name": "Serie B", "path": "/football/italy/serie-b/"},
    "FRA1": {"country": "France", "name": "Ligue 1", "path": "/football/france/ligue-1/"},
    "FRA2": {"country": "France", "name": "Ligue 2", "path": "/football/france/ligue-2/"},
    "NED1": {"country": "Netherlands", "name": "Eredivisie", "path": "/football/netherlands/eredivisie/"},
    "NED2": {"country": "Netherlands", "name": "Eerste Divisie", "path": "/football/netherlands/eerste-divisie/"},
    "POR1": {"country": "Portugal", "name": "Primeira Liga", "path": "/football/portugal/primeira-liga/"},
    "POR2": {"country": "Portugal", "name": "Liga Portugal 2", "path": "/football/portugal/liga-portugal-2/"},
    "BEL1": {"country": "Belgium", "name": "Pro League", "path": "/football/belgium/pro-league/"},
    "BEL2": {"country": "Belgium", "name": "Challenger Pro League", "path": "/football/belgium/challenger-pro-league/"},
    "TUR1": {"country": "Turkey", "name": "Süper Lig", "path": "/football/turkey/super-lig/"},
    "TUR2": {"country": "Turkey", "name": "1. Lig", "path": "/football/turkey/1-lig/"},
    "SCO1": {"country": "Scotland", "name": "Premiership", "path": "/football/scotland/premiership/"},
    "SCO2": {"country": "Scotland", "name": "Championship", "path": "/football/scotland/championship/"},
    # Add more as needed...
}

BASE = "https://www.flashscore.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- Helpers ---------------------------------------------------------------------------------

def read_existing_matches(excel_path: str) -> pd.DataFrame:
    if not os.path.exists(excel_path):
        # Create empty structure compatible with the template
        cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
                "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
                "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_excel(excel_path, sheet_name=MATCHES_SHEET, engine="openpyxl")
        # Normalize column names just in case
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"[WARN] Could not read existing matches from Excel: {e}")
        cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
                "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
                "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
        return pd.DataFrame(columns=cols)

def save_matches(excel_path: str, df_matches: pd.DataFrame) -> None:
    # Preserve sheet names if they exist by replacing Matches only
    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_matches.to_excel(writer, sheet_name=MATCHES_SHEET, index=False)
        print(f"[OK] Saved {len(df_matches)} total matches to Excel.")
    except Exception as e:
        # If the file does not exist yet, create new
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_matches.to_excel(writer, sheet_name=MATCHES_SHEET, index=False)
        print(f"[OK] Created Excel and saved {len(df_matches)} matches. Detail: {e}")

def polite_sleep(a=1.0, b=2.0):
    time.sleep(random.uniform(a, b))

# --- Flashscore scraping (best-effort) -------------------------------------------------------

def fetch_league_week(code: str, info: Dict, days: int = 7) -> pd.DataFrame:
    """
    Best-effort fetch of a league for the next `days` from Flashscore.
    Requires requests_html for JS rendering. If not present, returns empty and warns.
    """
    if not JS_ENABLED:
        print(f"[WARN] requests_html not installed; skip Flashscore for {code} ({info['name']}).")
        return pd.DataFrame(columns=["Date","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam","HomeGoals","AwayGoals"])

    session = HTMLSession()
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}

    all_rows = []
    today = datetime.now().date()
    for offset in range(0, days+1):
        d = today + timedelta(days=offset)
        # League fixtures page
        url = BASE + info["path"] + "fixtures/"
        try:
            r = session.get(url, headers=headers, timeout=20)
            # Render JS to populate matches
            r.html.render(timeout=30, sleep=2)
        except Exception as e:
            print(f"[WARN] Render failed for {code} {info['name']}: {e}")
            continue

        try:
            # Flashscore typically groups matches by day in blocks with class 'event__day'
            date_blocks = r.html.find("div.event__day")

            # Build human-readable date as shown on the site (approx)
            active_date_str = d.strftime("%d %b %Y").lower()  # e.g., '11 Oct 2025'

            for block in date_blocks:
                header = block.find("div.event__title--name", first=True)
                if header:
                    if active_date_str not in header.text.lower():
                        continue  # skip other dates

                matches = block.find("div.event__match")
                for m in matches:
                    home = m.find("div.event__participant--home", first=True)
                    away = m.find("div.event__participant--away", first=True)
                    hg_el = m.find("div.event__score--home", first=True)
                    ag_el = m.find("div.event__score--away", first=True)

                    home_team = home.text.strip() if home else ""
                    away_team = away.text.strip() if away else ""
                    hg = int(hg_el.text.strip()) if (hg_el and hg_el.text.strip().isdigit()) else None
                    ag = int(ag_el.text.strip()) if (ag_el and ag_el.text.strip().isdigit()) else None

                    if not home_team or not away_team:
                        continue

                    all_rows.append({
                        "Date": d.strftime("%Y-%m-%d"),
                        "Country": info["country"],
                        "LeagueCode": code,
                        "LeagueName": info["name"],
                        "HomeTeam": home_team,
                        "AwayTeam": away_team,
                        "HomeGoals": hg,
                        "AwayGoals": ag,
                    })
            polite_sleep(1.0, 2.0)
        except Exception as e:
            print(f"[WARN] Parse failed for {code} {info['name']} on {d}: {e}")
            continue

    return pd.DataFrame(all_rows)

def dedupe_merge(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if existing is None or existing.empty:
        base = new.copy()
    else:
        # Uniqueness key
        key_cols = ["Date","LeagueCode","HomeTeam","AwayTeam"]
        for col in key_cols:
            if col not in existing.columns:
                existing[col] = ""
            if col not in new.columns:
                new[col] = ""

        base = pd.concat([existing, new], ignore_index=True)
        base.sort_values(by=["Date","LeagueCode"], inplace=True)
        base.drop_duplicates(subset=key_cols, keep="last", inplace=True)

    # Normalize numeric
    for gcol in ["HomeGoals","AwayGoals"]:
        if gcol in base.columns:
            base[gcol] = pd.to_numeric(base[gcol], errors="coerce")

    # Derive flags
    def calc_flags(row):
        hg = row.get("HomeGoals", None)
        ag = row.get("AwayGoals", None)
        if pd.isna(hg) or pd.isna(ag):
            return pd.Series({"BTTS": None, "Over1_5": None, "Over2_5": None, "Over3_5": None})
        total = int(hg) + int(ag)
        return pd.Series({
            "BTTS": 1 if (hg > 0 and ag > 0) else 0,
            "Over1_5": 1 if total >= 2 else 0,
            "Over2_5": 1 if total >= 3 else 0,
            "Over3_5": 1 if total >= 4 else 0,
        })

    flags = base.apply(calc_flags, axis=1)
    for col in ["BTTS","Over1_5","Over2_5","Over3_5"]:
        base[col] = flags[col]

    # Ensure odds columns exist
    for col in ["Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]:
        if col not in base.columns:
            base[col] = None

    # Season guess
    if "Season" not in base.columns:
        base["Season"] = None
    def season_of(dstr):
        try:
            d = pd.to_datetime(dstr).date()
            yr = d.year
            if d.month >= 7:
                return f"{yr}-{str(yr+1)[-2:]}"
            else:
                return f"{yr-1}-{str(yr)[-2:]}"
        except Exception:
            return None
    base["Season"] = base["Season"].fillna(base["Date"].apply(season_of))

    # Order columns
    required_cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
                     "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
                     "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
    for col in required_cols:
        if col not in base.columns:
            base[col] = None
    base = base[required_cols]
    return base

def main():
    print("[INFO] EURO_GOALS v6d_auto — Flashscore weekly updater")
    print(f"[INFO] Excel path: {EXCEL_PATH}")
    if not JS_ENABLED:
        print("[WARN] 'requests_html' not installed. Install first:  pip install requests-html  ")
        print("[WARN] Skipping Flashscore fetching. Exiting.")
        sys.exit(1)

    existing = read_existing_matches(EXCEL_PATH)

    collected = []
    for code, info in FLASH_LEAGUES.items():
        print(f"[FETCH] {code} — {info['country']} / {info['name']}")
        df = fetch_league_week(code, info, days=7)
        print(f"[OK] {code}: fetched {len(df)} rows.")
        if not df.empty:
            collected.append(df)
    if not collected:
        print("[WARN] No data collected from Flashscore.")
        sys.exit(0)

    new_all = pd.concat(collected, ignore_index=True)
    merged = dedupe_merge(existing, new_all)
    save_matches(EXCEL_PATH, merged)
    print("[DONE] Update complete.")

if __name__ == "__main__":
    main()
