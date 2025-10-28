# ==============================================
# EURO_GOALS v8.9f – Module & League Badges
# Auto-Fallback + System Status + Live Module Indicators
# ==============================================

import os, time, threading
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

APP_VERSION = "v8.9f"
LANG = os.getenv("EG_LANG", "gr")

DATABASE_URL_ENV = os.getenv("DATABASE_URL", "").strip()
SQLITE_URL_FALLBACK = os.getenv("SQLITE_URL", "sqlite:///matches.db").strip()
PORT = int(os.getenv("PORT", "10000"))
STARTED_AT = datetime.now(timezone.utc)

status_lock = threading.Lock()
runtime_status = {
    "render_online": True,
    "db_in_use": "unknown",
    "last_health_ok_at": None,
    "last_health_error": None,
    "feeds_router_active": True,
    "uptime_seconds": 0,
}

# Ζωντανή κατάσταση modules
modules_state = {
    "Smart Money": True,
    "Flashscore Router": True,
    "Besoccer API": True,
    "Auto-Fallback": True,
    "Live Refresh": True,
    "Premier League": True,
    "La Liga": True,
    "Serie A": True,
}

app = FastAPI(title="EURO_GOALS", version=APP_VERSION)

if not os.path.isdir("static"):
    os.makedirs("static", exist_ok=True)
if not os.path.isdir("templates"):
    os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

engine = None
engine_label = "unknown"


def _test_engine(url: str) -> bool:
    try:
        eng = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def _make_engine(url: str):
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )


def init_db():
    global engine, engine_label
    if DATABASE_URL_ENV and _test_engine(DATABASE_URL_ENV):
        engine = _make_engine(DATABASE_URL_ENV)
        engine_label = "PostgreSQL"
    else:
        if not _test_engine(SQLITE_URL_FALLBACK):
            raise RuntimeError("SQLite fallback failed.")
        engine = _make_engine(SQLITE_URL_FALLBACK)
        engine_label = "SQLite (Fallback)"

    with status_lock:
        runtime_status["db_in_use"] = engine_label

    print(f"[EURO_GOALS][DB] ✅ Χρησιμοποιείται: {engine_label}")


def _health_probe():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with status_lock:
            runtime_status["last_health_ok_at"] = datetime.now(timezone.utc).isoformat()
            runtime_status["last_health_error"] = None
        return True
    except Exception as e:
        with status_lock:
            runtime_status["last_health_error"] = str(e)
        return False


def _background_monitor():
    while True:
        _health_probe()
        with status_lock:
            runtime_status["uptime_seconds"] = int(
                (datetime.now(timezone.utc) - STARTED_AT).total_seconds()
            )
        time.sleep(10)


@app.on_event("startup")
def on_startup():
    print(f"[EURO_GOALS] 🚀 Starting {APP_VERSION} – Module & League Badges")
    print(f"[EURO_GOALS] 🌐 Language: {LANG}")
    init_db()

    t = threading.Thread(target=_background_monitor, daemon=True)
    t.start()
    print("[EURO_GOALS] 🔁 Background monitor active (health + uptime)")


@app.get("/api/status")
def api_status():
    with status_lock:
        resp = {
            "render_online": runtime_status["render_online"],
            "db_in_use": runtime_status["db_in_use"],
            "feeds_router_active": runtime_status["feeds_router_active"],
            "last_health_ok_at": runtime_status["last_health_ok_at"],
            "last_health_error": runtime_status["last_health_error"],
            "uptime_seconds": runtime_status["uptime_seconds"],
            "version": APP_VERSION,
            "modules": modules_state,
        }
    return JSONResponse(resp)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "APP_VERSION": APP_VERSION}
    )
