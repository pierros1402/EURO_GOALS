from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
import os, shutil, sqlite3, socket


load_dotenv()

from colorama import Fore, Style, init
init(autoreset=True)

# 🔹 Έλεγχος αν υπάρχει σύνδεση Internet
def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# 🔹 Καθορισμός λειτουργίας
if check_internet():
    APP_MODE = "Online"
else:
    APP_MODE = "Offline"

# 🔹 Σύνδεση templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "mode": APP_MODE})

# 🔹 Σύνδεση με βάση δεδομένων (το αφήνεις όπως ήταν)
DATABASE_URL = os.getenv("DATABASE_URL")
if check_internet():
    print(Fore.GREEN + "✅ Online mode: Connected to PostgreSQL on Render")
else:
    print(Fore.RED + "⚠️ Offline mode: Using local SQLite database")
    DATABASE_URL = "sqlite:///./matches.db"



def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Ελέγχει αν υπάρχει σύνδεση Internet."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

# Αυτόματος έλεγχος
if not check_internet():
    print("⚠️ Offline mode: Using local SQLite database")
    DATABASE_URL = "sqlite:///./matches.db"
else:
    print(f"✅ Online mode: Connected to {DATABASE_URL}")
# Αποθήκευση κατάστασης λειτουργίας (online/offline)
if "sqlite" in DATABASE_URL:
    APP_MODE = "Offline"
else:
    APP_MODE = "Online"


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_odds = Column(Float, nullable=True)
    draw_odds = Column(Float, nullable=True)
    away_odds = Column(Float, nullable=True)
    result = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


class MatchCreate(BaseModel):
    home_team: str
    away_team: str
    home_odds: float | None = None
    draw_odds: float | None = None
    away_odds: float | None = None
    result: str | None = None


@app.get("/")
def root():
    return {"message": "🌐 Football Predictor API with SQLite is running on Render!"}


@app.post("/matches/")
def create_match(match: MatchCreate):
    db = SessionLocal()
    new_match = Match(**match.dict())
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    db.close()
    return {"status": "success", "data": match}


@app.get("/matches/")
def read_matches():
    db = SessionLocal()
    matches = db.query(Match).all()
    db.close()
    return {"total": len(matches), "matches": matches}


@app.get("/matches/{match_id}")
def read_match(match_id: int):
    db = SessionLocal()
    match = db.query(Match).filter(Match.id == match_id).first()
    db.close()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@app.get("/status")
def status():
    return {"status": "ok", "service": "football-predictor"}
@app.put("/matches/{match_id}")
def update_match(match_id: int, updated: MatchCreate):
    db = SessionLocal()
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        db.close()
        raise HTTPException(status_code=404, detail="Match not found")

    for key, value in updated.dict().items():
        setattr(match, key, value)
    db.commit()
    db.refresh(match)
    db.close()
    return {"status": "updated", "match": match}


@app.delete("/matches/{match_id}")
def delete_match(match_id: int):
    db = SessionLocal()
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        db.close()
        raise HTTPException(status_code=404, detail="Match not found")

    db.delete(match)
    db.commit()
    db.close()
    return {"status": "deleted", "match_id": match_id}
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# --- Smart Database Connection ---
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render / PostgreSQL connection
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("✅ Connected to PostgreSQL on Render")
else:
    # Local SQLite fallback
    engine = create_engine("sqlite:///football.db", echo=True)
    print("💾 Using local SQLite database")

# --- Initialize table ---
@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        conn.execute(text("""
          CREATE TABLE IF NOT EXISTS matches (
             id SERIAL PRIMARY KEY,
             home_team TEXT,
             away_team TEXT,
             home_odds REAL,
             draw_odds REAL,
             away_odds REAL,
             result TEXT
          )

        """))
        conn.commit()

# --- Endpoints ---

@app.get("/")
def root():
    return {"status": "ok", "message": "Football Predictor API active"}

@app.get("/matches")
def get_all_matches():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM matches"))
        matches = [dict(row._mapping) for row in result]
    return {"count": len(matches), "data": matches}

@app.get("/matches/{match_id}")
def get_match(match_id: int):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM matches WHERE id = :id"), {"id": match_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Match not found")
    return dict(result._mapping)

@app.get("/teams")
@app.delete("/matches/{match_id}")
def delete_match(match_id: int):
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM matches WHERE id = :id"), {"id": match_id})
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Match not found")
    return {"status": "deleted", "id": match_id}

def get_teams():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT home_team AS team FROM matches
            UNION
            SELECT DISTINCT away_team AS team FROM matches
        """))
        teams = [row[0] for row in result]
    return {"teams": teams}

from pydantic import BaseModel

# Μοντέλο εισόδου για POST
class Match(BaseModel):
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: float
    away_odds: float
    result: str | None = None

@app.post("/matches")
def add_match(match: Match):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO matches (home_team, away_team, home_odds, draw_odds, away_odds, result)
                VALUES (:home_team, :away_team, :home_odds, :draw_odds, :away_odds, :result)
            """),
            match.dict()
        )
        conn.commit()
    return {"status": "success", "data": match}
