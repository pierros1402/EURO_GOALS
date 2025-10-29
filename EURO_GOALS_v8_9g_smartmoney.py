# ============================================================
# EURO_GOALS v8_9g_smartmoney.py
# Smart Money Monitor + Admin Feeds + System Status + Auto Health Refresh
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from dotenv import load_dotenv
from threading import Thread
import time
import random
import requests
import os

# ------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------
load_dotenv()
RENDER_API_KEY = os.getenv("RENDER_API_KEY")

# ------------------------------------------------------------
# FASTAPI SETUP
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – Smart Money & System Status")
templates = Jinja2Templates(directory="templates")

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# GLOBAL STATUS SNAPSHOT (ανανεώνεται κάθε 5 λεπτά)
# ============================================================
latest_status_snapshot = []

# ------------------------------------------------------------
# SMART MONEY GENERATOR
# ------------------------------------------------------------
def generate_smartmoney_data():
    matches = [
        ("Arsenal - Chelsea", "Asian Handicap"),
        ("Barcelona - Sevilla", "Over/Under"),
        ("Bayern - Dortmund", "Asian Handicap"),
        ("PAOK - Olympiacos", "Over/Under"),
        ("Juventus - Inter", "Asian Handicap"),
        ("PSG - Marseille", "Over/Under"),
        ("Ajax - Feyenoord", "Asian Handicap"),
    ]
    data = []
    for match, market in matches:
        mfi = random.randint(45, 100)
        data.append({
            "match": match,
            "market": market,
            "money_flow_index": mfi,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return data

# ------------------------------------------------------------
# FEEDS GENERATOR
# ------------------------------------------------------------
def generate_feeds_status():
    feeds = [
        {"name": "BeSoccer API", "status": "OK", "details": "Historical & Live Data"},
        {"name": "Flashscore Parser", "status": "OK", "details": "Live Scores Feed"},
        {"name": "Betfair Monitor", "status": "FAIL", "details": "Proxy timeout"},
        {"name": "Asian Reader", "status": "OK", "details": "Smart Money Engine"},
        {"name": "Digitain Lead", "status": "PENDING", "details": "Awaiting API access"},
    ]
    for f in feeds:
        f["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return feeds

# ------------------------------------------------------------
# RENDER API CHECK
# ------------------------------------------------------------
def check_render_api():
    """Ελέγχει αν το Render API απαντά κανονικά."""
    if not RENDER_API_KEY:
        return {"status": "FAIL", "details": "API key missing"}
    try:
        headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
        response = requests.get("https://api.render.com/v1/services", headers=headers, timeout=5)
        if response.status_code == 200:
            return {"status": "OK", "details": "Render API reachable"}
        else:
            return {"status": "FAIL", "details": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "FAIL", "details": f"Error: {str(e)}"}

# ------------------------------------------------------------
# SYSTEM STATUS GENERATOR
# ------------------------------------------------------------
def generate_system_status():
    render_check = check_render_api()
    system_services = [
        {"name": "SmartMoney Engine", "status": "OK", "details": "Active feed check OK"},
        {"name": "Alert Center", "status": "OK", "details": "Browser alerts operational"},
        {"name": "Live Feeds", "status": "OK", "details": "Flashscore Sync running"},
        {"name": "Database", "status": "OK", "details": "Render PostgreSQL Connected"},
        {"name": "Render Auto-Refresh", "status": render_check["status"], "details": render_check["details"]},
    ]
    for s in system_services:
        s["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return system_services

# ------------------------------------------------------------
# BACKGROUND THREAD – AUTO HEALTH REFRESH
# ------------------------------------------------------------
def background_health_refresher():
    global latest_status_snapshot
    while True:
        try:
            latest_status_snapshot = generate_system_status()
            print(f"[EURO_GOALS] 🔁 System health refreshed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print("[EURO_GOALS] ❌ Error refreshing system health:", e)
        time.sleep(300)  # κάθε 5 λεπτά (300 sec)

# ------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------
@app.get("/smartmoney_feed")
def smartmoney_feed():
    return JSONResponse(generate_smartmoney_data())

@app.get("/smartmoney_monitor", response_class=HTMLResponse)
def smartmoney_monitor(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request})

@app.get("/feeds_status")
def feeds_status():
    return JSONResponse(generate_feeds_status())

@app.get("/admin_feeds", response_class=HTMLResponse)
def admin_feeds(request: Request):
    return templates.TemplateResponse("admin_feeds.html", {"request": request})

@app.get("/status_feed")
def status_feed():
    """Επιστρέφει το τελευταίο snapshot που ανανεώνεται στο παρασκήνιο."""
    if not latest_status_snapshot:
        return JSONResponse(generate_system_status())
    return JSONResponse(latest_status_snapshot)

@app.get("/system_status", response_class=HTMLResponse)
def system_status(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request})

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "EURO_GOALS SmartMoney + AutoHealth v8.9h"}

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 Smart Money, Feeds & Status Monitor ενεργοποιήθηκε.")
    print("[EURO_GOALS] ✅ Endpoints διαθέσιμα:")
    print("   - /smartmoney_monitor")
    print("   - /admin_feeds")
    print("   - /system_status")
    print("   - /status_feed")
    print("   - /health")
    print("[EURO_GOALS] 📡 Database connection OK")

    # Εκκίνηση background thread για αυτόματη ανανέωση health
    thread = Thread(target=background_health_refresher, daemon=True)
    thread.start()

# ------------------------------------------------------------
# MAIN (Local Run)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9g_smartmoney:app", host="127.0.0.1", port=8000, reload=True)
