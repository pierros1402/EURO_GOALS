# ==============================================
# EURO_GOALS v8 – FastAPI Backend (Smart Money)
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from dotenv import load_dotenv

# ==============================================
# Φόρτωση .env
# ==============================================
load_dotenv()

# ==============================================
# FastAPI Initialization
# ==============================================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ==============================================
# Database Connection
# ==============================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        print("[EURO_GOALS] ✅ Database connection established.")

# ==============================================
# MODULE IMPORTS
# ==============================================
from modules import asian_reader

# ==============================================
# ROUTES
# ==============================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Αρχική σελίδα"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/alerts", response_class=HTMLResponse)
async def alert_center(request: Request):
    """Alert Center"""
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/live", response_class=HTMLResponse)
async def live_page(request: Request):
    """Live Feed"""
    return templates.TemplateResponse("live.html", {"request": request})

# ==============================================
# SMART MONEY ENDPOINT (ASIAN READER)
# ==============================================
@app.get("/asian/smart-money")
async def get_smart_money():
    """
    Επιστρέφει τα αποτελέσματα του Smart Money Detector (asian_reader.py)
    """
    try:
        result = asian_reader.detect_smart_money()
        return {"status": "ok", "data": result}
    except Exception as e:
        print("[SMART MONEY API] ❌ Error:", e)
        return {"status": "error", "message": str(e)}

# ==============================================
# HEALTH CHECK ENDPOINT
# ==============================================
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EURO_GOALS v8 backend running successfully"}

# ==============================================
# STATIC FILES (optional, αν χρειάζεται)
# ==============================================
@app.get("/favicon.ico")
async def favicon():
    """επιστρέφει το εικονίδιο αν ζητηθεί"""
    path = os.path.join("static", "icons", "ball.png")
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return JSONResponse({"error": "Icon not found"}, status_code=404)
