# ================================================================
# EURO_GOALS v9.1 – Dual Data Engine (SmartMoney + GoalMatrix)
# ================================================================
# Συνδυάζει δύο ανεξάρτητες μηχανές δεδομένων:
# - SmartMoney Engine: Ανάλυση αγορών/μεταβολών αποδόσεων
# - GoalMatrix Engine: Ανάλυση ρυθμού και πιθανότητας γκολ
#
# Περιλαμβάνει health route (/health_dual) για ταχεία εποπτεία.
# ================================================================

import os
import json
import time
import threading
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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

SMARTMONEY_LOG = os.getenv("SMARTMONEY_LOG_FILE", "logs/smartmoney.log")
GOALMATRIX_LOG = os.getenv("GOALMATRIX_LOG_FILE", "logs/goalmatrix.log")

# ---------------------------------------------------------------
# 2. Logging Configuration
# ---------------------------------------------------------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dual_engine.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DualEngine")

# ---------------------------------------------------------------
# 3. SmartMoney Engine
# ---------------------------------------------------------------
def smartmoney_engine():
    """Ανάλυση κινήσεων αποδόσεων και εντοπισμός Smart Money"""
    while True:
        try:
            logger.info("🔍 [SmartMoney] Έλεγχος αποδόσεων σε εξέλιξη...")
            time.sleep(2)
            signal_found = True  # Placeholder
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
# 4. GoalMatrix Engine
# ---------------------------------------------------------------
def goalmatrix_engine():
    """Ανάλυση ρυθμού και πιθανότητας επόμενου γκολ"""
    while True:
        try:
            logger.info("⚽ [GoalMatrix] Ανάλυση ρυθμού αγώνων...")
            time.sleep(3)
            prediction = True  # Placeholder
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
# 5. Καταγραφή Κατάστασης & Ειδοποιήσεων
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
    """Καταγράφει νέα ειδοποίηση στο alert_history.json"""
    try:
        os.makedirs("data", exist_ok=True)
        alert_file = os.getenv("ALERT_HISTORY_FILE", "data/alert_history.json")
        data = []
        if os.path.exists(alert_file):
            with open(alert_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "message": message
        }
        data.insert(0, entry)
        with open(alert_file, "w", encoding="utf-8") as f:
            json.dump(data[:500], f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Σφάλμα καταγραφής ειδοποίησης: {e}")

# ---------------------------------------------------------------
# 6. FastAPI Application
# ---------------------------------------------------------------
app = FastAPI(title="EURO_GOALS Dual Engine API", version="9.1")

@app.get("/status")
def get_status():
    """Επιστρέφει την τρέχουσα κατάσταση των δύο μηχανών"""
    try:
        if os.path.exists(SYSTEM_STATUS_FILE):
            with open(SYSTEM_STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        else:
            return JSONResponse(content={"status": "no data yet"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/alerts")
def get_alerts():
    """Επιστρέφει το ιστορικό ειδοποιήσεων"""
    alert_file = os.getenv("ALERT_HISTORY_FILE", "data/alert_history.json")
    if os.path.exists(alert_file):
        with open(alert_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"alerts": []})

# ---------------------------------------------------------------
# 7. Εκκίνηση Threads
# ---------------------------------------------------------------
def start_engines():
    if DUAL_ENGINE_MODE.upper() != "ON":
        logger.warning("⚠️ Dual Engine Mode απενεργοποιημένο στο .env")
        return

    logger.info("🚀 Εκκίνηση Dual Data Engine...")

    threading.Thread(target=smartmoney_engine, daemon=True).start()
    threading.Thread(target=goalmatrix_engine, daemon=True).start()

    update_status("SmartMoney", "initializing")
    update_status("GoalMatrix", "initializing")

# ---------------------------------------------------------------
# 8. Startup Event
# ---------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    logger.info("EURO_GOALS v9.1 ξεκινά...")
    start_engines()
    logger.info("✅ Dual Engine ενεργό και συγχρονισμένο.")

# ---------------------------------------------------------------
# 8.5 Dual Engine Health Route
# ---------------------------------------------------------------
@app.get("/health_dual")
def health_dual():
    """Επιστρέφει συνοπτική εικόνα λειτουργίας SmartMoney + GoalMatrix"""
    try:
        status_path = os.getenv("SYSTEM_STATUS_FILE", "data/system_status.json")
        if not os.path.exists(status_path):
            return {"status": "FAIL", "summary": "No system_status.json found"}

        with open(status_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        smart_status = data.get("SmartMoney", {}).get("status", "unknown")
        goal_status = data.get("GoalMatrix", {}).get("status", "unknown")

        def to_emoji(state):
            if state == "active": return "✅"
            if state == "error": return "❌"
            if state == "initializing": return "🟡"
            return "⚪"

        summary = "OK"
        if "error" in (smart_status, goal_status):
            summary = "FAIL"
        elif "initializing" in (smart_status, goal_status):
            summary = "PENDING"

        result = {
            "SmartMoney": f"{to_emoji(smart_status)} {smart_status}",
            "GoalMatrix": f"{to_emoji(goal_status)} {goal_status}",
            "overall": summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        logger.info(f"[HEALTH] Dual Health status: {summary}")
        return result

    except Exception as e:
        logger.error(f"[HEALTH] Error reading health: {e}")
        return {"status": "FAIL", "error": str(e)}

# ---------------------------------------------------------------
# 9. Κύρια εκτέλεση (αν τρέχει standalone)
# ---------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dual_engine_manager:app", host="0.0.0.0", port=10000, reload=True)
