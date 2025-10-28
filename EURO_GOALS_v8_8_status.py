# ============================================================
# EURO_GOALS v8.8 – System Status Panel (Dynamic Feeds Version)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
import os, psutil, random, json

# ------------------------------------------------------------
# 1. FastAPI & Database setup
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – System Status Panel")
templates = Jinja2Templates(directory="templates")

# ➕ Πρόσθεσε ακριβώς εδώ:
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ------------------------------------------------------------
# 2. Load feeds.json dynamically
# ------------------------------------------------------------
FEEDS_FILE = "feeds.json"

def load_feeds():
    try:
        with open(FEEDS_FILE, "r", encoding="utf-8") as f:
            feeds = json.load(f)
        return feeds
    except Exception as e:
        print("[EURO_GOALS] ⚠️ Δεν βρέθηκε ή δεν ανοίγει το feeds.json:", e)
        return []

feeds_data = load_feeds()

# ------------------------------------------------------------
# 3. Demo jobs (temporary)
# ------------------------------------------------------------
jobs_demo = [
    {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
    {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
    {"name": "Alert Cleanup", "status": "Queued", "next_run": "depth: 1"},
    {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
]

# ------------------------------------------------------------
# 4. Routes
# ------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Φόρτωση feeds πριν τη σελίδα
    global feeds_data
    feeds_data = load_feeds()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "feeds": feeds_data,
            "jobs": jobs_demo,
        },
    )


@app.get("/api/system_status", response_class=JSONResponse)
async def system_status():
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = round(psutil.virtual_memory().used / (1024 ** 3), 1)
        disk = psutil.disk_usage("/").percent
        errors = random.randint(0, 2)
        alerts_24h = random.randint(10, 25)
        db_status = "Connected"

        # Basic DB check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "Error"

        # Logs με αναφορά στα alias (εσωτερικά)
        log_lines = [
            f"[INFO] System OK ({random.randint(120,280)}ms)",
            *[f"[FEED:{f['alias']}] status {f['status']}" for f in feeds_data],
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


# ------------------------------------------------------------
# 5. New endpoint – Feeds JSON API
# ------------------------------------------------------------
@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
    try:
        feeds = load_feeds()
        return {"feeds": feeds, "count": len(feeds)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ------------------------------------------------------------
# 6. Health check endpoint (για Render)
# ------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------
# 7. Startup event
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Εκκίνηση System Status Panel (Dynamic Feeds)...")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[EURO_GOALS] ✅ Βάση συνδέθηκε επιτυχώς.")
    print(f"[EURO_GOALS] 📡 Φορτώθηκαν {len(feeds_data)} πηγές από το feeds.json")

# ------------------------------------------------------------
# 8. Local run
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_8_status:app", host="0.0.0.0", port=8000, reload=True)
