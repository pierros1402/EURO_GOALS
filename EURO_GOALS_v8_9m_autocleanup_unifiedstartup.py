# ============================================================
# EURO_GOALS v8.9m – Auto Cleanup + Unified Startup + KeepAlive + Dashboard
# ============================================================
# Ενοποιημένη εφαρμογή FastAPI για EURO_GOALS NextGen:
# - Auto Cleanup (logs/temp/backups)
# - Unified startup modules (Health, SmartMoney, GoalMatrix, RenderMonitor)
# - Keep-Alive system για συνεχή λειτουργία στο Render
# - Web Dashboard με PWA & Notifications
# - Static mount για /static (manifest, service workers, icons, splash)
# ============================================================

import os
import sys
import time
import glob
import shutil
import threading
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# --------------------------------------------------
# KEEP ALIVE MODULE (Render Ping System)
# --------------------------------------------------
import keep_alive  # ping ανά 10' στο Render URL
print("[EURO_GOALS] 🔄 Keep-Alive ενεργό (Render ping κάθε 10’)")

# --------------------------------------------------
# 0) Περιβάλλον & paths
# --------------------------------------------------
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
TMP_DIR = BASE_DIR / "tmp"
BACKUP_DIR = BASE_DIR / "backups"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

for p in [DATA_DIR, LOG_DIR, TMP_DIR, BACKUP_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1) Logging (console + rotating file)
# --------------------------------------------------
LOG_LEVEL = os.getenv("EG_LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("EURO_GOALS")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s"))
logger.addHandler(_console)

log_file = LOG_DIR / "euro_goals.log"
_file = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
_file.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
logger.addHandler(_file)

