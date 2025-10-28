# =============================================================
# EURO_GOALS v8.9d – Auto-Fallback + Live System Status API
# =============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from datetime import datetime
import os, psutil, json

# -------------------------------------------------------------
# 1. Import custom data router (auto-fallback system)
# -------------------------------------------------------------
from data_router import get_data_auto, log_event

# -------------------------------------------------------------
# 2. Language setup (multilingual translations)
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 3. FastAPI setup
# -------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – Auto-Fallback + Live API")
templates = Jinja2Templates(directory="templates")
templates.env.globals["t"] = translations
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------
# 4. Database connection (Render PostgreSQL or local SQLite)
# -------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# -------------------------------------------------------------
# 5. Feeds loader
# -------------------------------------------------------------
def load_feeds():
    try:
        with open("feeds.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("feeds", [])
    except Exception as e:
        print("[EURO_GOALS] ❌ Σφάλμα ανάγνωσης feeds.json:", e)
        return []

# =============================================================
#  API ROUTES
# =============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    feeds = load_feeds()
    data_result = get_data_auto()
    active_source = data_result["source"] if data_result else "none"

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "feeds": feeds, "active_source": active_source}
    )

# -------------------------------------------------------------
# System Status API – for monitoring panel
# -------------------------------------------------------------
@app.get("/api/system_status", response_class=JSONResponse)
async def system_status():
    """
    Live endpoint για το Status Panel – επιστρέφει CPU, RAM, active feed, logs
    """
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    feeds = load_feeds()

    active = "none"
    for f in feeds:
        if f.get("active") and f.get("status") == "OK":
            active = f["alias"]

    # Ανάγνωση τελευταίων 5 γραμμών log
    logs = []
    try:
        with open("log_dualsource.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            logs = lines[-5:]
    except FileNotFoundError:
        logs = ["[LOG] No events recorded yet."]

    return {
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": cpu,
        "ram": ram,
        "active_feed": active,
        "logs": logs
    }

# -------------------------------------------------------------
# Feeds endpoints
# -------------------------------------------------------------
@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
    feeds = load_feeds()
    return {"feeds": feeds, "count": len(feeds)}

@app.post("/api/feeds/save", response_class=JSONResponse)
async def save_feeds(payload: dict = Body(...)):
    feeds = payload.get("feeds", [])
    with open("feeds.json", "w", encoding="utf-8") as f:
        json.dump({"feeds": feeds, "count": len(feeds)}, f, indent=2, ensure_ascii=False)
    log_event(f"💾 Feeds updated manually ({len(feeds)} entries)")
    return {"ok": True, "count": len(feeds)}

# -------------------------------------------------------------
# Health check
# -------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# -------------------------------------------------------------
# Startup event
# -------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Starting v8.9d – Auto-Fallback + Live API")
    print(f"[EURO_GOALS] 🌐 Language: {LANGUAGE}")
    print(f"[EURO_GOALS] 📡 Data Router Ready (feeds monitored)")
