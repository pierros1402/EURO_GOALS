# ==============================================
# EURO_GOALS v8.9e – System Status Panel (Top UI)
# Auto-Fallback (PostgreSQL -> SQLite), Health, Uptime
# ==============================================

import os
import time
import threading
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

# -------------------------
# 1)  .env & globals
# -------------------------
load_dotenv()

APP_VERSION = "v8.9e"
LANG = os.getenv("EG_LANG", "gr")

DATABASE_URL_ENV = os.getenv("DATABASE_URL", "").strip()
SQLITE_URL_FALLBACK = os.getenv("SQLITE_URL", "sqlite:///matches.db").strip()

PORT = int(os.getenv("PORT", "10000"))  # Render primary port binding
STARTED_AT = datetime.now(timezone.utc)

# Runtime status holders
status_lock = threading.Lock()
runtime_status = {
    "render_online": True,            # αν η εφαρμογή τρέχει, το θεωρούμε True
    "db_in_use": "unknown",
    "last_health_ok_at": None,
    "last_health_error": None,
    "feeds_router_active": True,      # placeholder σημαία για το data router
    "uptime_seconds": 0
}

# -------------------------
# 2)  FastAPI & templates
# -------------------------
app = FastAPI(title="EURO_GOALS", version=APP_VERSION)

# Static & templates (αν δεν υπάρχουν, μην σκάσει)
if not os.path.isdir("static"):
    os.makedirs("static", exist_ok=True)
if not os.path.isdir("static/js"):
    os.makedirs("static/js", exist_ok=True)
if not os.path.isdir("templates"):
    os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------------
# 3)  DB engines (auto-fallback)
# -------------------------
engine = None
engine_label = "unknown"


def _test_engine(url: str) -> bool:
    try:
        eng = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
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
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
    )


def init_db():
    global engine, engine_label
    # 1) προσπάθεια σε PostgreSQL (DATABASE_URL)
    if DATABASE_URL_ENV:
        ok = _test_engine(DATABASE_URL_ENV)
        if ok:
            engine = _make_engine(DATABASE_URL_ENV)
            engine_label = "PostgreSQL"
        else:
            print("[EURO_GOALS][DB] ❌ Αποτυχία σύνδεσης σε PostgreSQL. Θα γίνει fallback σε SQLite.")
    # 2) fallback σε SQLite
    if engine is None:
        if not SQLITE_URL_FALLBACK:
            raise RuntimeError("No valid DB url. Provide DATABASE_URL or SQLITE_URL.")
        ok = _test_engine(SQLITE_URL_FALLBACK)
        if not ok:
            raise RuntimeError("SQLite fallback failed to open.")
        engine = _make_engine(SQLITE_URL_FALLBACK)
        engine_label = "SQLite (Fallback)"

    with status_lock:
        runtime_status["db_in_use"] = engine_label
    print(f"[EURO_GOALS][DB] ✅ Χρησιμοποιείται: {engine_label}")


# ---------------------------------
# 4)  Health check & uptime thread
# ---------------------------------
def _health_probe():
    """
    Εκτελεί ένα ελαφρύ query για να επιβεβαιώσει ζωντανή DB
    και ενημερώνει last_health_ok_at ή last_health_error.
    """
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
    # τρέχει όσο ζει το process: health + uptime
    while True:
        _health_probe()
        with status_lock:
            runtime_status["uptime_seconds"] = int((datetime.now(timezone.utc) - STARTED_AT).total_seconds())
        time.sleep(10)  # κάθε 10s


# -------------------------
# 5)  Startup
# -------------------------
@app.on_event("startup")
def on_startup():
    print(f"[EURO_GOALS] 🚀 Starting {APP_VERSION} – Auto-Fallback + System Status Panel")
    print(f"[EURO_GOALS] 🌐 Language: {LANG}")
    init_db()

    # προαιρετική ελαφριά προετοιμασία για SQLite schema
    try:
        if engine_label.startswith("SQLite"):
            with engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS eg_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """))
                conn.execute(text("""
                INSERT OR IGNORE INTO eg_meta(key, value) VALUES ('created_at', :v)
                """), {"v": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        print("[EURO_GOALS] ⚠️ SQLite init warning:", e)

    # Background monitoring thread
    t = threading.Thread(target=_background_monitor, daemon=True)
    t.start()
    print("[EURO_GOALS] 🔁 Background monitor active (health + uptime)")


# -------------------------
# 6)  Routes (API)
# -------------------------
@app.get("/api/health")
def api_health():
    ok = _health_probe()
    with status_lock:
        payload = {
            "ok": ok,
            "db_in_use": runtime_status["db_in_use"],
            "last_health_ok_at": runtime_status["last_health_ok_at"],
            "error": runtime_status["last_health_error"],
            "version": APP_VERSION
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
        }
    return JSONResponse(resp, status_code=200)


# -------------------------
# 7)  UI routes
# -------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "APP_VERSION": APP_VERSION})


# (προαιρετικό) απλή σελίδα status αν τη ζητήσεις απευθείας
@app.get("/status", response_class=HTMLResponse)
def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request, "APP_VERSION": APP_VERSION})
