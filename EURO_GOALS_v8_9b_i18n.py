# ============================================================
# EURO_GOALS v8.9b – System Status Panel (Feeds + i18n)
# ============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from datetime import datetime
import os, psutil, random, json

# ------------------------------------------------------------
# 1. Γενικές Ρυθμίσεις & Μεταφράσεις
# ------------------------------------------------------------
LANGUAGE = os.getenv("LANGUAGE", "gr")

def load_translations():
    try:
        with open("translations.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(LANGUAGE, data["gr"])
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Translation load error: {e}")
        return {}

translations = load_translations()

app = FastAPI(title="EURO_GOALS – System Status Panel (Feeds + i18n)")
templates = Jinja2Templates(directory="templates")
templates.env.globals["t"] = translations
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ------------------------------------------------------------
# 2. Πίνακας feeds στη βάση
# ------------------------------------------------------------
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS feeds (
            id SERIAL PRIMARY KEY,
            name TEXT,
            alias TEXT UNIQUE,
            type TEXT,
            base_url TEXT,
            status TEXT,
            active BOOLEAN,
            fallback TEXT
        );
        """))
        conn.commit()

        result = conn.execute(text("SELECT COUNT(*) FROM feeds"))
        count = result.scalar()
        if count == 0:
            print("[EURO_GOALS] ⚙️ Initializing default feeds...")
            default_feeds = [
                {"name": "Live Source #1", "alias": "flashscore", "type": "unofficial_feed", "base_url": "https://www.flashscore.com/x/feed/", "status": "OK", "active": True, "fallback": "openfootball"},
                {"name": "Live Source #2", "alias": "sofascore", "type": "semi_official_api", "base_url": "https://api.sofascore.com/api/v1/", "status": "OK", "active": True, "fallback": "openfootball"},
                {"name": "Historical Data Feed", "alias": "besoccer", "type": "official_api", "base_url": "https://apiclient.besoccerapps.com/scripts/api/api.php", "status": "Pending", "active": True, "fallback": "openfootball"},
                {"name": "Smart Odds Monitor", "alias": "pinnacle", "type": "asian_odds_feed", "base_url": "https://api.pinnacle.com/", "status": "Planned", "active": False, "fallback": "none"},
                {"name": "Backup Data Source", "alias": "openfootball", "type": "open_source", "base_url": "https://github.com/openfootball", "status": "OK", "active": True, "fallback": "none"}
            ]
            for f in default_feeds:
                conn.execute(text("""
                    INSERT INTO feeds (name, alias, type, base_url, status, active, fallback)
                    VALUES (:name, :alias, :type, :base_url, :status, :active, :fallback)
                """), f)
            conn.commit()
            print("[EURO_GOALS] ✅ Default feeds inserted.")

def fetch_feeds():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM feeds ORDER BY id"))
        return [dict(row._mapping) for row in result]

def save_all_feeds(feeds):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM feeds"))
        for f in feeds:
            conn.execute(text("""
                INSERT INTO feeds (name, alias, type, base_url, status, active, fallback)
                VALUES (:name, :alias, :type, :base_url, :status, :active, :fallback)
            """), f)
        conn.commit()
    return True

# ------------------------------------------------------------
# 3. Routes
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    feeds = fetch_feeds()
    jobs = [
        {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
        {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
        {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
    ]
    return templates.TemplateResponse("index.html", {"request": request, "feeds": feeds, "jobs": jobs})

@app.get("/admin/feeds", response_class=HTMLResponse)
async def admin_feeds(request: Request):
    return templates.TemplateResponse("admin_feeds.html", {"request": request})

@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
    feeds = fetch_feeds()
    return {"feeds": feeds, "count": len(feeds)}

@app.post("/api/feeds/save", response_class=JSONResponse)
async def save_feeds_api(payload: dict = Body(...)):
    feeds = payload.get("feeds", [])
    save_all_feeds(feeds)
    return {"ok": True, "count": len(feeds)}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# ------------------------------------------------------------
# 4. Εκκίνηση
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Starting EURO_GOALS v8.9b (i18n)")
    init_db()
    print(f"[EURO_GOALS] ✅ Language set: {LANGUAGE}")
    print("[EURO_GOALS] ✅ Database ready & feeds initialized.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9b_i18n:app", host="0.0.0.0", port=8000, reload=True)
