# ============================================================
# EURO_GOALS NextGen v9.0 – API Integration Skeleton
# ============================================================
# - Config: ENV-based (Besoccer, Asian Odds)
# - DB Models: Match, Odds, Alert
# - HTTP Client: requests + retry
# - Workers (threads): SmartMoney, Schedulers
# - REST API: /api/matches, /api/odds, /api/alerts
# - Compatible with Render, keeps v8.9n UI
# ============================================================

import os, sys, time, json, threading, logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from requests.adapters import HTTPAdapter, Retry

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ------------- CONFIG ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

BESOCCER_API_KEY = os.getenv("BESOCCER_API_KEY", "")  # <-- βάλε το κλειδί όταν έρθει
BESOCCER_BASE    = os.getenv("BESOCCER_BASE", "https://apiv3.besoccerapps.com/scripts/api/api.php")

# Asian odds provider(s) – placeholder endpoints/keys
ASIAN_API_KEY    = os.getenv("ASIAN_API_KEY", "")
ASIAN_BASE       = os.getenv("ASIAN_BASE", "https://api.example-asian-odds.com")

ENABLE_SMARTMONEY = os.getenv("EG_ENABLE_SMARTMONEY", "1") == "1"

# ------------- LOGGING --------------------------------------------------------
logger = logging.getLogger("EURO_GOALS_V9")
logger.setLevel(logging.INFO)
_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s"))
logger.addHandler(_console)
_file = RotatingFileHandler(LOG_DIR / "v9.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
_file.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
logger.addHandler(_file)

# ------------- DB -------------------------------------------------------------
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    provider_id = Column(String, index=True)  # external id (e.g., Besoccer match id)
    league = Column(String, index=True)
    home = Column(String, index=True)
    away = Column(String, index=True)
    kickoff_utc = Column(DateTime, index=True)
    status = Column(String, default="scheduled")  # scheduled/live/finished
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    odds = relationship("Odds", back_populates="match", cascade="all, delete-orphan", lazy="selectin")

Index("ix_matches_unique", Match.provider_id, Match.kickoff_utc, unique=False)

class Odds(Base):
    __tablename__ = "odds"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    book = Column(String, index=True)  # Pinnacle/SBO/188
    market = Column(String, index=True)  # e.g., AH -0.5, O/U 2.5
    price = Column(Float)
    line = Column(Float, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)

    match = relationship("Match", back_populates="odds")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    level = Column(String, index=True)  # info/warning/critical
    kind = Column(String, index=True)   # smartmoney/goal/health
    message = Column(Text)
    payload = Column(Text)              # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

def init_db():
    Base.metadata.create_all(engine)

# ------------- HTTP CLIENT (retry) -------------------------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": "EURO_GOALS/v9"})
    return s

http = make_session()

# ------------- PROVIDERS (SKELETONS) -----------------------------------------
def besoccer_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skeleton for Besoccer API.
    Example doc (placeholder): add required params (tz, format, etc.)
    """
    if not BESOCCER_API_KEY:
        raise RuntimeError("Missing BESOCCER_API_KEY")
    full = {**params, "key": BESOCCER_API_KEY, "tz": "UTC", "format": "json", "req": endpoint}
    r = http.get(BESOCCER_BASE, params=full, timeout=12)
    r.raise_for_status()
    return r.json()

def asian_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Generic Asian odds provider skeleton."""
    if not ASIAN_API_KEY:
        raise RuntimeError("Missing ASIAN_API_KEY")
    url = f"{ASIAN_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {ASIAN_API_KEY}"}
    r = http.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

# ------------- INGESTION / BUSINESS LOGIC ------------------------------------
def upsert_match(session, provider_id: str, league: str, home: str, away: str, kickoff: datetime, status: str = "scheduled") -> Match:
    m = session.query(Match).filter_by(provider_id=provider_id).first()
    if not m:
        m = Match(provider_id=provider_id, league=league, home=home, away=away, kickoff_utc=kickoff, status=status)
        session.add(m)
    else:
        m.league, m.home, m.away, m.kickoff_utc, m.status = league, home, away, kickoff, status
        m.updated_at = datetime.utcnow()
    return m

def insert_odds(session, match: Match, book: str, market: str, price: float, line: Optional[float]):
    session.add(Odds(match=match, book=book, market=market, price=price, line=line, ts=datetime.utcnow()))

def create_alert(session, level: str, kind: str, message: str, payload: Dict[str, Any]):
    session.add(Alert(level=level, kind=kind, message=message, payload=json.dumps(payload), created_at=datetime.utcnow()))

# ---- Demo smart money heuristic (placeholder) --------------------------------
def detect_smart_move(prev: float, curr: float, threshold_points: float = 0.12) -> bool:
    """Very naive: flag if drop > 0.12 (e.g., 1.92 -> 1.78)"""
    try:
        return (prev - curr) >= threshold_points
    except Exception:
        return False

# ------------- WORKERS --------------------------------------------------------
_stop = threading.Event()

