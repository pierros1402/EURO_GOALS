# EURO_GOALS v6e — Dual Source Updater (Flashscore + Sofascore)
# Author: ChatGPT for Pierr
# See comments inside for usage instructions. (Full content below)

import os, sys, time, json, random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

LOG_PATH = "log_dualsource.txt"
EXCEL_PATH = r"C:\Users\pierr\Desktop\EURO_GOALS\EURO_GOALS_v6d.xlsx"
SHEET = "Matches"

FS_LEAGUES = {
    "ENG1":{"country":"England","name":"Premier League","path":"/football/england/premier-league/"},
    "ENG2":{"country":"England","name":"Championship","path":"/football/england/championship/"},
    "ENG3":{"country":"England","name":"League One","path":"/football/england/league-one/"},
    "ENG4":{"country":"England","name":"League Two","path":"/football/england/league-two/"},
    "ENG5":{"country":"England","name":"National League","path":"/football/england/national-league/"},
    "ENG6N":{"country":"England","name":"National League North","path":"/football/england/national-league-north/"},
    "ENG6S":{"country":"England","name":"National League South","path":"/football/england/national-league-south/"},
    "GER1":{"country":"Germany","name":"Bundesliga","path":"/football/germany/bundesliga/"},
    "GER2":{"country":"Germany","name":"2. Bundesliga","path":"/football/germany/2-bundesliga/"},
    "GER3":{"country":"Germany","name":"3. Liga","path":"/football/germany/3-liga/"},
    "GRE1":{"country":"Greece","name":"Super League 1","path":"/football/greece/super-league/"},
    "GRE2":{"country":"Greece","name":"Super League 2","path":"/football/greece/super-league-2/"},
    "GRE3":{"country":"Greece","name":"Gamma Ethniki","path":"/football/greece/gamma-ethniki/"},
    "ESP1":{"country":"Spain","name":"LaLiga","path":"/football/spain/laliga/"},
    "ESP2":{"country":"Spain","name":"Segunda División","path":"/football/spain/laliga2/"},
    "ITA1":{"country":"Italy","name":"Serie A","path":"/football/italy/serie-a/"},
    "ITA2":{"country":"Italy","name":"Serie B","path":"/football/italy/serie-b/"},
    "FRA1":{"country":"France","name":"Ligue 1","path":"/football/france/ligue-1/"},
    "FRA2":{"country":"France","name":"Ligue 2","path":"/football/france/ligue-2/"},
    "NED1":{"country":"Netherlands","name":"Eredivisie","path":"/football/netherlands/eredivisie/"},
    "NED2":{"country":"Netherlands","name":"Eerste Divisie","path":"/football/netherlands/eerste-divisie/"},
    "POR1":{"country":"Portugal","name":"Primeira Liga","path":"/football/portugal/primeira-liga/"},
    "POR2":{"country":"Portugal","name":"Liga Portugal 2","path":"/football/portugal/liga-portugal-2/"},
    "BEL1":{"country":"Belgium","name":"Pro League","path":"/football/belgium/pro-league/"},
    "BEL2":{"country":"Belgium","name":"Challenger Pro League","path":"/football/belgium/challenger-pro-league/"},
    "TUR1":{"country":"Turkey","name":"Süper Lig","path":"/football/turkey/super-lig/"},
    "TUR2":{"country":"Turkey","name":"1. Lig","path":"/football/turkey/1-lig/"},
    "SCO1":{"country":"Scotland","name":"Premiership","path":"/football/scotland/premiership/"},
    "SCO2":{"country":"Scotland","name":"Championship","path":"/football/scotland/championship/"},
}

