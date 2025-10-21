# ==========================================================
# EURO_GOALS_v6f_debug.py – Render + Smart Money + Auto Alerts + Dashboard
# ==========================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Εσωτερικά modules
from asian_reader import get_smart_money_data
from auto_mode import get_alerts
from keep_alive import keep_alive
from market_reader import get_market_data  # Προσθήκη για unified dashboard

print("🚀 EURO_GOALS v6f (Unified Dashboard Edition) starting...")

# -----------------------------------------
# FastAPI app setup
# -----------------------------------------
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# -----------------------------------------
# Root route (UI)
# -----------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------------------
# Healthcheck
# -----------------------------------------
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "EURO_GOALS online ✅"}


# -----------------------------------------
# Smart Money route – με επιλογή λίγκας
# -----------------------------------------
@app.get("/smart_money")
def smart_money(league: str = "epl"):
    """
    Επιστρέφει live odds για τη συγκεκριμένη λίγκα.
    Παράδειγμα: /smart_money?league=greece
    """
    data = get_smart_money_data(league)
    return JSONResponse({
        "status": "ok",
        "league": league,
        "last_update": data.get("last_update"),
        "results": data.get("results", [])
    })


# -----------------------------------------
# Smart Money Alerts route (Auto Mode)
# -----------------------------------------
@app.get("/alerts")
def alerts():
    """
    Επιστρέφει τα Smart Money Alerts από το Auto Mode engine.
    """
    data = get_alerts()
    return {
        "status": "ok",
        "last_update": data.get("last_update"),
        "alerts": data.get("alerts", [])
    }


# -----------------------------------------
# Unified Dashboard Data route
# -----------------------------------------
@app.get("/dashboard_data")
def dashboard_data():
    """
    Ενοποιημένο JSON με όλα τα δεδομένα για το UI
    """
    smart_data = get_smart_money_data()
    market_data = get_market_data()
    alerts_data = get_alerts()

    return JSONResponse({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_league": smart_data.get("current_league"),
        "smart_money": smart_data.get("results", []),
        "market_reader": market_data.get("markets", []),
        "alerts": alerts_data.get("alerts", [])
    })


# -----------------------------------------
# Keep Alive
# -----------------------------------------
keep_alive()

print("🌍 EURO_GOALS_v6f Debug server ready (Render Edition)")