def worker_fetch_besoccer_recent():
    """Poll skeleton: fetch today's schedule (placeholder mapping)."""
    while not _stop.is_set():
        try:
            if not BESOCCER_API_KEY:
                time.sleep(30); continue
            # Example placeholder call (adjust endpoint/params to real Besoccer docs)
            # data = besoccer_get("matches", {"day": datetime.utcnow().strftime("%Y-%m-%d")})
            data = {"matches":[{"id":"DUMMY123","league":"EPL","home":"Chelsea","away":"Arsenal","kickoff":"2025-11-02T16:30:00Z","status":"scheduled"}]}
            with SessionLocal() as s:
                for row in data.get("matches", []):
                    m = upsert_match(
                        s,
                        provider_id=str(row["id"]),
                        league=row.get("league","UNK"),
                        home=row.get("home","UNK"),
                        away=row.get("away","UNK"),
                        kickoff=datetime.fromisoformat(row["kickoff"].replace("Z","+00:00")),
                        status=row.get("status","scheduled"),
                    )
                s.commit()
            logger.info("[BESOCCER] schedule sync OK")
        except Exception as e:
            logger.warning("[BESOCCER] schedule sync failed: %s", e)
        time.sleep(60)

def worker_fetch_asian_odds():
    """Poll skeleton: fetch odds for saved matches and detect smart money moves."""
    prev_prices: Dict[str, float] = {}
    while not _stop.is_set():
        try:
            if not ASIAN_API_KEY:
                time.sleep(30); continue
            with SessionLocal() as s:
                matches = s.query(Match).filter(Match.kickoff_utc >= datetime.utcnow() - timedelta(hours=6)).all()
                for m in matches:
                    # Placeholder: simulate odds for AH -0.5 from Pinnacle
                    prev = prev_prices.get(m.provider_id, 1.92)
                    curr = round(max(1.5, prev - 0.02), 2)  # simulate drop
                    insert_odds(s, m, book="Pinnacle", market="AH -0.5", price=curr, line=-0.5)
                    if detect_smart_move(prev, curr):
                        create_alert(
                            s, "critical", "smartmoney",
                            f"Smart Money: {m.home} vs {m.away} ({prev} → {curr})",
                            {"match_id": m.provider_id, "market": "AH -0.5", "book":"Pinnacle", "prev": prev, "curr": curr}
                        )
                    prev_prices[m.provider_id] = curr
                s.commit()
            logger.info("[ASIAN] odds polling OK")
        except Exception as e:
            logger.warning("[ASIAN] odds polling failed: %s", e)
        time.sleep(30)

def start_workers():
    threads = []
    t1 = threading.Thread(target=worker_fetch_besoccer_recent, name="BesoccerSync", daemon=True)
    threads.append(t1); t1.start()
    if ENABLE_SMARTMONEY:
        t2 = threading.Thread(target=worker_fetch_asian_odds, name="AsianOdds", daemon=True)
        threads.append(t2); t2.start()
    return threads

# ------------- FASTAPI --------------------------------------------------------
app = FastAPI(title="EURO_GOALS NextGen v9.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)

@app.on_event("startup")
def on_startup():
    init_db()
    start_workers()
    logger.info("🚀 v9.0 workers started")

@app.on_event("shutdown")
def on_shutdown():
    _stop.set()
    logger.info("👋 v9.0 shutdown")

# ---- API: Matches ------------------------------------------------------------
@app.get("/api/matches")
def api_matches(since: Optional[str] = Query(None), league: Optional[str] = Query(None)):
    try:
        dt_since = datetime.fromisoformat(since) if since else datetime.utcnow() - timedelta(days=2)
    except Exception:
        raise HTTPException(400, "Invalid 'since' (use ISO 8601)")
    with SessionLocal() as s:
        q = s.query(Match).filter(Match.updated_at >= dt_since)
        if league: q = q.filter(Match.league == league)
        rows = q.order_by(Match.kickoff_utc.asc()).all()
        return [{"id": r.id, "provider_id": r.provider_id, "league": r.league, "home": r.home, "away": r.away,
                 "kickoff_utc": r.kickoff_utc.isoformat(), "status": r.status} for r in rows]

# ---- API: Odds ---------------------------------------------------------------
@app.get("/api/odds")
def api_odds(match_id: Optional[int] = Query(None), provider_id: Optional[str] = Query(None), limit: int = 200):
    with SessionLocal() as s:
        q = s.query(Odds).join(Match)
        if match_id: q = q.filter(Odds.match_id == match_id)
        if provider_id: q = q.filter(Match.provider_id == provider_id)
        q = q.order_by(Odds.ts.desc()).limit(max(1, min(limit, 1000)))
        rows = q.all()
        return [{"match_id": r.match_id, "book": r.book, "market": r.market, "price": r.price,
                 "line": r.line, "ts": r.ts.isoformat()} for r in rows]

# ---- API: Alerts -------------------------------------------------------------
@app.get("/api/alerts")
def api_alerts(level: Optional[str] = Query(None), kind: Optional[str] = Query(None), since: Optional[str] = Query(None), limit: int = 200):
    try:
        dt_since = datetime.fromisoformat(since) if since else datetime.utcnow() - timedelta(days=7)
    except Exception:
        raise HTTPException(400, "Invalid 'since'")
    with SessionLocal() as s:
        q = s.query(Alert).filter(Alert.created_at >= dt_since)
        if level: q = q.filter(Alert.level == level)
        if kind: q = q.filter(Alert.kind == kind)
        q = q.order_by(Alert.created_at.desc()).limit(max(1, min(limit, 1000)))
        rows = q.all()
        return [{"id": r.id, "level": r.level, "kind": r.kind, "message": r.message,
                 "payload": json.loads(r.payload or "{}"), "created_at": r.created_at.isoformat()} for r in rows]

# ---- Health ------------------------------------------------------------------
@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/.well-known/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("EURO_GOALS_v9_0_nextgen:app", host="0.0.0.0", port=port)