SS_TOURNAMENTS = {
    "ENG1":{"country":"England","name":"Premier League","id":17},
    "ENG2":{"country":"England","name":"Championship","id":34},
    "ENG3":{"country":"England","name":"League One","id":39},
    "ENG4":{"country":"England","name":"League Two","id":40},
    "ENG5":{"country":"England","name":"National League","id":50},
    "GER1":{"country":"Germany","name":"Bundesliga","id":35},
    "GER2":{"country":"Germany","name":"2. Bundesliga","id":36},
    "GER3":{"country":"Germany","name":"3. Liga","id":848},
    "GRE1":{"country":"Greece","name":"Super League 1","id":197},
    "GRE2":{"country":"Greece","name":"Super League 2","id":619},
    "ESP1":{"country":"Spain","name":"LaLiga","id":8},
    "ESP2":{"country":"Spain","name":"LaLiga2","id":7},
    "ITA1":{"country":"Italy","name":"Serie A","id":23},
    "ITA2":{"country":"Italy","name":"Serie B","id":24},
    "FRA1":{"country":"France","name":"Ligue 1","id":34},
    "FRA2":{"country":"France","name":"Ligue 2","id":301},
    "NED1":{"country":"Netherlands","name":"Eredivisie","id":37},
    "NED2":{"country":"Netherlands","name":"Eerste Divisie","id":561},
    "POR1":{"country":"Portugal","name":"Primeira Liga","id":238},
    "POR2":{"country":"Portugal","name":"Liga Portugal 2","id":239},
    "BEL1":{"country":"Belgium","name":"Pro League","id":66},
    "BEL2":{"country":"Belgium","name":"Challenger Pro League","id":67},
}

