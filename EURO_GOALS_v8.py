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
# ===================== SMART MONEY – SETTINGS =====================
from fastapi.responses import PlainTextResponse
SMARTMONEY_LOG = "smartmoney_log.txt"

def log_smartmoney(message: str):
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SMARTMONEY_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

# ===================== SMART MONEY – PAGE =========================
@app.get("/smartmoney", response_class=HTMLResponse)
async def smartmoney_page(request: Request):
    """Ξεχωριστή καρτέλα Smart Money Monitor"""
    return templates.TemplateResponse("smartmoney.html", {"request": request})

# ===================== SMART MONEY – API ==========================
@app.get("/api/smartmoney_scan")
async def api_smartmoney_scan():
    """
    Καλεί το modules.asian_reader.detect_smart_money()
    • επιστρέφει νέα alerts (λίστα)
    • τα γράφει και στο smartmoney_log.txt
    """
    try:
        results = asian_reader.detect_smart_money()  # list[dict] ή []
        # αποθήκευση σε log
        for a in results:
            # φτιάχνουμε καθαρό μήνυμα
            league = a.get("league", "unknown")
            match_ = a.get("match", "unknown")
            movement = a.get("movement", "")
            log_smartmoney(f"💰 {league} – {match_} ({movement})")
        return {"status": "ok", "alerts": results}
    except Exception as e:
        print("[SMART MONEY API] ❌ Error:", e)
        return {"status": "error", "message": str(e)}

@app.get("/api/smartmoney_history", response_class=PlainTextResponse)
async def api_smartmoney_history():
    """Επιστρέφει όλο το ιστορικό Smart Money (ως text)"""
    if not os.path.exists(SMARTMONEY_LOG):
        return "No Smart Money alerts yet."
    with open(SMARTMONEY_LOG, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/smartmoney_clear")
async def api_smartmoney_clear():
    """(προαιρετικό) Καθαρίζει το log"""
    if os.path.exists(SMARTMONEY_LOG):
        os.remove(SMARTMONEY_LOG)
    return {"status": "ok", "message": "Smart Money log cleared."}
