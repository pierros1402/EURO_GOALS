from fastapi import FastAPI
app = FastAPI()
print("🚀 Render new deploy check")

@app.get("/")
def home():
    return {"status": "ok", "message": "EURO_GOALS Render online ✅"}

print("⚽ EURO_GOALS ξεκινά κανονικά...")
# ("Πατήστε Enter για έξοδο")

# EURO_GOALS v6f_render_final.py
# Stable version for Render (FastAPI + Flashscore + Sofascore + Excel Export)
# Works both locally and on Render.com

from fastapi import FastAPI
import pandas as pd
import os, sys, time, json, random
from datetime import datetime, timedelta
from typing import Dict

# ===============================================================
# 1️⃣ FastAPI initialization
# ===============================================================
app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "EURO_GOALS Render online ✅"}

print("🌍 EURO_GOALS ξεκινά κανονικά...")

# ===============================================================
# 2️⃣ Configuration
# ===============================================================
BASE_FS = "https://www.flashscore.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_LOG = os.path.join(SCRIPT_DIR, "EURO_GOALS_log.txt")
RUN_DATE = datetime.now().strftime("%Y-%m-%d")
EXCEL_PATH = os.path.join(SCRIPT_DIR, f"EURO_GOALS_{RUN_DATE}.xlsx")
SHEET = "Matches"

# ===============================================================
# 3️⃣ Logging utility
# ===============================================================
def log(msg: str, logfile: str = DEFAULT_LOG):
    t = datetime.now().strftime("[%H:%M:%S]")
    line = f"{t} {msg}"
    print(line)
    try:
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"⚠️ Log error: {e}")

# ===============================================================
# 4️⃣ Placeholder data collection functions
# (Simulate Flashscore + Sofascore scrapers)
# ===============================================================
def polite_sleep():
    time.sleep(0.5)

def collect_flashscore() -> pd.DataFrame:
    log("Collecting Flashscore data...", DEFAULT_LOG)
    data = [{"League": "Premier League", "Home": "Arsenal", "Away": "Chelsea", "Score": "2-1"}]
    polite_sleep()
    return pd.DataFrame(data)

def collect_sofascore() -> pd.DataFrame:
    log("Collecting Sofascore data...", DEFAULT_LOG)
    data = [{"League": "La Liga", "Home": "Barcelona", "Away": "Real Madrid", "Score": "3-2"}]
    polite_sleep()
    return pd.DataFrame(data)

# ===============================================================
# 5️⃣ Merge and save data
# ===============================================================
def unify(df: pd.DataFrame) -> pd.DataFrame:
    log("Unifying data...", DEFAULT_LOG)
    df.drop_duplicates(inplace=True)
    return df

def save_excel(df: pd.DataFrame, logfile: str):
    try:
        df.to_excel(EXCEL_PATH, index=False, sheet_name=SHEET)
        log(f"Saved Excel → {EXCEL_PATH}", logfile)
    except Exception as e:
        log(f"❌ Excel save failed: {e}", logfile)

# ===============================================================
# 6️⃣ Main function logic
# ===============================================================
def main():
    frames = []

    fs = collect_flashscore()
    if not fs.empty:
        frames.append(fs)

    ss = collect_sofascore()
    if not ss.empty:
        frames.append(ss)

    if not frames:
        log("[WARN] No data collected from either source.", DEFAULT_LOG)
        return

    unified = unify(pd.concat(frames, ignore_index=True))
    save_excel(unified, logfile)
    log("EURO_GOALS v6f_debug – done ✅", logfile)
# input("Πατήστε Enter για έξοδο")


=======
    save_excel(unified, DEFAULT_LOG)
    log("EURO_GOALS v6f_render_final – done ✅", DEFAULT_LOG)

# ===============================================================
# 7️⃣ Entry point for local & Render environments
# ===============================================================
# ===============================================================
# 🔹 FastAPI endpoint για odds
# ===============================================================
from odds_reader import get_odds, get_odds_bundle

@app.get("/odds/{sport_key}")
def odds_route(sport_key: str, mode: str = "simple"):
    """
    Παίρνει αποδόσεις & pseudo-trend index.
    Παραδείγματα:
    /odds/soccer_epl?mode=simple
    /odds/soccer_epl?mode=combined
    """
    data = get_odds(sport_key, mode)
    return data


@app.get("/odds_bundle/{bundle}")
def odds_bundle_route(bundle: str):
    """
    Παράδειγμα κλήσεων:
    /odds_bundle/england_all
    /odds_bundle/greece_1_2_3
    /odds_bundle/germany_1_2_3
    /odds_bundle/europe_1_2
    """
    return get_odds_bundle(bundle)


    """
    Παίρνει αποδόσεις & pseudo-trend index.
    Παραδείγματα:
      /odds/soccer_epl?mode=simple
      /odds/soccer_epl?mode=combined
    """
    data = get_odds(sport_key, mode)
    return data



# Entry point for local & Render environments

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("EURO_GOALS_v6f_render_final:app", host="0.0.0.0", port=port)
# ==========================================================
# AUTO REFRESH CACHE THREAD (every 10 minutes)
# ==========================================================
import threading
import time
import requests
# from asian_reader import detect_smart_money

def auto_refresh_cache():
    urls = [
        "https://euro-goals.onrender.com/odds_bundle/england_all",
        "https://euro-goals.onrender.com/odds_bundle/greece_1_2_3",
        "https://euro-goals.onrender.com/odds_bundle/germany_1_2_3",
        "https://euro-goals.onrender.com/odds_bundle/europe_1_2",
    ]
    while True:
        print("[AUTO REFRESH] Refreshing odds bundles...")
        for url in urls:
            try:
                r = requests.get(url, timeout=20)
                if r.status_code == 200:
                    print(f"[AUTO REFRESH] ✅ Updated: {url}")
                else:
                    print(f"[AUTO REFRESH] ⚠️ {url} returned {r.status_code}")
            except Exception as e:
                print(f"[AUTO REFRESH] ❌ Error for {url}: {e}")
        time.sleep(600)  # 10 λεπτά

        # --- Smart Money Check ---
        # detect_smart_money()

threading.Thread(target=auto_refresh_cache, daemon=True).start()

