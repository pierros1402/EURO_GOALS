# ==============================================
# EURO_GOALS v8.7_SM – Integrated Season Manager
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv
import os

# ------------------------------------------------------------
# Φόρτωση μεταβλητών περιβάλλοντος
# ------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ============================================================
# SEASON MANAGER (Flashscore Parser – χωρίς API key)
# ============================================================
import requests
from bs4 import BeautifulSoup

FLASH_BASE = "https://www.flashscore.com"
FLASH_LEAGUES = {
    "Premier League": "/football/england/premier-league/",
    "La Liga": "/football/spain/laliga/",
    "Serie A": "/football/italy/serie-a/",
    "Bundesliga": "/football/germany/bundesliga/",
    "Ligue 1": "/football/france/ligue-1/",
    "Super League Greece": "/football/greece/super-league/"
}

def get_recent_seasons():
    current_year = datetime.now().year
    return [f"{current_year-1-i}/{current_year-i}" for i in range(5)]

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

def match_exists(conn, league, date, home, away):
    res = conn.execute(text("""
        SELECT 1 FROM matches 
        WHERE league=:league AND date=:date AND home_team=:home AND away_team=:away
        LIMIT 1
    """), {"league": league, "date": date, "home": home, "away": away}).fetchone()
    return res is not None

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
        print(f"[SEASON MANAGER] 💾 {new_count} νέοι αγώνες για {league} ({season})")

def update_all_leagues(current_only=False):
    seasons = [get_recent_seasons()[0]] if current_only else get_recent_seasons()
    for season in seasons:
        for league_name, path in FLASH_LEAGUES.items():
            url = f"{FLASH_BASE}{path}"
            matches = fetch_matches(url, season)
            insert_into_db(matches, league_name, season)
    print("[SEASON MANAGER] ✅ Ενημέρωση ολοκληρώθηκε.")

# ============================================================
# STARTUP EVENT – ενημέρωση βάσης με σεζόν
# ============================================================
@app.on_event("startup")
def startup_event():
    import time
    print("[EURO_GOALS] 🚀 Εκκίνηση εφαρμογής...")

    # Προσωρινή καθυστέρηση 10'' για να προλάβει το Render health check
    # (αν περάσει επιτυχώς, μπορεί να αφαιρεθεί)
    time.sleep(10)

    try:
        # Ενημέρωση όλων των πρωταθλημάτων (τρέχουσα + παλαιότερες σεζόν)
        update_all_leagues(current_only=False)
        print("[EURO_GOALS] ✅ Βάση ενημερωμένη.")
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Σφάλμα κατά την ενημέρωση βάσης: {e}")
    finally:
        print("[EURO_GOALS] 🩺 Startup check ολοκληρώθηκε.")

# ============================================================

# ROUTES
# ============================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "EURO_GOALS v8.7_SM – Active"})

@app.get("/api/matches")
def get_matches(limit: int = 50):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM matches ORDER BY date DESC LIMIT :limit"), {"limit": limit})
        data = [dict(row._mapping) for row in result]
    return JSONResponse(content={"matches": data})

# ============================================================
# MANUAL REFRESH ENDPOINT
# ============================================================
@app.get("/api/refresh")
def manual_refresh():
    update_all_leagues(current_only=False)
    return JSONResponse(content={"status": "ok", "message": "Ενημέρωση βάσης ολοκληρώθηκε."})

# ============================================================
# INFO
# ============================================================
@app.get("/api/info")
def info():
    return {
        "version": "8.7_SM",
        "status": "active",
        "source": "Flashscore Parser (no API key)",
        "seasons_loaded": get_recent_seasons()
    }
# ============================================================
# STARTUP EVENT – ενημέρωση βάσης με σεζόν
# ============================================================
@app.on_event("startup")
def startup_event():
    import time
    print("[EURO_GOALS] 🚀 Εκκίνηση εφαρμογής...")

    # Μικρή καθυστέρηση για να προλάβει το Render health check
    time.sleep(10)

    try:
        update_all_leagues(current_only=False)
        print("[EURO_GOALS] ✅ Βάση ενημερωμένη.")
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Σφάλμα κατά την ενημέρωση βάσης: {e}")
    finally:
        print("[EURO_GOALS] 🩺 Startup check ολοκληρώθηκε.")


# ============================================================
# HEALTH CHECK ENDPOINT (Render)
# ============================================================
from fastapi.responses import JSONResponse

@app.get("/api/health")
async def health_check():
    """
    Render health check endpoint.
    Επιστρέφει 200 OK για να θεωρηθεί επιτυχής η εκκίνηση.
    """
    return JSONResponse(content={"status": "ok"}, status_code=200)


@app.head("/api/health")
async def health_check_head():
    """
    Υποστήριξη HEAD αιτημάτων (που στέλνει το Render).
    """
    return JSONResponse(content={}, status_code=200)


# ============================================================
# ΤΕΛΟΣ EURO_GOALS_v8_7_SM
# ============================================================

