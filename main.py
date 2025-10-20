# ==============================================
# EURO_GOALS v6f – FastAPI Backend
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import openpyxl
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        if "sqlite" in DATABASE_URL:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    league TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    home_odds REAL,
                    draw_odds REAL,
                    away_odds REAL,
                    result TEXT
                )
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    league TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    home_odds REAL,
                    draw_odds REAL,
                    away_odds REAL,
                    result TEXT
                )
            """))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/matches")
def get_matches():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM matches O*
