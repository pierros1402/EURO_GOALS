# ==============================================
# EURO_GOALS v8.9g – Smart Money Live Sync
# Auto-Fallback + System Status + Smart Money API
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
from asian_reader import detect_smart_money

load_dotenv()

APP_VERSION = "v8.9g"
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
    "smartmoney": {},
}

app = FastAPI(title="EURO_GOALS", version=APP_VERSION)

# --- Static / templates
if not os.path.isdir("static"): os.makedirs("static", exist_ok=True)
if not os.path.isdir("templates"): os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

engine = None
engine_label = "unknown"

# --- DB init / fallback
def _test_engine(url: str) -> bool:
    try:
        eng = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        )
        with eng.connect() as conn: conn.execute(text("SELECT 1"))
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
        engine = _make_engine(SQLITE_URL_FALLBACK)
        engine_label = "SQLite (Fallback)"
    with status_lock:
        runtime_status["db_in_use"] = engine_label
    print(f"[EURO_GOALS][DB] ✅ {engine_label}")

# --- Health / uptime monitor
def _health_probe():
    try:
        with engine.connect() as conn: conn.execute(text("SELECT 1"))
        with status_lock:
            runtime_status["last_health_ok_at"] = datetime.now(timezone.utc).isoformat()
            runtime_status["last_health_error"] = None
        return True
    except Exception as e:
        with status_lock: runtime_status["last_health_error"] = str(e)
        return False

def _background_monitor():
    while True:
        _health_probe()
        with status_lock:
            runtime_status["uptime_seconds"] = int(
                (datetime.now(timezone.utc) - STARTED_AT).total_seconds()
            )
            runtime_status["smartmoney"] = detect_smart_money()
        time.sleep(15)

# --- Startup
@app.on_event("startup")
def on_startup():
    print(f"[EURO_GOALS] 🚀 Starting {APP_VERSION} – Smart Money Live Sync")
    init_db()
    t = threading.Thread(target=_background_monitor, daemon=True)
    t.start()
    print("[EURO_GOALS] 🔁 Monitor active (health + uptime + smartmoney)")

# --- API routes
@app.get("/api/health")
def api_health():
    ok = _health_probe()
    with status_lock:
        payload = {
            "ok": ok,
            "db_in_use": runtime_status["db_in_use"],
            "last_health_ok_at": runtime_status["last_health_ok_at"],
            "error": runtime_status["last_health_error"],
            "version": APP_VERSION,
        }
    return JSONResponse(payload, status_code=200 if ok else 500)

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
            "smartmoney": runtime_status["smartmoney"],
        }
    return JSONResponse(resp)

@app.get("/api/smartmoney_status")
def api_smartmoney_status():
    data = detect_smart_money()
    with status_lock:
        runtime_status["smartmoney"] = data
    return JSONResponse(data)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request, "APP_VERSION": APP_VERSION})
