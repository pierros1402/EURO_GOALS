from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os, sqlite3, socket, shutil

# =====================================
#  🔹 ΡΥΘΜΙΣΕΙΣ ΚΑΙ ΕΚΚΙΝΗΣΗ
# =====================================
load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Έλεγχος Internet
def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# Επιλογή βάσης
DATABASE_URL = os.getenv("DATABASE_URL")
if not check_internet() or not DATABASE_URL:
    DATABASE_URL = "sqlite:///./matches.db"
    print("💾 Χρήση τοπικής SQLite βάσης")
else:
    print("✅ Σύνδεση με PostgreSQL (Render)")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# =====================================
#  🔹 HTML ROUTE (UI)
# =====================================
@app.get("/", response_class=HTMLResponse)
async def ui_home(request: Request):
    """Φορτώνει το EURO_GOALS UI"""
    return templates.TemplateResponse("index.html", {"request": request})

# =====================================
#  🔹 API ENDPOINTS
# =====================================

# Δημιουργία πίνακα matches αν δεν υπάρχει
@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        create_sqlite = """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            odds TEXT,
            smart_money TEXT
        )
        """

        create_postgres = """
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            date TEXT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            odds TEXT,
            smart_money TEXT
        )
        """

        # Αντιλαμβάνεται ποια βάση χρησιμοποιείται
        if "postgres" in str(engine.url):
            conn.execute(text(create_postgres))
        else:
            conn.execute(text(create_sqlite))
        conn.commit()
# =====================================
#  HEALTH + MATCHES ENDPOINTS (API)
# =====================================

from pydantic import BaseModel
from sqlalchemy import text

@app.get("/api/health")
def api_health():
    return {"status": "ok"}

@app.get("/api/matches")
def api_get_matches():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM matches"))
        data = [dict(row._mapping) for row in result]
    return {"count": len(data), "matches": data}

class Match(BaseModel):
    date: str
    league: str
    home_team: str
    away_team: str
    odds: str | None = None
    smart_money: str | None = None

@app.post("/api/matches")
def api_add_match(match: Match):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO matches (date, league, home_team, away_team, odds, smart_money)
            VALUES (:date, :league, :home_team, :away_team, :odds, :smart_money)
        """), match.dict())
        conn.commit()
    return {"status": "ok", "data": match.dict()}


# =====================================
#  ΕΝΑΡΞΗ ΕΦΑΡΜΟΓΗΣ
# =====================================
# =====================================
#  ΕΞΑΓΩΓΗ ΣΕ EXCEL
# =====================================
from fastapi.responses import FileResponse
import pandas as pd

@app.get("/api/export_excel")
def export_excel():
    """Εξάγει όλους τους αγώνες σε Excel (.xlsx)"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM matches"))
            data = [dict(row._mapping) for row in result]

        if not data:
            return {"error": "Η βάση είναι άδεια"}

        df = pd.DataFrame(data)
        filepath = "matches_export.xlsx"
        df.to_excel(filepath, index=False)
        return FileResponse(filepath, filename="EURO_GOALS_Matches.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

