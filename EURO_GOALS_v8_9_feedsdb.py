# ============================================================
# EURO_GOALS v8.9 – System Status Panel (Feeds stored in PostgreSQL)
# ============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from datetime import datetime
import os, psutil, random

# ------------------------------------------------------------
# 1. FastAPI & DB setup
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – System Status Panel (Feeds in DB)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ------------------------------------------------------------
# 2. Initialize feeds table (if not exists)
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

        # Αν δεν υπάρχουν δεδομένα, αρχικοποιούμε 5 default feeds
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

# ------------------------------------------------------------
# 3. Helper functions
# ------------------------------------------------------------
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

def toggle_feed(alias, active):
    with engine.connect() as conn:
        res = conn.execute(text("UPDATE feeds SET active=:a WHERE alias=:b"), {"a": active, "b": alias})
        conn.commit()
        return res.rowcount > 0

# ------------------------------------------------------------
# 4. UI Routes
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    feeds = fetch_feeds()
    jobs = [
        {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
        {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
        {"name": "Alert Cleanup", "status": "Queued", "next_run": "depth: 1"},
        {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
    ]
    return templates.TemplateResponse("index.html", {"request": request, "feeds": feeds, "jobs": jobs})

@app.get("/admin/feeds", response_class=HTMLResponse)
async def admin_feeds(request: Request):
    return templates.TemplateResponse("admin_feeds.html", {"request": request})

# ------------------------------------------------------------
# 5. API Routes
# ------------------------------------------------------------
@app.get("/api/system_status", response_class=JSONResponse)
async def system_status():
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = round(psutil.virtual_memory().used / (1024 ** 3), 1)
        disk = psutil.disk_usage("/").percent
        db_status = "Connected"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "Error"

        return {
            "server": "Healthy",
            "database": db_status,
            "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "alerts_24h": random.randint(10, 25),
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "errors": random.randint(0, 2),
            "logs": [f"[DB] Connection {db_status}", f"[INFO] System OK ({random.randint(120,280)}ms)"]
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
    feeds = fetch_feeds()
    return {"feeds": feeds, "count": len(feeds)}

@app.post("/api/feeds/save", response_class=JSONResponse)
async def save_feeds_api(payload: dict = Body(...)):
    feeds = payload.get("feeds", [])
    save_all_feeds(feeds)
    return {"ok": True, "count": len(feeds)}

@app.post("/api/feeds/toggle", response_class=JSONResponse)
async def toggle_feed_api(payload: dict = Body(...)):
    alias = payload.get("alias")
    active = bool(payload.get("active", True))
    ok = toggle_feed(alias, active)
    if ok:
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "alias_not_found"}, status_code=404)

# ------------------------------------------------------------
# 6. Health Check (Render)
# ------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# ------------------------------------------------------------
# 7. Startup Event
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Starting System Status Panel (DB Feeds)...")
    init_db()
    print("[EURO_GOALS] ✅ Database connected & feeds initialized.")

# ------------------------------------------------------------
# 8. Local run
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9_feedsdb:app", host="0.0.0.0", port=8000, reload=True)
