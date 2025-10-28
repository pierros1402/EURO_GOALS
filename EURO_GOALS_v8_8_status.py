# ============================================================
# EURO_GOALS v8.8 – System Status Panel (Render Safe Version)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
import os, psutil, random

# ------------------------------------------------------------
# 1. FastAPI & Database setup
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – System Status Panel")
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# ------------------------------------------------------------
# 2. Data sources (public name + internal alias)
# ------------------------------------------------------------
feeds_demo = [
    {"name": "Live Source #1", "alias": "flashscore", "status": "OK", "detail": "Latency 420ms"},
    {"name": "Live Source #2", "alias": "sofascore", "status": "OK", "detail": "Latency 510ms"},
    {"name": "Historic Data Feed", "alias": "besoccer", "status": "Pending", "detail": "API key needed"},
    {"name": "Smart Odds Monitor", "alias": "pinnacle", "status": "Planned", "detail": "Odds monitoring"},
    {"name": "Backup Data Source", "alias": "openfootball", "status": "OK", "detail": "Local cache"},
]

# ------------------------------------------------------------
# 3. Background jobs (schedule simulation)
# ------------------------------------------------------------
jobs_demo = [
    {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
    {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
    {"name": "Alert Cleanup", "status": "Queued", "next_run": "depth: 1"},
    {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
]

# ------------------------------------------------------------
# 4. Route – main panel (HTML)
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "feeds": feeds_demo,
            "jobs": jobs_demo,
        },
    )

# ------------------------------------------------------------
# 5. Route – system status data (JSON)
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

        # Basic DB check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "Error"

        # Demo logs with alias names (for internal tracing)
        log_lines = [
            f"[INFO] System healthy ({random.randint(120,280)}ms)",
            f"[FEED:{feeds_demo[0]['alias']}] ✓ pull ok",
            f"[FEED:{feeds_demo[1]['alias']}] ✓ pull ok",
            f"[DB] Connection {db_status}",
            f"[ALERT] Smart Money module standby",
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
# 6. Health check endpoint (για Render)
# ------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------
# 6. Startup event
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Εκκίνηση System Status Panel...")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[EURO_GOALS] ✅ Βάση συνδέθηκε επιτυχώς.")

# ------------------------------------------------------------
# 7. Optional – local run (για δοκιμή)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_8_status:app", host="0.0.0.0", port=8000, reload=True)
