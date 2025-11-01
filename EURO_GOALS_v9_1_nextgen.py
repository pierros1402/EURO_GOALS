# ================================================================
# EURO_GOALS v9.1_nextgen – Unified Platform
# ================================================================
# Περιλαμβάνει:
#  - Dual Data Engine (SmartMoney + GoalMatrix)
#  - Alert System + JSON logs
#  - FastAPI + UI templates + Health routes
# ================================================================

import os
import json
import time
import threading
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# ---------------------------------------------------------------
# 1. Φόρτωση .env
# ---------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
SMARTMONEY_REFRESH = int(os.getenv("SMARTMONEY_REFRESH_INTERVAL", 60))
GOALMATRIX_REFRESH = int(os.getenv("GOALMATRIX_REFRESH_INTERVAL", 45))
DUAL_ENGINE_MODE = os.getenv("DUAL_ENGINE_MODE", "ON")

SYSTEM_STATUS_FILE = os.getenv("SYSTEM_STATUS_FILE", "data/system_status.json")
ALERT_HISTORY_FILE = os.getenv("ALERT_HISTORY_FILE", "data/alert_history.json")

# ---------------------------------------------------------------
# 2. Logging
# ---------------------------------------------------------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/eurogoals_v9_1.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EURO_GOALS_v9_1")

# ---------------------------------------------------------------
# 3. FastAPI App + UI
# ---------------------------------------------------------------
app = FastAPI(title="EURO_GOALS v9.1_nextgen", version="9.1")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------
# 4. Utility: update system_status.json & alert_history.json
# ---------------------------------------------------------------
def update_status(engine_name: str, state: str):
    """Ενημερώνει το system_status.json"""
    try:
        os.makedirs(os.path.dirname(SYSTEM_STATUS_FILE), exist_ok=True)
        data = {}
        if os.path.exists(SYSTEM_STATUS_FILE):
            with open(SYSTEM_STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[engine_name] = {
            "status": state,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(SYSTEM_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Σφάλμα ενημέρωσης system_status.json: {e}")

def append_alert(source: str, message: str):
    """Καταγραφή νέας ειδοποίησης"""
    try:
        os.makedirs(os.path.dirname(ALERT_HISTORY_FILE), exist_ok=True)
        data = []
        if os.path.exists(ALERT_HISTORY_FILE):
            with open(ALERT_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "message": message
        }
        data.insert(0, entry)
        with open(ALERT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data[:500], f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Σφάλμα καταγραφής ειδοποίησης: {e}")

# ---------------------------------------------------------------
# 5. SmartMoney Engine
# ---------------------------------------------------------------
def smartmoney_engine():
    while True:
        try:
            logger.info("🔍 [SmartMoney] Έλεγχος αποδόσεων σε εξέλιξη...")
            time.sleep(2)
            signal_found = True
            if signal_found:
                msg = f"[SmartMoney] Εντοπίστηκε sharp move στις {datetime.now().strftime('%H:%M:%S')}"
                logger.info(msg)
                append_alert("SMARTMONEY", msg)
                update_status("SmartMoney", "active")
        except Exception as e:
            logger.error(f"[SmartMoney] Σφάλμα: {e}")
            update_status("SmartMoney", "error")
        time.sleep(SMARTMONEY_REFRESH)

# ---------------------------------------------------------------
# 6. GoalMatrix Engine
# ---------------------------------------------------------------
def goalmatrix_engine():
    while True:
        try:
            logger.info("⚽ [GoalMatrix] Ανάλυση ρυθμού αγώνων...")
            time.sleep(3)
            prediction = True
            if prediction:
                msg = f"[GoalMatrix] Πιθανό γκολ εντός 5’ ({datetime.now().strftime('%H:%M:%S')})"
                logger.info(msg)
                append_alert("GOALMATRIX", msg)
                update_status("GoalMatrix", "active")
        except Exception as e:
            logger.error(f"[GoalMatrix] Σφάλμα: {e}")
            update_status("GoalMatrix", "error")
        time.sleep(GOALMATRIX_REFRESH)

# ---------------------------------------------------------------
# 7. Routes
# ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request})

@app.get("/status")
def get_status():
    try:
        if os.path.exists(SYSTEM_STATUS_FILE):
            with open(SYSTEM_STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        return JSONResponse(content={"status": "no data yet"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/alerts")
def get_alerts():
    if os.path.exists(ALERT_HISTORY_FILE):
        with open(ALERT_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"alerts": []})

# ---------------------------------------------------------------
# 7.5 /health_dual Route (ενισχυμένο)
# ---------------------------------------------------------------
@app.get("/health_dual", response_class=JSONResponse)
def health_dual():
    """Επιστρέφει συνοπτική εικόνα λειτουργίας SmartMoney + GoalMatrix"""
    try:
        if not os.path.exists(SYSTEM_STATUS_FILE):
            return JSONResponse(content={"status": "FAIL", "summary": "No system_status.json found"})

        with open(SYSTEM_STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        smart = data.get("SmartMoney", {}).get("status", "unknown")
        goal = data.get("GoalMatrix", {}).get("status", "unknown")

        def emoji(s):
            return {"active":"✅", "error":"❌", "initializing":"🟡"}.get(s, "⚪")

        summary = "OK"
        if "error" in (smart, goal): summary = "FAIL"
        elif "initializing" in (smart, goal): summary = "PENDING"

        resp = {
            "SmartMoney": f"{emoji(smart)} {smart}",
            "GoalMatrix": f"{emoji(goal)} {goal}",
            "overall": summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        logger.info(f"[HEALTH] Dual Engine: {summary}")
        return JSONResponse(content=resp)

    except Exception as e:
        logger.error(f"[HEALTH] Error: {e}")
        return JSONResponse(content={"status": "FAIL", "error": str(e)}, status_code=500)

@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"

@app.get("/.well-known/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"

# ---------------------------------------------------------------
# 8. Thread Startup
# ---------------------------------------------------------------
def start_engines():
    if DUAL_ENGINE_MODE.upper() != "ON":
        logger.warning("⚠️ Dual Engine Mode απενεργοποιημένο")
        return
    logger.info("🚀 Εκκίνηση Dual Data Engine...")
    threading.Thread(target=smartmoney_engine, daemon=True).start()
    threading.Thread(target=goalmatrix_engine, daemon=True).start()
    update_status("SmartMoney", "initializing")
    update_status("GoalMatrix", "initializing")

@app.on_event("startup")
def startup_event():
    logger.info("EURO_GOALS v9.1 ξεκινά...")
    start_engines()
    logger.info("✅ Dual Engine ενεργό και συγχρονισμένο.")

# ---------------------------------------------------------------
# 9. Run
# ---------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v9_1_nextgen:app", host="0.0.0.0", port=10000, reload=True)
