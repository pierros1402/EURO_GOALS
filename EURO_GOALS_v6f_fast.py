# EURO_GOALS_v6f_fast — Dual Source (Flashscore + Sofascore), fast & quiet
# (See in-file comments for usage and features.)
import os, sys, time, json, random, argparse
from datetime import datetime, timedelta, date
from typing import Dict, List
import pandas as pd
import json
import os

LAST_SELECTION_FILE = "last_selection.json"

def save_last_selection(country, league):
    """Αποθηκεύει την τελευταία επιλογή σε αρχείο JSON"""
    data = {"country": country, "league": league}
    with open(LAST_SELECTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_last_selection():
    """Φορτώνει την τελευταία επιλογή αν υπάρχει"""
    if os.path.exists(LAST_SELECTION_FILE):
        try:
            with open(LAST_SELECTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("country"), data.get("league")
        except Exception:
            return None, None
    return None, None

from europelist import EURO_LEAGUES, list_countries, get_country
BASE_FS = "https://www.flashscore.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_LOG = os.path.join(SCRIPT_DIR, "EURO_GOALS_log.txt")
RUN_DATE = datetime.now().strftime("%Y-%m-%d")
EXCEL_PATH = os.path.join(SCRIPT_DIR, f"EURO_GOALS_{RUN_DATE}.xlsx")

FS_LEAGUES: Dict[str, Dict[str,str]] = {
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
    "SUI1":{"country":"Switzerland","name":"Super League","path":"/football/switzerland/super-league/"},
    "SUI2":{"country":"Switzerland","name":"Challenge League","path":"/football/switzerland/challenge-league/"},
    "AUT1":{"country":"Austria","name":"Bundesliga","path":"/football/austria/bundesliga/"},
    "AUT2":{"country":"Austria","name":"2. Liga","path":"/football/austria/2-liga/"},
    "DEN1":{"country":"Denmark","name":"Superliga","path":"/football/denmark/superliga/"},
    "DEN2":{"country":"Denmark","name":"1st Division","path":"/football/denmark/1st-division/"},
    "NOR1":{"country":"Norway","name":"Eliteserien","path":"/football/norway/eliteserien/"},
    "NOR2":{"country":"Norway","name":"OBOS-ligaen","path":"/football/norway/obos-ligaen/"},
    "SWE1":{"country":"Sweden","name":"Allsvenskan","path":"/football/sweden/allsvenskan/"},
    "SWE2":{"country":"Sweden","name":"Superettan","path":"/football/sweden/superettan/"},
    "POL1":{"country":"Poland","name":"Ekstraklasa","path":"/football/poland/ekstraklasa/"},
    "POL2":{"country":"Poland","name":"I liga","path":"/football/poland/i-liga/"},
    "CZE1":{"country":"Czechia","name":"Fortuna Liga","path":"/football/czech-republic/1-liga/"},
    "CZE2":{"country":"Czechia","name":"FNL","path":"/football/czech-republic/fnl/"},
    "ROU1":{"country":"Romania","name":"Liga I","path":"/football/romania/liga-1/"},
    "ROU2":{"country":"Romania","name":"Liga II","path":"/football/romania/liga-2/"},
    "SRB1":{"country":"Serbia","name":"SuperLiga","path":"/football/serbia/super-liga/"},
    "SRB2":{"country":"Serbia","name":"Prva Liga","path":"/football/serbia/prva-liga/"},
    "HUN1":{"country":"Hungary","name":"NB I","path":"/football/hungary/nb-i/"},
    "HUN2":{"country":"Hungary","name":"NB II","path":"/football/hungary/nb-ii/"},
    "BUL1":{"country":"Bulgaria","name":"First League","path":"/football/bulgaria/first-league/"},
    "BUL2":{"country":"Bulgaria","name":"Second League","path":"/football/bulgaria/second-league/"},
    "SVN1":{"country":"Slovenia","name":"PrvaLiga","path":"/football/slovenia/prva-liga/"},
    "SVN2":{"country":"Slovenia","name":"2. SNL","path":"/football/slovenia/2-snl/"},
    "SVK1":{"country":"Slovakia","name":"Fortuna Liga","path":"/football/slovakia/fortuna-liga/"},
    "SVK2":{"country":"Slovakia","name":"2. Liga","path":"/football/slovakia/2-liga/"},
    "IRL1":{"country":"Ireland","name":"Premier Division","path":"/football/ireland/premier-division/"},
    "IRL2":{"country":"Ireland","name":"First Division","path":"/football/ireland/first-division/"},
    "FIN1":{"country":"Finland","name":"Veikkausliiga","path":"/football/finland/veikkausliiga/"},
    "FIN2":{"country":"Finland","name":"Ykkönen","path":"/football/finland/ykkonen/"},
    "CYP1":{"country":"Cyprus","name":"First Division","path":"/football/cyprus/first-division/"},
    "CYP2":{"country":"Cyprus","name":"Second Division","path":"/football/cyprus/second-division/"},
}

SS_TOURNAMENTS: Dict[str, Dict[str, int]] = {
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
    "TUR1":{"country":"Turkey","name":"Super Lig","id":34},
}

def log(line: str, logfile: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = f"[{ts}] {line}"
    try:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(out + "\n")
    except Exception:
        pass

def polite_sleep(a=0.6, b=1.4):
    time.sleep(random.uniform(a, b))

def season_start_from_august(today: date) -> date:
    return date(today.year, 8, 1) if today.month >= 8 else date(today.year-1, 8, 1)

def fetch_sofascore_range(code: str, info: Dict, start_d: date, end_d: date, logfile: str) -> pd.DataFrame:
    import requests
    rows = []
    cur = start_d
    while cur <= end_d:
        try:
            url = f"https://api.sofascore.com/api/v1/unique-tournament/{info['id']}/events/week/{cur.isoformat()}"
            r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
            if r.status_code != 200:
                log(f"[SS][{code}] HTTP {r.status_code} @ {url}", logfile)
                cur += timedelta(days=7); continue
            data = r.json()
            for ev in data.get("events", []) or []:
                rows.append({
                    "Date": datetime.fromtimestamp(ev.get("startTimestamp", 0)).strftime("%Y-%m-%d"),
                    "Country": info["country"], "LeagueCode": code, "LeagueName": info["name"],
                    "HomeTeam": ev.get("homeTeam", {}).get("name",""),
                    "AwayTeam": ev.get("awayTeam", {}).get("name",""),
                    "HomeGoals": ev.get("homeScore",{}).get("current"),
                    "AwayGoals": ev.get("awayScore",{}).get("current"),
                    "source": "SS"
                })
        except Exception as e:
            log(f"[SS][{code}] error: {e}", logfile)
        cur += timedelta(days=7)
        polite_sleep()
    return pd.DataFrame(rows)

def fetch_flashscore_month(code: str, info: Dict, y: int, m: int, visible: bool, logfile: str) -> pd.DataFrame:
    try:
        import nest_asyncio; nest_asyncio.apply()
        from requests_html import HTMLSession
    except Exception as e:
        log(f"[FS][{code}] import failed: {e}", logfile)
        return pd.DataFrame(columns=[])
    os.environ["PYPPETEER_HEADLESS"] = "false" if visible else "true"
    session = HTMLSession()
    headers = {"User-Agent": UA, "Accept-Language":"en-US,en;q=0.9"}
    rows = []
    url = BASE_FS + info["path"] + "fixtures/"
    try:
        r = session.get(url, headers=headers, timeout=30)
        r.html.render(timeout=25, sleep=1.2, keep_page=False, scrolldown=1)
        blocks = r.html.find("div.event__day")
        for b in blocks:
            head = b.find("div.event__title--name", first=True)
            if not head or not head.text: continue
            try:
                d = datetime.strptime(head.text.strip(), "%d %b %Y").date()
            except Exception:
                continue
            if d.year != y or d.month != m: continue
            matches = b.find("div.event__match")
            for mdiv in matches:
                home = mdiv.find("div.event__participant--home", first=True)
                away = mdiv.find("div.event__participant--away", first=True)
                hg_el = mdiv.find("div.event__score--home", first=True)
                ag_el = mdiv.find("div.event__score--away", first=True)
                home_team = (home.text or "").strip() if home else ""
                away_team = (away.text or "").strip() if away else ""
                hg = int(hg_el.text.strip()) if (hg_el and hg_el.text.strip().isdigit()) else None
                ag = int(ag_el.text.strip()) if (ag_el and ag_el.text.strip().isdigit()) else None
                if not home_team or not away_team: continue
                rows.append({
                    "Date": d.strftime("%Y-%m-%d"),
                    "Country": info["country"], "LeagueCode": code, "LeagueName": info["name"],
                    "HomeTeam": home_team, "AwayTeam": away_team,
                    "HomeGoals": hg, "AwayGoals": ag, "source": "FS"
                })
    except Exception as e:
        log(f"[FS][{code}] render/parse failed: {e}", logfile)
    finally:
        try: r.close()
        except Exception: pass
        try: session.close()
        except Exception: pass
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
    key = ["Date","LeagueCode","HomeTeam","AwayTeam","source"]
    df = df.sort_values(key).drop_duplicates(subset=["Date","LeagueCode","HomeTeam","AwayTeam"], keep="last")
    def calc(row):
        hg, ag = row["HomeGoals"], row["AwayGoals"]
        if pd.isna(hg) or pd.isna(ag):
            return pd.Series({"BTTS":None,"Over1_5":None,"Over2_5":None,"Over3_5":None})
        total = int(hg)+int(ag)
        return pd.Series({
            "BTTS":1 if (int(hg)>0 and int(ag)>0) else 0,
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
            return f"{yr}-{str(yr+1)[-2:]}" if d.month>=8 else f"{yr-1}-{str(yr)[-2:]}"
        except Exception:
            return None
    df["Season"] = df["Date"].apply(season_of)
    for c in ["Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]:
        if c not in df.columns: df[c] = None
    cols = ["Date","Season","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam",
            "HomeGoals","AwayGoals","BTTS","Over1_5","Over2_5","Over3_5",
            "Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]
    return df[cols]

def save_excel_per_country(df: pd.DataFrame, path: str, logfile: str):
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            for country, gdf in df.groupby("Country"):
                gdf_sorted = gdf.sort_values(["Date","LeagueCode","HomeTeam","AwayTeam"])
                gdf_sorted.to_excel(w, sheet_name=country[:31], index=False)
        log(f"[OK] Saved {len(df)} rows to {path}", logfile)
    except Exception as e:
        log(f"[ERR] Excel save failed: {e}", logfile)
def filter_leagues_by_selection(fs_leagues, country_name, league_name):
    """Φιλτράρει FS_LEAGUES και επιστρέφει μόνο τη λίγκα που επέλεξε ο χρήστης"""
    filtered = {}
    for code, info in fs_leagues.items():
        if info["country"].lower() == country_name.lower() and league_name.lower() in info["name"].lower():
            filtered[code] = info
    return filtered
def main():
    country, league = choose_country_and_league()
    last_country, last_league = load_last_selection()
    if last_country and last_league:
        use_last = input(f"\n➡️ Να χρησιμοποιηθεί η προηγούμενη επιλογή ({last_country} – {last_league}) ; (y/n): ").strip().lower()
        if use_last == "y":
            print(f"\n✅ Χρήση προηγούμενης επιλογής: {last_country} – {last_league}\n")
            return last_country, last_league

    if not country:
        print("Έξοδος λόγω μη επιλογής.")
        return
    global FS_LEAGUES
    FS_LEAGUES = filter_leagues_by_selection(FS_LEAGUES, country, league)
    if not FS_LEAGUES:
        print(f"⚠️ Δεν βρέθηκε λίγκα για {country} – {league}")
        return
    else:
        print(f"✅ Ενεργή λίγκα: {list(FS_LEAGUES.keys())}")
        parser = argparse.ArgumentParser()
        parser.add_argument("--visible", action="store_true")
        parser.add_argument("--log", type=str, default=DEFAULT_LOG)
    args = parser.parse_args()

    logfile = args.log
    start_d = season_start_from_august(date.today())
    end_d = date.today()

    frames: List[pd.DataFrame] = []
    # Flashscore months between start_d and end_d
    months = []
    cur = date(start_d.year, start_d.month, 1)
    while cur <= end_d:
        months.append((cur.year, cur.month))
        if cur.month == 12: cur = date(cur.year+1, 1, 1)
        else: cur = date(cur.year, cur.month+1, 1)

    for code, info in FS_LEAGUES.items():
        for (yy, mm) in months:
            fsdf = fetch_flashscore_month(code, info, yy, mm, visible=args.visible, logfile=logfile)
            if not fsdf.empty: frames.append(fsdf)
            polite_sleep()

    for code, meta in SS_TOURNAMENTS.items():
        ssdf = fetch_sofascore_range(code, meta, start_d, end_d, logfile=logfile)
        if not ssdf.empty: frames.append(ssdf)
        polite_sleep()

    if not frames:
        print("EURO_GOALS v6f_fast — No data collected. Check log for details.")
        return

    unified = unify(pd.concat(frames, ignore_index=True))
    unified = unified[(pd.to_datetime(unified["Date"])>=pd.to_datetime(start_d)) &
                      (pd.to_datetime(unified["Date"])<=pd.to_datetime(end_d))]

    save_excel_per_country(unified, EXCEL_PATH, logfile)
    print(f"EURO_GOALS v6f_fast — completed ✅ Saved {len(unified)} rows to {EXCEL_PATH}")
def choose_country_and_league():
    last_country, last_league = load_last_selection()
    if last_country and last_league:
       use_last = input(f"\n➡️  Να χρησιμοποιηθεί η προηγούμενη επιλογή ({last_country} – {last_league}) ; (Y/n): ").strip().lower()
if use_last in ["", "y"]:  # Enter = ναι
    print(f"\n✅ Χρήση προηγούμενης επιλογής: {last_country} – {last_league}\n")
    return last_country, last_league
 
    """Μενού επιλογής χώρας και λίγκας"""
    countries = list_countries()
    print("\nΔιαθέσιμες χώρες:")
    for i, c in enumerate(countries, 1):
        print(f"{i}. {c}")

    choice = input("\nΕπιλέξτε χώρα (όνομα ή αριθμό): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(countries):
            country_name = countries[idx]
        else:
            print("❌ Μη έγκυρος αριθμός.")
            return None, None
    else:
        country_name = choice.title()

    country = get_country(country_name)
    if not country:
        print("❌ Δεν βρέθηκε χώρα.")
        return None, None

    print(f"\nΛίγκες για {country.country}:")
    for i, div in enumerate(country.divisions, 1):
        print(f"{i}. {div.name}")

    lvl_choice = input("\nΕπιλέξτε λίγκα (όνομα ή αριθμό): ").strip()
    if lvl_choice.isdigit():
        idx = int(lvl_choice) - 1
        if 0 <= idx < len(country.divisions):
            division = country.divisions[idx]
        else:
            print("❌ Μη έγκυρος αριθμός.")
            return None, None
    else:
        matches = [d for d in country.divisions if lvl_choice.lower() in d.name.lower()]
        division = matches[0] if matches else None

    if not division:
        print("❌ Δεν βρέθηκε λίγκα.")
        return None, None
    print(f"💾 Αποθηκεύτηκε τελευταία επιλογή: {country.country} – {division.name}")
    print(f"\n✅ Επιλογή: {country.country} — {division.name}\n")
   
    return country.country, division.name
if __name__ == "__main__":
    main()
    
#print("Σύνδεση με europelist.py OK ✅")
#print("Πρώτες 10 χώρες:", list_countries()[:10])
#gr = get_country("Greece")
#print("Λίγκες Ελλάδας:")
#for d in gr.divisions:
#    print(f"  L{d.level}: {d.name} ({d.code})")
 # main()