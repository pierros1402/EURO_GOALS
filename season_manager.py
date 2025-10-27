# ==============================================
# EURO_GOALS – Season Manager v2 (Flashscore Parser)
# ==============================================
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
import os

# --- Ρύθμιση βάσης --------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# --- Flashscore URLs -----------------------------
FLASH_BASE = "https://www.flashscore.com"
FLASH_LEAGUES = {
    "Premier League": "/football/england/premier-league/",
    "La Liga": "/football/spain/laliga/",
    "Serie A": "/football/italy/serie-a/",
    "Bundesliga": "/football/germany/bundesliga/",
    "Ligue 1": "/football/france/ligue-1/",
    "Super League Greece": "/football/greece/super-league/"
}

# --- Δημιουργία λίστας τελευταίων 5 σεζόν ----------------
def get_recent_seasons():
    current_year = datetime.now().year
    seasons = []
    for i in range(5):
        seasons.append(f"{current_year-1-i}/{current_year-i}")
    return seasons  # π.χ. ['2024/2025', '2023/2024', '2022/2023', '2021/2022', '2020/2021']

# --- Εξαγωγή αγώνων από Flashscore -------------------------------
def fetch_matches(league_url, season):
    try:
        print(f"[SEASON MANAGER] 🔍 Λήψη δεδομένων για {season} – {league_url}")
        r = requests.get(league_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        matches = []
        for match in soup.select("div.event__match"):
            date = match.get("data-date")
            home = match.select_one(".event__participant--home").text.strip() if match.select_one(".event__participant--home") else ""
            away = match.select_one(".event__participant--away").text.strip() if match.select_one(".event__participant--away") else ""
            score = match.select_one(".event__scores").text.strip() if match.select_one(".event__scores") else ""
            matches.append({"date": date, "home": home, "away": away, "score": score})
        print(f"[SEASON MANAGER] ✅ {len(matches)} αγώνες ελήφθησαν")
        return matches

    except Exception as e:
        print(f"[SEASON MANAGER] ❌ Σφάλμα λήψης δεδομένων: {e}")
        return []

# --- Έλεγχος αν υπάρχουν ήδη στη βάση -------------------------------
def match_exists(conn, league, date, home, away):
    res = conn.execute(text("""
        SELECT 1 FROM matches 
        WHERE league=:league AND date=:date AND home_team=:home AND away_team=:away
        LIMIT 1
    """), {"league": league, "date": date, "home": home, "away": away}).fetchone()
    return res is not None

# --- Εισαγωγή στη βάση ------------------------------------------
def insert_into_db(matches, league, season):
    if not matches:
        return
    with engine.begin() as conn:
        new_count = 0
        for m in matches:
            if not match_exists(conn, league, m["date"], m["home"], m["away"]):
                conn.execute(text("""
                    INSERT INTO matches (league, season, date, home_team, away_team, score)
                    VALUES (:league, :season, :date, :home, :away, :score)
                """), {"league": league, "season": season, "date": m["date"], "home": m["home"], "away": m["away"], "score": m["score"]})
                new_count += 1
        print(f"[SEASON MANAGER] 💾 Εισαγωγή {new_count} νέων αγώνων για {league} ({season})")

# --- Κύρια εκτέλεση ---------------------------------------------
def update_all_leagues(current_only=False):
    seasons = [get_recent_seasons()[0]] if current_only else get_recent_seasons()
    for season in seasons:
        for league_name, path in FLASH_LEAGUES.items():
            url = f"{FLASH_BASE}{path}"
            matches = fetch_matches(url, season)
            insert_into_db(matches, league_name, season)
    print("[SEASON MANAGER] ✅ Ολοκλήρωση ενημέρωσης.")

if __name__ == "__main__":
    update_all_leagues(current_only=False)
