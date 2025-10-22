# =========================================================
# EURO_GOALS v7.9c – Alert History + Filters + Excel Export
# =========================================================

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv
import os
import openpyxl

# ---------------------------------------------------------
# ENV / APP
# ---------------------------------------------------------
load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------
# DB TABLE
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
if "sqlite" in DATABASE_URL:
    create_table_sql = create_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

with engine.begin() as conn:
    conn.execute(text(create_table_sql))

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def log_alert(alert_type, message, league=None, match_id=None):
    """Καταγραφή νέου alert."""
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
        print(f"[ALERT LOGGED] {alert_type} – {message}")
    except Exception as e:
        print("[ALERT LOG ERROR]", e)


def fetch_alerts_filtered(alert_type=None, league=None, date_from=None, date_to=None):
    query = "SELECT * FROM alerts WHERE 1=1"
    params = {}
    if alert_type:
        query += " AND type = :type"
        params["type"] = alert_type
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
    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in rows]

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/live", response_class=HTMLResponse)
def live_feed(request: Request):
    return templates.TemplateResponse("live.html", {"request": request})

@app.get("/alerts", response_class=HTMLResponse)
def show_alerts(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/alerts")
def get_alerts(
    type: str = Query(None),
    league: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    try:
        data = fetch_alerts_filtered(type, league, date_from, date_to)
        return JSONResponse(data)
    except Exception as e:
        print("[ERROR] /api/alerts:", e)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/alerts/leagues")
def get_leagues():
    sql = "SELECT DISTINCT league FROM alerts WHERE league IS NOT NULL AND league <> '' ORDER BY league ASC"
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
            leagues = [r[0] for r in rows]
            return {"leagues": leagues}
    except Exception as e:
        print("[ERROR] /api/alerts/leagues:", e)
        return JSONResponse({"error": str(e)}, status_code=500)

# ---------------------------------------------------------
# EXCEL EXPORT
# ---------------------------------------------------------
@app.get("/api/alerts/export")
def export_alerts_to_excel(
    type: str = Query(None),
    league: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    """Εξαγωγή alerts σε αρχείο Excel με τα τρέχοντα φίλτρα."""
    try:
        data = fetch_alerts_filtered(type, league, date_from, date_to)

        filename = f"EURO_GOALS_ALERTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = f"/tmp/{filename}"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Alerts"

        headers = ["Timestamp", "Type", "League", "Message", "Match ID"]
        ws.append(headers)

        for a in data:
            ws.append([a.get("timestamp"), a.get("type"), a.get("league"), a.get("message"), a.get("match_id")])

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column].width = min(max_length + 2, 60)

        wb.save(filepath)
        return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            filename=filename)
    except Exception as e:
        print("[ERROR] Export Excel:", e)
        return JSONResponse({"error": str(e)}, status_code=500)

# ---------------------------------------------------------
# TEST / HEALTH
# ---------------------------------------------------------
@app.get("/api/test_alert")
def test_alert():
    log_alert("SmartMoney", "⚡ Απότομη πτώση αποδόσεων στο Over 2.5", "Premier League", "12345")
    return {"status": "ok", "message": "Test alert logged"}

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.on_event("startup")
def startup_event():
    print("===============================================")
    print("  EURO_GOALS v7.9c – Filters + Excel Export  ")
    print("===============================================")
    print(f"Database: {DATABASE_URL}")
    print("[✅] System initialized successfully.")
