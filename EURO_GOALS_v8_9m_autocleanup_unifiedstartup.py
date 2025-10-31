# ==============================================
# EURO_GOALS v8.9m – Auto Cleanup + Unified Startup
# ==============================================
# FastAPI app με ενοποιημένη εκκίνηση modules και αυτόματο cleanup.
# Συμβατό με Render. Περιλαμβάνει health/status endpoints & log tail.
#
# .env (ενδεικτικά):
#   DATABASE_URL=sqlite:///matches.db
#   EG_PRUNE_ALERTS_DAYS=60
#   EG_ENABLE_HEALTH=1
#   EG_ENABLE_SMARTMONEY=1
#   EG_ENABLE_GOALMATRIX=1
#   EG_ENABLE_RENDERMONITOR=1
#   EG_LOG_LEVEL=INFO
#   RENDER=1
#   PORT=8000
# ==============================================

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
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

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

for p in [DATA_DIR, LOG_DIR, TMP_DIR, BACKUP_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1) Logging (console + rotating file)
# --------------------------------------------------
LOG_LEVEL = os.getenv("EG_LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("EURO_GOALS")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Console
_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s"))
logger.addHandler(_console)

# File (rotating)
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
# 2) DB Engine
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def _sqlite_connect_args(url: str):
    return {"check_same_thread": False} if "sqlite" in url else {}

engine: Engine = create_engine(DATABASE_URL, connect_args=_sqlite_connect_args(DATABASE_URL))

# Απλή δομή πίνακα alerts (αν δεν υπάρχει) για pruning demo:
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
    """Καθαρισμός SQLite WAL/SHM όταν η DB είναι κλειστή."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    # Τοπικό path SQLite:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    wal = f"{db_path}-wal"
    shm = f"{db_path}-shm"
    for f in [wal, shm]:
        try:
            if os.path.exists(f):
                os.remove(f)
                logger.info("Removed SQLite sidecar: %s", f)
        except Exception as e:
            logger.warning("Could not remove %s: %s", f, e)

def prune_alerts(days: int):
    """Διαγραφή παλαιών alerts > days."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with engine.begin() as conn:
            if "sqlite" in DATABASE_URL:
                conn.execute(
                    text("DELETE FROM alerts WHERE datetime(created_at) < :cutoff"),
                    {"cutoff": cutoff.strftime("%Y-%m-%d %H:%M:%S")}
                )
            else:
                conn.execute(
                    text("DELETE FROM alerts WHERE created_at < :cutoff"),
                    {"cutoff": cutoff}
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
            except Exception as e:
                logger.debug("Skip remove %s (%s)", f, e)
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
# 4) Unified Startup – modules (threads)
# --------------------------------------------------
ENABLE_HEALTH = os.getenv("EG_ENABLE_HEALTH", "1") == "1"
ENABLE_SMARTMONEY = os.getenv("EG_ENABLE_SMARTMONEY", "1") == "1"
ENABLE_GOALMATRIX = os.getenv("EG_ENABLE_GOALMATRIX", "1") == "1"
ENABLE_RENDERMONITOR = os.getenv("EG_ENABLE_RENDERMONITOR", "1") == "1"

_threads: List[threading.Thread] = []
_stop_event = threading.Event()

def _thread_wrap(name: str, target, *args, **kwargs):
    """Τυλιχτικό για ασφαλή εκτέλεση background worker."""
    def runner():
        logger.info("[%s] thread started", name)
        _write_startup_line(f"{name}: started")
        try:
            target(*args, **kwargs)
        except Exception as e:
            logger.exception("[%s] crashed: %s", name, e)
        finally:
            logger.info("[%s] thread exited", name)
    th = threading.Thread(target=runner, daemon=True, name=name)
    _threads.append(th)
    th.start()

# ---- Workers (placeholders που μπορείς να αντικαταστήσεις με πραγματική λογική) ----
def worker_health():
    # π.χ. metrics συλλογή/επιτήρηση πόρων
    while not _stop_event.is_set():
        time.sleep(15)

def worker_smart_money():
    # π.χ. polling APIs (Pinnacle/SBO/188BET) και καταγραφή μεταβολών
    while not _stop_event.is_set():
        # demo: γράψε heartbeat στο log κάθε 30s
        logger.debug("[SmartMoney] heartbeat")
        time.sleep(30)

def worker_goal_matrix():
    # π.χ. επεξεργασία live feeds -> goal probability matrix
    while not _stop_event.is_set():
        time.sleep(20)

def worker_render_monitor():
    # π.χ. auto-refresh Render service μέσω API (εφόσον υπάρχουν κλειδιά)
    while not _stop_event.is_set():
        time.sleep(60)

def unified_startup():
    logger.info("UNIFIED STARTUP begin")
    _write_startup_line("UNIFIED STARTUP: begin")
    ensure_schema()
    auto_cleanup(run_prune=True)

    if ENABLE_HEALTH:
        _thread_wrap("HealthMonitor", worker_health)
    if ENABLE_SMARTMONEY:
        _thread_wrap("SmartMoney", worker_smart_money)
    if ENABLE_GOALMATRIX:
        _thread_wrap("GoalMatrix", worker_goal_matrix)
    if ENABLE_RENDERMONITOR:
        _thread_wrap("RenderMonitor", worker_render_monitor)

    _write_startup_line("UNIFIED STARTUP: modules started")
    logger.info("UNIFIED STARTUP completed")

def unified_shutdown():
    logger.info("UNIFIED SHUTDOWN begin")
    _write_startup_line("UNIFIED SHUTDOWN: begin")
    _stop_event.set()
    # δώσε λίγο χρόνο για να τερματίσουν ομαλά
    for th in _threads:
        th.join(timeout=2.0)
    _write_startup_line("UNIFIED SHUTDOWN: complete")
    logger.info("UNIFIED SHUTDOWN completed")

# --------------------------------------------------
# 5) FastAPI app & templates
# --------------------------------------------------
app = FastAPI(title="EURO_GOALS v8.9m", version="8.9m")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None

@app.on_event("startup")
def on_startup():
    logger.info("🚀 EURO_GOALS v8.9m starting up…")
    _write_startup_line("APP STARTUP")
    unified_startup()

@app.on_event("shutdown")
def on_shutdown():
    unified_shutdown()
    logger.info("👋 Shutdown complete")

# --------------------------------------------------
# 6) Models / DTOs
# --------------------------------------------------
class StatusDTO(BaseModel):
    version: str
    time: str
    modules: dict
    database_url: str

# --------------------------------------------------
# 7) Routes
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Αν υπάρχει template index.html, χρησιμοποίησέ το, αλλιώς μίνι fallback HTML
    if templates and (TEMPLATES_DIR / "index.html").exists():
        return templates.TemplateResponse("index.html", {"request": request, "version": "8.9m"})
    html = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>EURO_GOALS v8.9m</title>
        <style>
          body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 24px; }}
          .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
          .ok {{ color: #1a7f37; }}
          .muted {{ color: #666; }}
          code {{ background:#f6f8fa; padding:2px 6px; border-radius:6px; }}
        </style>
      </head>
      <body>
        <h1>EURO_GOALS <small class="muted">v8.9m</small></h1>
        <div class="card">
          <h3>Unified Startup</h3>
          <p>Τα modules έχουν εκκινηθεί ως background threads. Έλεγξε το <code>/status</code> και το <code>/logs/tail</code>.</p>
        </div>
        <div class="card">
          <h3>Auto Cleanup</h3>
          <p>Το αυτόματο cleanup εκτελέστηκε στο startup. Μπορείς να το καλέσεις χειροκίνητα: <code>/cleanup/run</code></p>
        </div>
        <div class="card">
          <ul>
            <li><a href="/health">/health</a> &nbsp;|&nbsp; <a href="/.well-known/healthz">/.well-known/healthz</a></li>
            <li><a href="/status">/status</a></li>
            <li><a href="/logs/tail">/logs/tail</a></li>
          </ul>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/health", response_class=JSONResponse)
def health():
    return {"status": "ok", "service": "EURO_GOALS", "version": "8.9m", "time": datetime.utcnow().isoformat()}

# Render-compatible health endpoint
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
    """Επιστρέφει τα τελευταία N lines από το main log + startup log (συγχωνευμένα)."""
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

# --------------------------------------------------
# 8) Local dev entry (προαιρετικό)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
