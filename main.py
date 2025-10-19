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
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            odds TEXT,
            smart_money TEXT
        )
        """))
        conn.commit()

# GET: Επιστροφή όλων των αγώνων (ή ανά λίγκα)
@app.get("/api/matches")
def get_matches(league: str = None):
    with engine.connect() as conn:
        if league:
            result = conn.execute(text("SELECT * FROM matches WHERE league = :league"), {"league": league})
        else:
            result = conn.execute(text("SELECT * FROM matches"))
        data = [dict(row._mapping) for row in result]
    return {"count": len(data), "matches": data}

# POST: Προσθήκη νέου αγώνα
class Match(BaseModel):
    date: str
    league: str
    home_team: str
    away_team: str
    odds: str | None = None
    smart_money:_
