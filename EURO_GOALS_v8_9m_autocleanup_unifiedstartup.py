# ============================================================
# EURO_GOALS NextGen v8.9n – Unified PWA + AlertCenter + Logs
# ============================================================

import os, sys, time, threading, logging, json
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = BASE_DIR / "templates"
STATIC = BASE_DIR / "static"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logging
logger = logging.getLogger("EURO_GOALS")
logger.setLevel(logging.INFO)
_console = logging.StreamHandler(sys.stdout)
logger.addHandler(_console)
_file = RotatingFileHandler(LOG_DIR / "eurogoals.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
logger.addHandler(_file)

# FastAPI App
app = FastAPI(title="EURO_GOALS NextGen v8.9n")
templates = Jinja2Templates(directory=str(TEMPLATES))
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@app.on_event("startup")
def startup_event():
    logger.info("🚀 EURO_GOALS v8.9n started")
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                message TEXT
            )
        """)
        conn.exec_driver_sql("DELETE FROM alerts WHERE datetime(timestamp) < datetime('now', '-60 days')")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status", response_class=JSONResponse)
def status():
    return {
        "version": "8.9n",
        "time": datetime.utcnow().isoformat(),
        "modules": {
            "Health": True,
            "SmartMoney": True,
            "GoalMatrix": True,
            "RenderMonitor": True,
        }
    }

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/logs/tail", response_class=PlainTextResponse)
def logs_tail(lines: int = Query(150, ge=10, le=1000)):
    log_path = LOG_DIR / "eurogoals.log"
    if not log_path.exists(): return "No logs yet."
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        return "".join(f.readlines()[-lines:])

# --- Demo endpoints ---
@app.get("/smartmoney_demo", response_class=JSONResponse)
def smartmoney_demo():
    return {
        "updated": datetime.utcnow().isoformat(),
        "signals": [
            {"match": "Chelsea - Arsenal", "market": "AH -0.5", "odds": "1.92→1.78", "book": "Pinnacle"},
            {"match": "Milan - Napoli", "market": "O/U 2.5", "odds": "1.95→1.81", "book": "SBOBET"}
        ]
    }

@app.get("/goal_matrix_demo", response_class=JSONResponse)
def goal_matrix_demo():
    return {
        "updated": datetime.utcnow().isoformat(),
        "matrix": {"BTTS%": {"TeamA": 62, "TeamB": 48}, "Over2.5%": {"TeamA": 59, "TeamB": 53}}
    }

@app.get("/alerts_demo", response_class=JSONResponse)
def alerts_demo():
    return {
        "updated": datetime.utcnow().isoformat(),
        "alerts": [
            {"timestamp": "2025-11-01 13:30:00", "level": "info", "message": "System startup completed"},
            {"timestamp": "2025-11-01 13:35:00", "level": "warning", "message": "Asian odds feed delay"},
            {"timestamp": "2025-11-01 13:40:00", "level": "critical", "message": "SmartMoney API unreachable"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("EURO_GOALS_v8_9n_unifiedstartup:app", host="0.0.0.0", port=port)
