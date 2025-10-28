# =============================================================
# EURO_GOALS v8.9c – System Status Panel + Auto-Fallback Feeds
# =============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from datetime import datetime
import os, psutil, json

# -------------------------------------------------------------
# 1. Εισαγωγή Auto-Fallback Router
# -------------------------------------------------------------
from data_router import get_data_auto, log_event

# -------------------------------------------------------------
# 2. Ρυθμίσεις μεταφράσεων (πολυγλωσσικό σύστημα)
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
# 3. FastAPI & Templates
# -------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – Auto-Fallback System")
templates = Jinja2Templates(directory="templates")
templates.env.globals["t"] = translations
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------
# 4. Σύνδεση βάσης
# -------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# -------------------------------------------------------------
# 5. Ανάγνωση feeds.json για εμφάνιση
# -------------------------------------------------------------
def load_feeds():
    try:
        with open("feeds.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("feeds", [])
    except Exception as e:
        print("[EURO_GOALS] ❌ Σφάλμα ανάγνωσης feeds.json:", e)
        return []

# -------------------------------------------------------------
# 6. ROUTES
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    feeds = load_feeds()
    jobs = [
        {"name": "Season Sync", "status": "Running", "next_run": "02:30"},
        {"name": "Health Check", "status": "Scheduled", "next_run": "1 min"},
        {"name": "DB Backup", "status": "Idle", "next_run": "Sunday 03:00"},
    ]

    # Προσπαθεί να πάρει δεδομένα από ενεργή πηγή
    data_result = get_data_auto()
    active_source = data_result["source"] if data_result else "none"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "feeds": feeds,
            "jobs": jobs,
            "active_source": active_source
        }
    )

@app.get("/admin/feeds", response_class=HTMLResponse)
async def admin_feeds(request: Request):
    return templates.TemplateResponse("admin_feeds.html", {"request": request})

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

@app.get("/api/health")
async def health_check():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    return {"status": "ok", "cpu": cpu, "ram": ram}

# -------------------------------------------------------------
# 7. Εκκίνηση
# -------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Starting v8.9c – Auto-Fallback Edition")
    print(f"[EURO_GOALS] 🌐 Language: {LANGUAGE}")
    print(f"[EURO_GOALS] 📡 Data Router Ready (feeds monitored)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9c_autofallback:app", host="0.0.0.0", port=8000)
