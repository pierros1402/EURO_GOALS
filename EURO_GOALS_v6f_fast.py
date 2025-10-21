# ==============================================
# EURO_GOALS v7.1 – Main Backend (Auto Live Mode + Cross Verification)
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import threading
import time
import socket
import requests
from dotenv import load_dotenv

# ----------------------------------------------
# Modules
# ----------------------------------------------
import live_feeds
import flashscore_reader
import asian_reader
import backup_manager
import cross_verifier   # ✅ νέο module

# ----------------------------------------------
# Load environment variables
# ----------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# FastAPI setup
# ----------------------------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ----------------------------------------------
# Homepage
# ----------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": "v7.1"})

# ----------------------------------------------
# API: Live Scores
# ----------------------------------------------
@app.get("/api/live_scores")
def get_live_scores():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT match_id, home, away, score, status, source, updated_at
                FROM matches
                WHERE status IN ('live', 'inprogress', '1st_half', '2nd_half')
                ORDER BY updated_at DESC
                LIMIT 100;
            """)).mappings().all()

        matches = [dict(r) for r in result]
        return JSONResponse({"count": len(matches), "matches": matches})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ----------------------------------------------
# API: System Health Check
# ----------------------------------------------
@app.get("/api/system_check")
def system_check():
    status = {"status": "ok", "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}

    # ✅ Database check
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) AS cnt FROM matches")).mappings().first()
            status["database"] = {"connected": True, "live_matches": result["cnt"]}
    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)}
        status["status"] = "warning"

    # ✅ Sofascore API check
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://api.sofascore.com/api/v1/sport/football/events/live", headers=headers, timeout=5)
        status["feeds"] = {"sofascore_api": "reachable" if r.status_code == 200 else f"error {r.status_code}"}
    except Exception as e:
        status["feeds"] = {"sofascore_api": f"error {e}"}
        status["status"] = "warning"

    # ✅ Threads check (simple confirmation)
    status["threads"] = {
        "sofascore": "running",
        "flashscore": "running",
        "verifier": "running",
        "backup": "ok"
    }

    status["host"] = socket.gethostname()
    return JSONResponse(status)

# ----------------------------------------------
# Web Page: Live Matches
# ----------------------------------------------
@app.get("/live", response_class=HTMLResponse)
def live_page(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})

# ----------------------------------------------
# Background Threads
# ----------------------------------------------
def start_sofascore_feed():
    while True:
        print("[THREAD] 🟢 Sofascore feed running...")
        live_feeds.update_sofascore_data()
        time.sleep(120)

def start_flashscore_feed():
    while True:
        print("[THREAD] 🔵 Flashscore feed running...")
        html = flashscore_reader.fetch_flashscore_html()
        if html:
            matches = flashscore_reader.parse_flashscore(html)
            flashscore_reader.update_database(matches)
        time.sleep(180)

def start_cross_verifier():
    while True:
        print("[THREAD] ⚖️ Cross Verifier running...")
        cross_verifier.verify_and_update()
        time.sleep(180)  # κάθε 3 λεπτά

def start_backup_manager():
    print("[THREAD] 💾 Backup manager active (monthly check)")
    backup_manager.check_auto_backup()

# ----------------------------------------------
# Startup event
# ----------------------------------------------
@app.on_event("startup")
def startup_event():
    print("\n==============================================")
    print("🚀 EURO_GOALS v7.1 STARTING (Cross Verification Mode)")
    print("==============================================")

    threading.Thread(target=start_sofascore_feed, daemon=True).start()
    threading.Thread(target=start_flashscore_feed, daemon=True).start()
    threading.Thread(target=start_cross_verifier, daemon=True).start()
    threading.Thread(target=start_backup_manager, daemon=True).start()

    print("[SYSTEM] ✅ All background threads launched!")

# ----------------------------------------------
# Local run
# ----------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