BASE_FS = "https://www.flashscore.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    try:
        with open("log_dualsource.txt","a",encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

def polite_sleep(a=0.8,b=1.8):
    time.sleep(random.uniform(a,b))

def read_existing() -> pd.DataFrame:
    if not os.path.exists(EXCEL_PATH):
        cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
                "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
                "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
        return pd.DataFrame(columns=cols)
    try:
        return pd.read_excel(EXCEL_PATH, sheet_name=SHEET, engine="openpyxl")
    except Exception as e:
        log(f"[WARN] Could not read Excel: {e}")
        cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
                "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
                "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
        return pd.DataFrame(columns=cols)

def save_excel(df: pd.DataFrame):
    try:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
            df.to_excel(w, sheet_name=SHEET, index=False)
        log(f"[OK] Saved {len(df)} rows to Excel.")
    except Exception as e:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as w:
            df.to_excel(w, sheet_name=SHEET, index=False)
        log(f"[OK] Created Excel and saved {len(df)} rows. ({e})")

def fetch_sofascore_week(code: str, info: dict, days: int = 7) -> pd.DataFrame:
    import requests
    rows = []
    today = datetime.now().date()
    for offset in range(0,days+1):
        d = today + timedelta(days=offset)
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{info['id']}/events/week/{d.isoformat()}"
        try:
            r = requests.get(url, headers={"User-Agent":UA}, timeout=20)
            if r.status_code != 200: continue
            data = r.json()
            for ev in data.get("events",[]) or []:
                home = ev.get("homeTeam",{}).get("name","")
                away = ev.get("awayTeam",{}).get("name","")
                hg = ev.get("homeScore",{}).get("current")
                ag = ev.get("awayScore",{}).get("current")
                rows.append({
                    "Date": datetime.fromtimestamp(ev.get("startTimestamp",0)).strftime("%Y-%m-%d"),
                    "Country": info["country"],
                    "LeagueCode": code,
                    "LeagueName": info["name"],
                    "HomeTeam": home, "AwayTeam": away,
                    "HomeGoals": hg, "AwayGoals": ag,
                    "source": "SS"
                })
        except Exception as e:
            log(f"[WARN] SS fetch failed for {code}: {e}")
        polite_sleep()
    return pd.DataFrame(rows)

def fetch_flashscore_week(code: str, info: dict, days: int = 7) -> pd.DataFrame:
    # Import inside function to avoid false negatives
    try:
        import nest_asyncio
        nest_asyncio.apply()
        from requests_html import HTMLSession
    except Exception as e:
        log(f"[WARN] requests_html import failed: {e}")
        return pd.DataFrame(columns=[])

    session = HTMLSession()
    headers = {"User-Agent":UA,"Accept-Language":"en-US,en;q=0.9"}

    rows = []
    today = datetime.now().date()
    url = BASE_FS + info["path"] + "fixtures/"
    try:
        r = session.get(url, headers=headers, timeout=25)
        r.html.render(timeout=45, sleep=2)  # Headless Chromium
    except Exception as e:
        log(f"[WARN] FS render failed for {code}: {e}")
        return pd.DataFrame(rows)

    try:
        blocks = r.html.find("div.event__day")
        for offset in range(0,days+1):
            d = today + timedelta(days=offset)
            label = d.strftime("%d %b %Y").lower()
            for b in blocks:
                head = b.find("div.event__title--name", first=True)
                if head and (label not in head.text.lower()): continue
                matches = b.find("div.event__match")
                for m in matches:
                    home = m.find("div.event__participant--home", first=True)
                    away = m.find("div.event__participant--away", first=True)
                    hg_el = m.find("div.event__score--home", first=True)
                    ag_el = m.find("div.event__score--away", first=True)
                    home_team = home.text.strip() if home else ""
                    away_team = away.text.strip() if away else ""
                    hg = int(hg_el.text.strip()) if (hg_el and hg_el.text.strip().isdigit()) else None
                    ag = int(ag_el.text.strip()) if (ag_el and ag_el.text.strip().isdigit()) else None
                    if not home_team or not away_team: continue
                    rows.append({
                        "Date": d.strftime("%Y-%m-%d"),
                        "Country": info["country"],
                        "LeagueCode": code,
                        "LeagueName": info["name"],
                        "HomeTeam": home_team, "AwayTeam": away_team,
                        "HomeGoals": hg, "AwayGoals": ag,
                        "source": "FS"
                    })
        polite_sleep()
    except Exception as e:
        log(f"[WARN] FS parse failed for {code}: {e}")
    return pd.DataFrame(rows)

def unify(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
            "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
            "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"
        ])
    for g in ["HomeGoals","AwayGoals"]:
        df[g] = pd.to_numeric(df.get(g), errors="coerce")
    key = ["Date","LeagueCode","HomeTeam","AwayTeam"]
    df = df.sort_values(key+["source"]).drop_duplicates(subset=key, keep="last")
    def calc(row):
        hg, ag = row["HomeGoals"], row["AwayGoals"]
        if pd.isna(hg) or pd.isna(ag):
            return pd.Series({"BTTS":None,"Over1_5":None,"Over2_5":None,"Over3_5":None})
        total = int(hg)+int(ag)
        return pd.Series({
            "BTTS":1 if (hg>0 and ag>0) else 0,
            "Over1_5":1 if total>=2 else 0,
            "Over2_5":1 if total>=3 else 0,
            "Over3_5":1 if total>=4 else 0,
        })
    flags = df.apply(calc, axis=1)
    for c in ["BTTS","Over1_5","Over2_5","Over3_5"]:
        df[c] = flags[c]
    def season_of(dstr):
        try:
            d = pd.to_datetime(dstr).date()
            yr = d.year
            return f"{yr}-{str(yr+1)[-2:]}" if d.month>=7 else f"{yr-1}-{str(yr)[-2:]}"
        except Exception:
            return None
    df["Season"] = df["Date"].apply(season_of)
    for c in ["Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]:
        if c not in df.columns: df[c] = None
    cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
            "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
            "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
    return df[cols]

def merge_into(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if existing is None or existing.empty:
        return new.copy()
    key = ["Date","LeagueCode","HomeTeam","AwayTeam"]
    both = pd.concat([existing, new], ignore_index=True)
    both.drop_duplicates(subset=key, keep="last", inplace=True)
    return both

def main():
    print("[INFO] EURO_GOALS v6e_dualsource — start (FS + SS, 7 days)")
    existing = read_existing()
    frames = []

    # Flashscore sweep
    for code, info in FS_LEAGUES.items():
        print(f"[FETCH/FS] {code} — {info['country']} / {info['name']}")
        fs = fetch_flashscore_week(code, info, days=7)
        print(f"[OK/FS] {code}: {len(fs)} rows")
        if not fs.empty: frames.append(fs)

    # Sofascore sweep (subset of leagues)
    for code, meta in SS_TOURNAMENTS.items():
        print(f"[FETCH/SS] {code} — {meta['country']} / {meta['name']}")
        ss = fetch_sofascore_week(code, meta, days=7)
        print(f"[OK/SS] {code}: {len(ss)} rows")
        if not ss.empty: frames.append(ss)

    if not frames:
        print("[WARN] No data collected from either source.")
        sys.exit(0)

    unified = unify(pd.concat(frames, ignore_index=True))
    merged = merge_into(existing, unified)
    save_excel(merged)
    print("[DONE] v6e_dualsource update complete.")

if __name__ == "__main__":
    main()
