# ==============================================
# EURO_GOALS v8 – FastAPI Backend (Smart Money)
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
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
# BASIC ROUTES
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
# SMART MONEY – CORE ENDPOINT
# ==============================================
@app.get("/asian/smart-money")
async def get_smart_money():
    """
    Επιστρέφει αποτελέσματα από τον Smart Money Detector (asian_reader.py)
    """
    try:
        result = asian_reader.detect_smart_money()
        return {"status": "ok", "data": result}
    except Exception as e:
        print("[SMART MONEY API] ❌ Error:", e)
        return {"status": "error", "message": str(e)}

# ==============================================
# SMART MONEY – SETTINGS & LOGGING
# ==============================================
SMARTMONEY_LOG = "smartmoney_log.txt"

def log_smartmoney(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SMARTMONEY_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

# ==============================================
# SMART MONEY – UI PAGE
# ==============================================
@app.get("/smartmoney", response_class=HTMLResponse)
async def smartmoney_page(request: Request):
    """Ξεχωριστή καρτέλα Smart Money Monitor"""
    return templates.TemplateResponse("smartmoney.html", {"request": request})

# ==============================================
# SMART MONEY – API ROUTES
# ==============================================
@app.get("/api/smartmoney_scan")
async def api_smartmoney_scan():
    """Καλεί το asian_reader.detect_smart_money() και αποθηκεύει αποτελέσματα"""
    try:
        results = asian_reader.detect_smart_money()
        for a in results:
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
    """Επιστρέφει όλο το ιστορικό Smart Money"""
    if not os.path.exists(SMARTMONEY_LOG):
        return "No Smart Money alerts yet."
    with open(SMARTMONEY_LOG, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/smartmoney_clear")
async def api_smartmoney_clear():
    """Καθαρίζει το log"""
    if os.path.exists(SMARTMONEY_LOG):
        os.remove(SMARTMONEY_LOG)
    return {"status": "ok", "message": "Smart Money log cleared."}

# ==============================================
# HEALTH CHECK ENDPOINT
# ==============================================
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "EURO_GOALS v8 backend running successfully"}

# ==============================================
# STATIC FILES (optional)
# ==============================================
@app.get("/favicon.ico")
async def favicon():
    """επιστρέφει το εικονίδιο αν ζητηθεί"""
    path = os.path.join("static", "icons", "ball.png")
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return JSONResponse({"error": "Icon not found"}, status_code=404)

# ==============================================
# SMART MONEY – SERVER-SIDE SCHEDULER
# ==============================================
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def auto_smartmoney_job():
    """Τρέχει περιοδικά στο background"""
    from modules import asian_reader
    try:
        results = asian_reader.detect_smart_money()
        if results:
            for a in results:
                league = a.get("league", "unknown")
                match_ = a.get("match", "unknown")
                movement = a.get("movement", "")
                log_smartmoney(f"💰 {league} – {match_} ({movement}) [AUTO]")
            print(f"[AUTO SMART MONEY] ✅ {len(results)} alerts logged.")
        else:
            print("[AUTO SMART MONEY] No movements detected.")
    except Exception as e:
        print("[AUTO SMART MONEY] ❌", e)

# Εκτελείται κάθε 60 δευτερόλεπτα
scheduler.add_job(auto_smartmoney_job, "interval", seconds=60)
scheduler.start()
print("[SCHEDULER] ⏱️ Smart Money auto-scanner ενεργό (κάθε 60 sec)")
# ==============================================
# SMART MONEY – AUTO CLEANUP (κάθε 24 ώρες)
# ==============================================
def cleanup_old_smartmoney():
    """Διαγράφει alerts παλαιότερα από 24 ώρες"""
    import time
    if not os.path.exists(SMARTMONEY_LOG):
        return
    cutoff = time.time() - 86400  # 24 ώρες σε δευτερόλεπτα
    with open(SMARTMONEY_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        try:
            ts = line.split("]")[0].replace("[", "")
            ts_obj = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            if ts_obj.timestamp() > cutoff:
                new_lines.append(line)
        except:
            pass
    with open(SMARTMONEY_LOG, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("[CLEANUP] 🧹 Smart Money log cleaned (24h old removed)")

# Εκτέλεση καθαρισμού κάθε 24 ώρες
scheduler.add_job(cleanup_old_smartmoney, "interval", hours=24)
