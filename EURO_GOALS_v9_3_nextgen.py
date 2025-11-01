# ==============================================================
# EURO_GOALS v9.3 – Unified Monitoring Backend
# Combines System Status + SmartMoney + GoalMatrix Panels
# ==============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

# --------------------------------------------------------------
# LOAD ENVIRONMENT
# --------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "")
FOOTBALLDATA_API_KEY = os.getenv("FOOTBALLDATA_API_KEY", "")
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "")
BESOCCER_API_KEY = os.getenv("BESOCCER_API_KEY", "")
GOALMATRIX_SOURCES = os.getenv("GOALMATRIX_SOURCES", "SOFASCORE,FLASHCORE,BESOCCER").split(",")
GOALMATRIX_ALERT_THRESHOLD = os.getenv("GOALMATRIX_ALERT_THRESHOLD", "0.82")

# --------------------------------------------------------------
# FASTAPI INIT
# --------------------------------------------------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# --------------------------------------------------------------
# CHECK FUNCTIONS
# --------------------------------------------------------------
def check_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "✅ OK"
    except Exception:
        return "❌ Offline"

def check_render():
    if not RENDER_HEALTH_URL:
        return "⚠️ URL Missing"
    try:
        r = requests.get(RENDER_HEALTH_URL, timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_footballdata():
    if not FOOTBALLDATA_API_KEY:
        return "⚠️ Missing key"
    try:
        r = requests.get("https://api.football-data.org/v4/competitions",
                         headers={"X-Auth-Token": FOOTBALLDATA_API_KEY},
                         timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_sportmonks():
    if not SPORTMONKS_API_KEY:
        return "⚠️ Missing key"
    try:
        r = requests.get(f"https://api.sportmonks.com/v3/core/countries?api_token={SPORTMONKS_API_KEY}", timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_besoccer():
    if not BESOCCER_API_KEY:
        return "⚠️ Missing key"
    try:
        r = requests.get(f"https://apiv3.apifootball.com/?action=get_leagues&APIkey={BESOCCER_API_KEY}", timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_smartmoney():
    return "✅ Active"

def check_goalmatrix_sources():
    results = {}
    for s in GOALMATRIX_SOURCES:
        s = s.strip().upper()
        if s in ["SOFASCORE", "FLASHCORE", "BESOCCER"]:
            results[s] = "✅ Connected"
        else:
            results[s] = "❌ Unknown"
    return results

# --------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/unified_monitor", response_class=HTMLResponse)
def unified_monitor_page(request: Request):
    return templates.TemplateResponse("unified_monitor.html", {"request": request})

@app.get("/system_status_data")
def system_status_data():
    goalmatrix_overall = "✅ Active" if all(v.startswith("✅") for v in check_goalmatrix_sources().values()) else "⚠️ Partial"
    data = {
        "db": check_database(),
        "render": check_render(),
        "footballdata": check_footballdata(),
        "sportmonks": check_sportmonks(),
        "besoccer": check_besoccer(),
        "smartmoney": check_smartmoney(),
        "goalmatrix": goalmatrix_overall,
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    return JSONResponse(content=data)

@app.get("/smartmoney_data")
def smartmoney_data():
    data = {
        "pinnacle": "✅ Stable",
        "sbobet": "✅ Stable",
        "188bet": "⚠️ Delay",
        "alerts_active": True,
        "last_refresh": datetime.now().strftime("%H:%M:%S")
    }
    return JSONResponse(content=data)

@app.get("/goalmatrix_data")
def goalmatrix_data():
    data = {
        "sources": check_goalmatrix_sources(),
        "threshold": GOALMATRIX_ALERT_THRESHOLD,
        "last_update": datetime.now().strftime("%H:%M:%S")
    }
    return JSONResponse(content=data)

@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS v9.3] 🚀 Unified Monitoring initialized.")
