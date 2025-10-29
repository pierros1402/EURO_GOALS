# ==============================================
# EURO_GOALS v8.9g – Main App (SmartMoney + Asianconnect API Panel)
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import os

# Custom modules
from asianconnect_status import check_asianconnect_status
from asian_reader import detect_smart_money  # Αν δεν υπάρχει, άφησέ το προσωρινά ως σχόλιο

# --------------------------------------------------
# Φόρτωση .env
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# FastAPI Setup
# --------------------------------------------------
app = FastAPI(title="EURO_GOALS v8.9g – Smart Money Monitor")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------
# Database Setup (PostgreSQL / SQLite fallback)
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def make_engine():
    if "sqlite" in DATABASE_URL:
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return create_engine(DATABASE_URL, pool_pre_ping=True)

engine = make_engine()

# --------------------------------------------------
# Utilities
# --------------------------------------------------
def log_event(msg: str):
    with open("EURO_GOALS_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Βασική σελίδα (System Status Panel)
    """
    return templates.TemplateResponse("system_status.html", {"request": request})


@app.get("/check_asianconnect", response_class=JSONResponse)
async def api_check_asianconnect():
    """
    Επιστρέφει την κατάσταση του Asianconnect API
    """
    result = check_asianconnect_status()
    return result


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Επιστρέφει γενική κατάσταση συστήματος
    """
    return {"status": "ok", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/smartmoney", response_class=JSONResponse)
async def smartmoney_check():
    """
    Ελέγχει ύποπτες κινήσεις αποδόσεων (Smart Money)
    """
    try:
        result = detect_smart_money()
        log_event("[SMART MONEY] Detection complete.")
        return {"status": "ok", "result": result}
    except Exception as e:
        log_event(f"[SMART MONEY] ❌ Error: {e}")
        return {"status": "error", "message": str(e)}

# --------------------------------------------------
# STARTUP
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    log_event("[EURO_GOALS] 🚀 Application startup")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log_event("[EURO_GOALS] ✅ Database connection OK")
    except Exception as e:
        log_event(f"[EURO_GOALS] ❌ Database connection failed: {e}")

    # Αυτόματος έλεγχος Asianconnect API στο startup
    status = check_asianconnect_status()
    log_event(f"[EURO_GOALS] 🔍 Asianconnect initial status: {status['status']}")

# --------------------------------------------------
# MAIN
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9g_smartmoney:app", host="0.0.0.0", port=10000)
