# ==============================================
# EURO_GOALS v7.9e – FastAPI Backend (Notifications + Alerts)
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# -------------------------
# App & Templates
# -------------------------
app = FastAPI(title="EURO_GOALS v7.9e")
templates = Jinja2Templates(directory="templates")

if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -------------------------
# Database
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# -------------------------
# Root page
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------
# Service Worker route
# -------------------------
@app.get("/service-worker.js")
async def service_worker():
    path = os.path.join("static", "js", "service-worker.js")
    if not os.path.exists(path):
        return PlainTextResponse("// service-worker missing", media_type="application/javascript")
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    return FileResponse(path, media_type="application/javascript", headers=headers)

# -------------------------
# Notification endpoint
# -------------------------
class NotifyPayload(BaseModel):
    title: str
    body: str | None = None
    icon: str | None = None
    url: str | None = None
    tag: str | None = None
    sound: bool | None = True

@app.post("/notify")
async def notify(payload: NotifyPayload):
    """
    Επιστρέφει payload ειδοποίησης για το front-end.
    """
    return JSONResponse({
        "ok": True,
        "data": payload.dict(),
        "ts": datetime.utcnow().isoformat()
    })

# -------------------------
# Health Check
# -------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "7.9e"}

# -------------------------
# Startup Event (DB Meta Table)
# -------------------------
@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """))
    print("[SYSTEM] ✅ EURO_GOALS v7.9e started successfully.")

# ==========================================================
# ALERTS ENDPOINTS (Smart Money / Asian Reader / Notifications)
# ==========================================================
from datetime import datetime

# Προσωρινή λίστα ειδοποιήσεων (στη μνήμη)
alerts = []

@app.post("/api/add_alert")
async def add_alert(request: Request):
    """
    Δέχεται νέα ειδοποίηση (π.χ. Smart Money Detected)
    από modules όπως asian_reader ή betfair_reader.
    """
    try:
        data = await request.json()
        alert_msg = data.get("message", "")
        source = data.get("source", "System")

        if alert_msg:
            alert_entry = {
                "message": alert_msg,
                "source": source,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            alerts.append(alert_entry)
            print(f"[ALERT] ✅ Added new alert: {alert_msg}")
            return {"status": "ok", "alert": alert_entry, "total": len(alerts)}
        else:
            return {"status": "error", "message": "No alert message provided."}

    except Exception as e:
        print(f"[ALERT] ❌ Error adding alert: {e}")
        return {"status": "error", "details": str(e)}

@app.get("/alerts")
async def get_alerts():
    """
    Επιστρέφει όλες τις ειδοποιήσεις (Alert History)
    για εμφάνιση στο Alert Center του UI.
    """
    try:
        print(f"[ALERT] 🗂 Returning {len(alerts)} alerts.")
        return {"alerts": alerts}
    except Exception as e:
        print(f"[ALERT] ❌ Error reading alerts: {e}")
        return {"alerts": [], "error": str(e)}

@app.delete("/api/clear_alerts")
async def clear_alerts():
    """
    Διαγράφει όλες τις ειδοποιήσεις (reset).
    Μπορεί να καλείται από το κουμπί 'Clear' του Alert Center.
    """
    try:
        count = len(alerts)
        alerts.clear()
        print(f"[ALERT] 🧹 Cleared {count} alerts.")
        return {"status": "ok", "cleared": count}
    except Exception as e:
        print(f"[ALERT] ❌ Error clearing alerts: {e}")
        return {"status": "error", "details": str(e)}