@app.put("/matches/{match_id}")
def update_match(match_id: int, match: Match):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM matches WHERE id = :id"),
            {"id": match_id}
        ).mappings().first()

        if not result:
            raise HTTPException(status_code=404, detail="Match not found")

        conn.execute(text("""
            UPDATE matches
            SET home_team = :home_team,
                away_team = :away_team,
                home_odds = :home_odds,
                draw_odds = :draw_odds,
                away_odds = :away_odds,
                result = :result
            WHERE id = :id
        """), {**match.dict(), "id": match_id})
        conn.commit()

    return {"status": "updated", "id": match_id, "data": match.dict()}
# =====================================
# 🟩 ADMIN RESTORE + HEALTH CHECK
# =====================================
from fastapi import UploadFile, Form
import os, sqlite3

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
DB_PATH = os.environ.get("DB_PATH", "matches.db")  # ή "football.db"

@app.post("/admin/restore")
async def admin_restore(token: str = Form(...), sql: UploadFile = None):
    """Δέχεται αρχείο SQL και κάνει restore στη βάση"""
    if token != ADMIN_TOKEN:
        return {"ok": False, "error": "unauthorized"}

    if sql is None:
        return {"ok": False, "error": "missing file 'sql'"}

    try:
        sql_text = (await sql.read()).decode("utf-8", errors="ignore")
        conn = sqlite3.connect(DB_PATH)
        conn.isolation_level = None
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = OFF;")
        cur.execute("BEGIN;")
        cur.executescript(sql_text)
        cur.execute("COMMIT;")
        cur.execute("VACUUM;")
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/health")
def health():
    """Έλεγχος λειτουργίας"""
    return {"status": "OK"}



from fastapi import File, UploadFile, Form
import os, shutil

UPLOAD_FOLDER = "backups"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload_backup")
async def upload_backup(token: str = Form(...), file: UploadFile = File(...)):


@app.post("/refresh_database")
async def refresh_database(token: str = Form(...), background_tasks: BackgroundTasks = None):
    admin_token = os.getenv("ADMIN_TOKEN")
    if token != admin_token:
        return {"status": "error", "message": "Μη έγκυρο token"}

    # Δημιουργία ονόματος βάσης με μήνα/έτος
    month_tag = datetime.now().strftime("%Y_%m")
    new_db_name = f"football_{month_tag}.db"
    new_db_path = os.path.join(os.getcwd(), new_db_name)

    # Βρες το πιο πρόσφατο .sql backup
    backups = sorted(
        [f for f in os.listdir("backups") if f.endswith(".sql")],
        reverse=True
    )
    if not backups:
        return {"status": "error", "message": "Δεν βρέθηκε backup για restore."}

    latest_backup = os.path.join("backups", backups[0])

    def restore_db():
        conn = sqlite3.connect(new_db_path)
        cursor = conn.cursor()
        with open(latest_backup, "r", encoding="utf-8") as f:
            sql_script = f.read()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()

    # Τρέξε restore στο παρασκήνιο
    if background_tasks:
        background_tasks.add_task(restore_db)
    else:
        restore_db()

    # Ενημέρωσε το .env
    with open(".env", "w", encoding="utf-8") as envf:
        envf.write(f'DB_PATH={new_db_name}\n')
        envf.write(f'ADMIN_TOKEN={admin_token}\n')

    return {
        "status": "ok",
        "message": f"Νέα βάση {new_db_name} δημιουργήθηκε και επαναφέρθηκε επιτυχώς."
    }
    token: str = Form(...),
    file: UploadFile = File(...)
):
    # Έλεγχος δικαιώματος
    admin_token = os.getenv("ADMIN_TOKEN")
    if token != admin_token:
        return {"status": "error", "message": "Μη έγκυρο token"}

    # Αποθήκευση backup στο Render
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Επιβεβαίωση
    return {
        "status": "ok",
        "message": f"Backup {file.filename} ανέβηκε επιτυχώς στο Render!",
        "path": file_path
    }


# =====================================
# ΤΕΛΟΣ ΠΡΟΣΘΗΚΗΣ
# =====================================
from fastapi import UploadFile, File, Form
import shutil

UPLOAD_FOLDER = "backups"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/refresh_database")
async def refresh_database(token: str = Form(...)):
    admin_token = os.getenv("ADMIN_TOKEN")
    if token != admin_token:
        return {"status": "error", "message": "Μη έγκυρο token"}

    return {"status": "ok", "message": "Η βάση δεδομένων ανανεώθηκε επιτυχώς!"}


@app.post("/upload_backup")
async def upload_backup(token: str = Form(...), file: UploadFile = File(...):
    """Ανέβασμα backup αρχείων στο Render"""
    admin_token = os.getenv("ADMIN_TOKEN")
    if token != admin_token:
        return {"status": "error", "message": "Μη έγκυρο token"}

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "ok",
        "message": f"Το αρχείο {file.filename} ανέβηκε επιτυχώς!"
    }


import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
