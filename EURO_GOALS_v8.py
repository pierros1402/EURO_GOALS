# ==============================================
# EURO_GOALS v8 – FastAPI Backend
# ==============================================
# Περιλαμβάνει:
#  - Notifications (manual + automatic)
#  - Smart Money integration
#  - Alert Center
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

# ------------------------------------------------
# Εξωτερικά Modules
# ------------------------------------------------
from src.smart_money_refiner import detect_smart_money  # ✅ Νέο import

# ------------------------------------------------
# Εφαρμογή & Templates
# ------------------------------------------------
app = FastAPI(title="EURO_GOALS v8")
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

# ------------------------------------------------
# Database
# ------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ------------------------------------------------
# Startup – Create tables
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                source TEXT,
                level TEXT,
                timestamp TEXT
            )
        """))
        conn.commit()
    print("[SYSTEM] ✅ EURO_GOALS v8 started successfully and DB initialized.")

# ------------------------------------------------
# Root page
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------------------------------------
# Service Worker
# ------------------------------------------------
@app.get("/service-worker.js")
async def service_worker():
    path = os.path.join("static", "js", "service-worker.js")
    if not os.path.exists(path):
        return PlainTextResponse("// service-worker missing", media_type="application/javascript")
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    return FileResponse(path, media_type="application/javascript", headers=headers)

# ------------------------------------------------
# Health check
# ------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "8.0"}

# ------------------------------------------------
# Εσωτερική συνάρτηση για απευθείας εισαγωγή ειδοποίησης
# ------------------------------------------------
def add_alert_direct(message: str, source="System", level="info"):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO alerts (message, source, level, timestamp) VALUES (:m, :s, :l, :t)"),
                {"m": message, "s": source, "l": level, "t": datetime.utcnow().isoformat()}
            )
            conn.commit()
        print(f"[ALERT] 🔔 Direct insert → {message}")
    except Exception as e:
        print(f"[ALERT] ❌ Failed to insert alert: {e}")

# ------------------------------------------------
# Notification endpoint
# ------------------------------------------------
class NotifyPayload(BaseModel):
    title: str
    body: str | None = None
    icon: str | None = None
    url: str | None = None
    tag: str | None = None
    sound: bool | None = True

@app.post("/notify")
async def notify(payload: NotifyPayload):
    add_alert_direct(payload.title, source="Manual", level="info")
    return JSONResponse({
        "ok": True,
        "data": payload.dict(),
        "ts": datetime.utcnow().isoformat()
    })

# ------------------------------------------------
# SMART MONEY ENDPOINT
# ------------------------------------------------
@app.get("/api/test_smartmoney")
async def test_smartmoney():
    """
    Εκτελεί το Smart Money Refiner και αποθηκεύει τα alerts στη βάση.
    Μπορεί να κληθεί απευθείας από browser.
    """
    try:
        result = detect_smart_money()
        count = result.get("count", 0)
        alerts = result.get("alerts", [])
        for a in alerts:
            add_alert_direct(a["message"], source=a["source"], level="warning")
        print(f"[SMART MONEY] ✅ Triggered manually via /api/test_smartmoney ({count} signals)")
        return {"status": "ok", "detected": count, "alerts": alerts}
    except Exception as e:
        print(f"[SMART MONEY] ❌ Error triggering Smart Money: {e}")
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Alerts API
# ------------------------------------------------
@app.get("/api/alerts")
async def get_alerts():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM alerts ORDER BY id DESC"))
        alerts = [
            dict(row._mapping)
            for row in res.fetchall()
        ]
    return {"alerts": alerts, "total": len(alerts)}

# ------------------------------------------------
# Clear Alerts
# ------------------------------------------------
@app.get("/api/clear_alerts")
async def clear_alerts():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alerts"))
        conn.commit()
    return {"status": "ok", "cleared": True}

# ------------------------------------------------
# Alert History Page
# ------------------------------------------------
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

