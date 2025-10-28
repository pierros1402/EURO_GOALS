# ============================================================
# EURO_GOALS v8.8 – System Status Panel (Dynamic Feeds + Admin)
# ============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from datetime import datetime
from pathlib import Path
import os, psutil, random, json

# ------------------------------------------------------------
# 1. FastAPI & static / templates
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – System Status Panel")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ------------------------------------------------------------
# 2. feeds.json helpers
# ------------------------------------------------------------
FEEDS_FILE = Path("feeds.json")

def load_feeds():
    try:
        with FEEDS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("[EURO_GOALS] ⚠️ feeds.json not loaded:", e)
        return []

def save_feeds(feeds):
    try:
        tmp = FEEDS_FILE.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(feeds, f, ensure_ascii=False, indent=2)
        tmp.replace(FEEDS_FILE)
        return True
    except Exception as e:
        print("[EURO_GOALS] ❌ save_feeds error:", e)
        return False

feeds_cache = load_feeds()

# ------------------------------------------------------------
# 3. Demo jobs (placeholder)
# ------------------------------------------------------------
jobs_demo = [
    {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
    {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
    {"name": "Alert Cleanup", "status": "Queued", "next_run": "depth: 1"},
    {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
]

# ------------------------------------------------------------
# 4. Routes – UI
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    global feeds_cache
    feeds_cache = load_feeds()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "feeds": feeds_cache, "jobs": jobs_demo},
    )

@app.get("/admin/feeds", response_class=HTMLResponse)
async def admin_feeds(request: Request):
    return templates.TemplateResponse("admin_feeds.html", {"request": request})

# ------------------------------------------------------------
# 5. Routes – APIs
# ------------------------------------------------------------
@app.get("/api/system_status", response_class=JSONResponse)
async def system_status():
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = round(psutil.virtual_memory().used / (1024 ** 3), 1)
        disk = psutil.disk_usage("/").percent
        errors = random.randint(0, 2)
        alerts_24h = random.randint(10, 25)
        db_status = "Connected"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "Error"
        log_lines = [
            f"[INFO] System OK ({random.randint(120,280)}ms)",
            *[f"[FEED:{f.get('alias','?')}] status {f.get('status','?')}" for f in feeds_cache],
            f"[DB] Connection {db_status}",
        ]
        return {
            "server": "Healthy",
            "database": db_status,
            "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "alerts_24h": alerts_24h,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "errors": errors,
            "logs": log_lines,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
    feeds = load_feeds()
    return {"feeds": feeds, "count": len(feeds)}


@app.post("/api/feeds/save", response_class=JSONResponse)
async def save_feeds_endpoint(payload: dict = Body(...)):
    feeds = payload.get("feeds", [])
    ok = save_feeds(feeds)
    if ok:
        global feeds_cache
        feeds_cache = feeds
        return {"ok": True, "count": len(feeds)}
    return JSONResponse({"ok": False, "error": "write_failed"}, status_code=500)


@app.post("/api/feeds/toggle", response_class=JSONResponse)
async def toggle_feed(payload: dict = Body(...)):
    alias = payload.get("alias")
    active = bool(payload.get("active", True))
    feeds = load_feeds()
    changed = False
    for f in feeds:
        if f.get("alias") == alias:
            f["active"] = active
            changed = True
            break
    if not changed:
        return JSONResponse({"ok": False, "error": "alias_not_found"}, status_code=404)
    if save_feeds(feeds):
        global feeds_cache
        feeds_cache = feeds
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "write_failed"}, status_code=500)

# ------------------------------------------------------------
# 6. Health check (Render)
# ------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# ------------------------------------------------------------
# 7. Startup event
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 System Status Panel starting…")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"[EURO_GOALS] 📡 feeds.json loaded: {len(feeds_cache)} feeds")

# ------------------------------------------------------------
# 8. Local run
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_8_status_clean:app", host="0.0.0.0", port=8000, reload=True)