startup_log = LOG_DIR / "startup_log.txt"
def _write_startup_line(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with startup_log.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

# --------------------------------------------------
# 2) Database setup
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def _sqlite_connect_args(url: str):
    return {"check_same_thread": False} if "sqlite" in url else {}

engine: Engine = create_engine(DATABASE_URL, connect_args=_sqlite_connect_args(DATABASE_URL))

def ensure_schema():
    try:
        with engine.begin() as conn:
            if "sqlite" in DATABASE_URL:
                conn.exec_driver_sql("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    type TEXT,
                    payload TEXT
                );
                """)
    except Exception as e:
        logger.exception("Schema ensure failed: %s", e)

# --------------------------------------------------
# 3) Auto Cleanup
# --------------------------------------------------
PRUNE_ALERTS_DAYS = int(os.getenv("EG_PRUNE_ALERTS_DAYS", "60"))
CLEANUP_PATTERNS = [
    str(LOG_DIR / "*.old"),
    str(TMP_DIR / "*"),
    str(BASE_DIR / "*.tmp"),
    str(BASE_DIR / "*.bak"),
    str(BACKUP_DIR / "*_old*"),
]

def cleanup_sqlite_shm_wal():
    if not DATABASE_URL.startswith("sqlite"):
        return
    db_path = DATABASE_URL.replace("sqlite:///", "")
    for suffix in ("-wal", "-shm"):
        f = db_path + suffix
        if os.path.exists(f):
            try:
                os.remove(f)
                logger.info("Removed SQLite sidecar: %s", f)
            except Exception as e:
                logger.warning("Could not remove %s: %s", f, e)

def prune_alerts(days: int):
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM alerts WHERE datetime(created_at) < :cutoff"),
                {"cutoff": cutoff.strftime("%Y-%m-%d %H:%M:%S")}
            )
        logger.info("Pruned alerts older than %s days", days)
    except Exception as e:
        logger.warning("Prune alerts failed: %s", e)

def delete_patterns(patterns: List[str]):
    removed = 0
    for pat in patterns:
        for f in glob.glob(pat):
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    os.remove(f)
                removed += 1
            except Exception:
                pass
    logger.info("Cleanup removed %d items (patterns=%d)", removed, len(patterns))

def auto_cleanup(run_prune=True):
    logger.info("AUTO-CLEANUP started")
    _write_startup_line("AUTO-CLEANUP: begin")
    cleanup_sqlite_shm_wal()
    delete_patterns(CLEANUP_PATTERNS)
    if run_prune and PRUNE_ALERTS_DAYS > 0:
        prune_alerts(PRUNE_ALERTS_DAYS)
    _write_startup_line("AUTO-CLEANUP: complete")
    logger.info("AUTO-CLEANUP completed")

# --------------------------------------------------
# 4) Unified Startup Modules
# --------------------------------------------------
ENABLE_HEALTH = os.getenv("EG_ENABLE_HEALTH", "1") == "1"
ENABLE_SMARTMONEY = os.getenv("EG_ENABLE_SMARTMONEY", "1") == "1"
ENABLE_GOALMATRIX = os.getenv("EG_ENABLE_GOALMATRIX", "1") == "1"
ENABLE_RENDERMONITOR = os.getenv("EG_ENABLE_RENDERMONITOR", "1") == "1"

_threads: List[threading.Thread] = []
_stop_event = threading.Event()

def _thread_wrap(name: str, target):
    def runner():
        logger.info("[%s] thread started", name)
        _write_startup_line(f"{name}: started")
        try:
            target()
        except Exception as e:
            logger.exception("[%s] crashed: %s", name, e)
    th = threading.Thread(target=runner, daemon=True, name=name)
    _threads.append(th)
    th.start()

def worker_health():
    while not _stop_event.is_set():
        time.sleep(15)

def worker_smartmoney():
    while not _stop_event.is_set():
        logger.debug("[SmartMoney] heartbeat")
        time.sleep(30)

def worker_goalmatrix():
    while not _stop_event.is_set():
        time.sleep(20)

def worker_rendermonitor():
    while not _stop_event.is_set():
        time.sleep(60)

def unified_startup():
    logger.info("UNIFIED STARTUP begin")
    _write_startup_line("UNIFIED STARTUP: begin")
    ensure_schema()
    auto_cleanup(run_prune=True)
    if ENABLE_HEALTH: _thread_wrap("HealthMonitor", worker_health)
    if ENABLE_SMARTMONEY: _thread_wrap("SmartMoney", worker_smartmoney)
    if ENABLE_GOALMATRIX: _thread_wrap("GoalMatrix", worker_goalmatrix)
    if ENABLE_RENDERMONITOR: _thread_wrap("RenderMonitor", worker_rendermonitor)
    _write_startup_line("UNIFIED STARTUP: modules started")
    logger.info("UNIFIED STARTUP completed")

def unified_shutdown():
    logger.info("UNIFIED SHUTDOWN begin")
    _stop_event.set()
    for th in _threads: th.join(timeout=2.0)
    logger.info("UNIFIED SHUTDOWN completed")

# --------------------------------------------------
# 5) FastAPI app + static/templates mount
# --------------------------------------------------
app = FastAPI(title="EURO_GOALS NextGen", version="8.9m")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.on_event("startup")
def on_startup():
    logger.info("🚀 EURO_GOALS NextGen starting up...")
    unified_startup()

@app.on_event("shutdown")
def on_shutdown():
    unified_shutdown()
    logger.info("👋 Shutdown complete")

# --------------------------------------------------
# 6) DTOs
# --------------------------------------------------
class StatusDTO(BaseModel):
    version: str
    time: str
    modules: dict
    database_url: str

# --------------------------------------------------
# 7) Routes (UI + API)
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if (TEMPLATES_DIR / "index.html").exists():
        return templates.TemplateResponse("index.html", {"request": request, "version": "8.9m"})
    return HTMLResponse("<h1>EURO_GOALS NextGen</h1><p>Running on Render</p>")

@app.get("/health", response_class=JSONResponse)
def health():
    # Μικρό summary ώστε το UI να δείχνει κάτι χρήσιμο live
    return {
        "status": "OK",
        "service": "EURO_GOALS",
        "version": "8.9m",
        "time": datetime.utcnow().isoformat(),
        "components": {
            "Database": "OK",
            "SmartMoney": "OK" if ENABLE_SMARTMONEY else "DISABLED",
            "GoalMatrix": "OK" if ENABLE_GOALMATRIX else "DISABLED",
            "RenderMonitor": "OK" if ENABLE_RENDERMONITOR else "DISABLED"
        }
    }

@app.get("/.well-known/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"

@app.get("/status", response_model=StatusDTO)
def status():
    mods = {
        "Health": ENABLE_HEALTH,
        "SmartMoney": ENABLE_SMARTMONEY,
        "GoalMatrix": ENABLE_GOALMATRIX,
        "RenderMonitor": ENABLE_RENDERMONITOR,
    }
    return StatusDTO(
        version="8.9m",
        time=datetime.utcnow().isoformat(),
        modules=mods,
        database_url=DATABASE_URL,
    )

@app.post("/cleanup/run")
def cleanup_run(prune: bool = Query(True, description="Εκτέλεση και pruning alerts")):
    auto_cleanup(run_prune=prune)
    return {"status": "ok", "message": "Cleanup executed", "prune": prune}

@app.get("/logs/tail", response_class=PlainTextResponse)
def logs_tail(lines: int = Query(200, ge=1, le=2000)):
    def tail_file(path: Path, n: int) -> List[str]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()
        return content[-n:]
    a = tail_file(log_file, lines)
    b = tail_file(startup_log, int(lines / 2))
    merged = ["--- euro_goals.log ---\n"] + a + ["\n--- startup_log.txt ---\n"] + b
    return "".join(merged)

# ---- Demo endpoints για UI auto-refresh (μπορείς να τα αντικαταστήσεις με πραγματικά) ----
@app.get("/smartmoney", response_class=JSONResponse)
def smartmoney_feed():
    return {
        "updated": datetime.utcnow().isoformat(),
        "signals": [
            {"league": "EPL", "match": "Chelsea vs Arsenal", "market": "AH -0.5", "odds_move": "1.92 → 1.78", "book": "Pinnacle"},
            {"league": "Serie A", "match": "Milan vs Napoli", "market": "O/U 2.5", "odds_move": "1.95 → 1.80", "book": "SBOBET"}
        ]
    }

@app.get("/goal_matrix", response_class=JSONResponse)
def goal_matrix_feed():
    return {
        "updated": datetime.utcnow().isoformat(),
        "matrix": {
            "BTTS%": {"TeamA": 62, "TeamB": 48},
            "Over2.5%": {"TeamA": 58, "TeamB": 51},
            "SmartMoneyTag": {"TeamA": True, "TeamB": False}
        }
    }

# --------------------------------------------------
# 8) Local dev entry
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("EURO_GOALS_v8_9m_autocleanup_unifiedstartup:app", host="0.0.0.0", port=port)
