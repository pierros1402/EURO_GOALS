# =========================================================
# EURO_GOALS v7.9 – Filterable Alert History (FINAL)
# =========================================================
# Περιλαμβάνει: Home, Live Feed, Alert History, API
# Συμβατό με SQLite & PostgreSQL
# =========================================================

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv
import os

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Database setup (PostgreSQL ή SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ---------------------------------------------------------
# STATIC FILES (CSS / JS)
# ---------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------
# DATABASE STRUCTURE (AUTO CREATE ALERTS TABLE)
# ---------------------------------------------------------
create_table_sql = """
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TEXT,
    type TEXT,
    message TEXT,
    league TEXT,
    match_id TEXT
);
"""
# Για SQLite fallback (όταν δεν χρησιμοποιείται PostgreSQL)
if "sqlite" in DATABASE_URL:
    create_table_sql = create_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

with engine.begin() as conn:
    conn.execute(text(create_table_sql))

# ---------------------------------------------------------
# LOG ALERT FUNCTION
# ---------------------------------------------------------
def log_alert(alert_type, message, league=None, match_id=None):
    """Αποθηκεύει νέα ειδοποίηση στο ιστορικό."""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alerts (timestamp, type, message, league, match_id)
                VALUES (:timestamp, :type, :message, :league, :match_id)
            """), {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": alert_type,
                "message": message,
                "league": league or "",
                "match_id": match_id or ""
            })
        print(f"[ALERT LOGGED] {alert_type} - {message}")
    except Exception as e:
        print("[ALERT LOG ERROR]", e)

# ---------------------------------------------------------
# MAIN ROUTE (HOME)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------------------------------------------------
# LIVE FEED PAGE
# ---------------------------------------------------------
@app.get("/live", response_class=HTMLResponse)
def live_feed(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})

# ---------------------------------------------------------
# ALERT HISTORY PAGE
# ---------------------------------------------------------
@app.get("/alerts", response_class=HTMLResponse)
def show_alerts(request: Request):
    """Επιστρέφει το HTML για το ιστορικό ειδοποιήσεων."""
    return templates.TemplateResponse("alert_history.html", {"request": request})

# ---------------------------------------------------------
# ALERT HISTORY API (FILTERABLE)
# ---------------------------------------------------------
@app.get("/api/alerts")
def get_alerts(
    type: str = Query(None),
    league: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    """Επιστρέφει λίστα ειδοποιήσεων με φίλτρα (JSON)."""
    query = "SELECT * FROM alerts WHERE 1=1"
    params = {}

    if type:
        query += " AND type = :type"
        params["type"] = type
    if league:
        query += " AND league = :league"
        params["league"] = league
    if date_from:
        query += " AND timestamp >= :date_from"
        params["date_from"] = date_from
    if date_to:
        query += " AND timestamp <= :date_to"
        params["date_to"] = date_to

    query += " ORDER BY timestamp DESC LIMIT 300"

    try:
        with engine.connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return JSONResponse([dict(row._mapping) for row in rows])
    except Exception as e:
        print("[ERROR] Fetching alerts:", e)
        return JSONResponse({"error": str(e)})

# ---------------------------------------------------------
# TEST ALERT ROUTE (FOR DEBUG)
# ---------------------------------------------------------
@app.get("/api/test_alert")
def test_alert():
    """Δοκιμαστική εγγραφή ειδοποίησης."""
    log_alert("SmartMoney", "⚡ Απότομη πτώση αποδόσεων στο Over 2.5", "Premier League", "12345")
    return {"status": "ok", "message": "Test alert logged"}

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ---------------------------------------------------------
# STARTUP MESSAGE
# ---------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("===============================================")
    print("   EURO_GOALS v7.9 – Filterable Alert History  ")
    print("===============================================")
    print(f"Database: {DATABASE_URL}")
    print("[✅] System initialized successfully.")
    print("Visit: /alerts for alert history view")
