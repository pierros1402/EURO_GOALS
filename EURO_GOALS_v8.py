# ==============================================
# EURO_GOALS v8 – FastAPI Backend (SmartMoney + LiveFeeds Auto)
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
import threading
import time

# ------------------------------------------------
# External Modules
# ------------------------------------------------
from src.smart_money_refiner import detect_smart_money
from src.live_feeds_alerts import detect_live_alerts

# ------------------------------------------------
# App Initialization
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
# Utility: Insert Alert Directly to DB
# ------------------------------------------------
def add_alert_direct(message: str, source="System", level="info"):
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alerts (message, source, level, timestamp)
                VALUES (:m, :s, :l, :t)
            """), {"m": message, "s": source, "l": level, "t": datetime.utcnow().isoformat()})
        print(f"[ALERT] 🔔 {source}: {message}")
    except Exception as e:
        print(f"[ALERT] ❌ Failed to insert alert: {e}")

# ------------------------------------------------
# Auto Monitor Thread (Live Feeds & SmartMoney)
# ------------------------------------------------
def auto_monitor():
    """
    Εκτελεί ανά 60s έλεγχο Smart Money και Live Feeds.
    """
    while True:
        try:
            print("\n[MONITOR] 🔄 Checking Smart Money & Live Feeds...")
            sm = detect_smart_money()
            lf = detect_live_alerts()

            # Smart Money alerts
            for a in sm.get("alerts", []):
                add_alert_direct(a["message"], source="SmartMoney", level="warning")

            # Live Feed alerts
            for b in lf.get("alerts", []):
                lvl = (
                    "success" if b["type"] == "goal" else
                    "danger" if b["type"] == "card" else
                    "info"
                )
                add_alert_direct(b["message"], source="LiveFeed", level=lvl)

            print("[MONITOR] ✅ Cycle complete.")
        except Exception as e:
            print(f"[MONITOR] ❌ Error in monitor loop: {e}")
            add_alert_direct(f"Monitor error: {e}", "System", "danger")

        time.sleep(60)  # επανάληψη κάθε 60s

# ------------------------------------------------
# Startup Event
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
            );
        """))
        conn.commit()

    print("[SYSTEM] ✅ EURO_GOALS v8 started and DB initialized.")

    # Ξεκινά το monitoring thread
    t = threading.Thread(target=auto_monitor, daemon=True)
    t.start()
    print("[SYSTEM] 🧠 Background Monitor thread started (SmartMoney + LiveFeeds).")

# ------------------------------------------------
# Root Page
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------------------------------------
# Health Check
# ------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "8.0"}

# ------------------------------------------------
# Manual SmartMoney Trigger
# ------------------------------------------------
@app.get("/api/test_smartmoney")
async def test_smartmoney():
    try:
        result = detect_smart_money()
        count = result.get("count", 0)
        for a in result.get("alerts", []):
            add_alert_direct(a["message"], "SmartMoney", "warning")
        return {"status": "ok", "detected": count, "alerts": result.get("alerts", [])}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Manual Live Feed Trigger
# ------------------------------------------------
@app.get("/api/test_livefeeds")
async def test_livefeeds():
    try:
        result = detect_live_alerts()
        count = result.get("count", 0)
        for a in result.get("alerts", []):
            lvl = "success" if a["type"] == "goal" else "danger" if a["type"] == "card" else "info"
            add_alert_direct(a["message"], "LiveFeed", lvl)
        return {"status": "ok", "detected": count}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Alerts API
# ------------------------------------------------
@app.get("/api/alerts")
async def get_alerts():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM alerts ORDER BY id DESC"))
        data = [dict(row._mapping) for row in res.fetchall()]
    return {"alerts": data, "total": len(data)}

@app.get("/api/clear_alerts")
async def clear_alerts():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM alerts"))
    return {"status": "ok", "cleared": True}

# ------------------------------------------------
# Alert History Page
# ------------------------------------------------
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})
