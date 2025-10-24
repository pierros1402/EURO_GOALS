# ==============================================
# EURO_GOALS v8 – Backend with Persistent Alerts + Test Endpoint
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
# Import external modules (Live Feeds)
# ------------------------------------------------
from sofascore_reader import get_live_matches
from flashscore_reader import get_flashscore_odds

# ------------------------------------------------
# FastAPI App Initialization
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
# Database Connection
# ------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ------------------------------------------------
# Root Page
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
# Notification Payload Schema
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
    return JSONResponse({
        "ok": True,
        "data": payload.dict(),
        "ts": datetime.utcnow().isoformat()
    })

# ------------------------------------------------
# Health Check
# ------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "8.0"}

# ------------------------------------------------
# Startup Event – Create Tables
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                source TEXT,
                timestamp TEXT,
                level TEXT DEFAULT 'info'
            );
        """))
        conn.commit()
    print("[SYSTEM] ✅ EURO_GOALS v8 started successfully and DB initialized.")

# ------------------------------------------------
# ALERT ENDPOINTS – Persistent Storage
# ------------------------------------------------
@app.post("/api/add_alert")
async def add_alert(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "")
        src = data.get("source", "System")
        lvl = data.get("level", "info")

        if not msg:
            return {"status": "error", "message": "Empty alert message."}

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alerts (message, source, timestamp, level)
                VALUES (:m, :s, :t, :l)
            """), {"m": msg, "s": src, "t": ts, "l": lvl})

        print(f"[ALERT] ✅ {lvl.upper()} | {src} → {msg}")
        return {"status": "ok", "message": msg, "source": src, "time": ts}

    except Exception as e:
        print(f"[ALERT] ❌ Error adding alert: {e}")
        return {"status": "error", "details": str(e)}

@app.get("/alerts")
async def get_alerts():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM alerts ORDER BY id DESC"))
            data = [dict(row._mapping) for row in result]
        return {"alerts": data, "total": len(data)}
    except Exception as e:
        print(f"[ALERT] ❌ Error reading alerts: {e}")
        return {"alerts": [], "error": str(e)}

@app.delete("/api/clear_alerts")
async def clear_alerts():
    try:
        with engine.begin() as conn:
            count = conn.execute(text("DELETE FROM alerts"))
        print("[ALERT] 🧹 Alerts table cleared.")
        return {"status": "ok", "cleared": count.rowcount}
    except Exception as e:
        print(f"[ALERT] ❌ Error clearing alerts: {e}")
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# SIMPLE TEST ALERT ENDPOINT (One-click alert)
# ------------------------------------------------
@app.get("/api/test_alert")
async def test_alert():
    """
    Δημιουργεί μια δοκιμαστική ειδοποίηση στη βάση χωρίς Postman.
    """
    try:
        msg = "Test Alert Triggered via Browser"
        src = "Manual"
        lvl = "info"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alerts (message, source, timestamp, level)
                VALUES (:m, :s, :t, :l)
            """), {"m": msg, "s": src, "t": ts, "l": lvl})

        print(f"[ALERT] 🧪 Test alert inserted: {msg}")
        return {"status": "ok", "message": msg, "time": ts}

    except Exception as e:
        print(f"[ALERT] ❌ Error inserting test alert: {e}")
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# ALERT HISTORY PAGE
# ------------------------------------------------
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

# ------------------------------------------------
# LIVE ODDS ENDPOINT (Sofascore + Flashscore)
# ------------------------------------------------
@app.get("/api/live_odds")
async def live_odds():
    try:
        sofascore_data = get_live_matches()
        flashscore_data = get_flashscore_odds()

        if not sofascore_data and not flashscore_data:
            return [{"league": "No live data", "home": "-", "away": "-", "odds": "-"}]

        combined = []
        for s in sofascore_data:
            for f in flashscore_data:
                if s["home"].split("(")[0].strip() in f["home"] or s["away"].split("(")[0].strip() in f["away"]:
                    match = {
                        "league": s["league"],
                        "home": s["home"],
                        "away": s["away"],
                        "odds": f.get("odds", "-"),
                        "status": s.get("status", ""),
                        "minute": s.get("minute", "-")
                    }
                    combined.append(match)

        if not combined:
            combined = sofascore_data

        print(f"[LIVE] ✅ {len(combined)} combined live matches.")
        return combined

    except Exception as e:
        print(f"[LIVE] ❌ Error combining live feeds: {e}")
        return [{"league": "Error loading live feed", "home": "-", "away": "-", "odds": "-"}]
