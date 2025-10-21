# ==============================================
# EURO_GOALS v7 – Main Backend (Auto Live Mode)
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import threading
import time
from dotenv import load_dotenv

# ----------------------------------------------
# Εισαγωγή modules
# ----------------------------------------------
import live_feeds
import flashscore_reader
import asian_reader
import backup_manager

# ----------------------------------------------
# Φόρτωση .env και βάση
# ----------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# FastAPI App
# ----------------------------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ----------------------------------------------
# Homepage
# ----------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": "v7"})

# ----------------------------------------------
# API: Live Scores (Συνδυάζει Sofascore + Flashscore)
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
# Web Page: Live Matches UI
# ----------------------------------------------
@app.get("/live", response_class=HTMLResponse)
def live_page(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})

# ----------------------------------------------
# Background Threads για Live Modules
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

def start_backup_manager():
    print("[THREAD] 💾 Backup manager active (monthly check)")
    backup_manager.check_auto_backup()

# ----------------------------------------------
# Εκκίνηση όλων των background services
# ----------------------------------------------
@app.on_event("startup")
def startup_event():
    print("\n==============================================")
    print("🚀 EURO_GOALS v7 STARTING (Auto Live Mode)")
    print("==============================================")

    # Threads για παράλληλη λειτουργία
    threading.Thread(target=start_sofascore_feed, daemon=True).start()
    threading.Thread(target=start_flashscore_feed, daemon=True).start()
    threading.Thread(target=start_backup_manager, daemon=True).start()

    print("[SYSTEM] ✅ All background threads launched!")

# ----------------------------------------------
# Τοπική εκτέλεση
# ----------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
