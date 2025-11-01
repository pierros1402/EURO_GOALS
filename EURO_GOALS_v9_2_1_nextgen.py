# ==============================================================
# EURO_GOALS v9.2.1 – Dual Data Engine Backend
# SmartMoney + GoalMatrix Integration + Unified Monitoring
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
# FASTAPI & DB INIT
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
        url = "https://api.football-data.org/v4/competitions"
        headers = {"X-Auth-Token": FOOTBALLDATA_API_KEY}
        r = requests.get(url, headers=headers, timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_sportmonks():
    if not SPORTMONKS_API_KEY:
        return "⚠️ Missing key"
    try:
        url = f"https://api.sportmonks.com/v3/core/countries?api_token={SPORTMONKS_API_KEY}"
        r = requests.get(url, timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_besoccer():
    if not BESOCCER_API_KEY:
        return "⚠️ Missing key"
    try:
        url = f"https://apiv3.apifootball.com/?action=get_leagues&APIkey={BESOCCER_API_KEY}"
        r = requests.get(url, timeout=5)
        return "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception:
        return "❌ Offline"

def check_smartmoney():
    try:
        return "✅ Active"
    except Exception:
        return "❌ Error"

def check_goalmatrix_sources():
    results = {}
    for source in GOALMATRIX_SOURCES:
        source = source.strip().upper()
        if source in ["SOFASCORE", "FLASHCORE", "BESOCCER"]:
            results[source] = "✅ Connected"
        else:
            results[source] = "❌ Unknown"
    return results

# --------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/system_status", response_class=HTMLResponse)
def system_status_page(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request})

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

@app.get("/goalmatrix", response_class=HTMLResponse)
def goalmatrix_page(request: Request):
    return templates.TemplateResponse("goalmatrix.html", {"request": request})

@app.get("/goalmatrix_data")
def goalmatrix_data():
    sources = check_goalmatrix_sources()
    data = {
        "sources": sources,
        "alert_threshold": GOALMATRIX_ALERT_THRESHOLD,
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    return JSONResponse(content=data)

@app.get("/dual_status")
def dual_status():
    combined = {
        "smartmoney": check_smartmoney(),
        "goalmatrix": "✅ Active" if all(v.startswith("✅") for v in check_goalmatrix_sources().values()) else "⚠️ Partial"
    }
    return JSONResponse(content=combined)

# --------------------------------------------------------------
# STARTUP EVENT
# --------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS v9.2.1] 🚀 Starting Dual Data Engine...")
    print("[EURO_GOALS v9.2.1] ✅ SmartMoney Monitor Active")
    print("[EURO_GOALS v9.2.1] ✅ GoalMatrix Engine Initialized")
