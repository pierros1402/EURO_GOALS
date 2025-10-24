# ==============================================
# EURO_GOALS v8.5 – Real Live Feeds + Alert Logger
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Εισαγωγή modules
from modules.goal_tracker import fetch_live_goals
from modules.asian_reader import detect_smart_money

# ==============================================
# APP INITIALIZATION
# ==============================================
app = FastAPI(title="EURO_GOALS v8.5 – Real Alerts & Logger")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==============================================
# ALERT LOGGER
# ==============================================
def log_alert(alert_type, message):
    """Αποθηκεύει κάθε alert σε αρχείο κειμένου με timestamp."""
    log_file = "alert_log.txt"
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{time_now}] {alert_type.upper()} - {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
        print(f"[LOGGER] ✅ Logged {alert_type.upper()} alert.")
    except Exception as e:
        print("[LOGGER] ❌ Error writing log:", e)

# ==============================================
# ROUTES
# ==============================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ⚽ GOAL ALERTS (Live Sofascore)
@app.get("/api/trigger_goal_alert")
async def goal_alert():
    results = fetch_live_goals()
    if results:
        alert = results[0]
        log_alert(alert["alert_type"], alert["message"])
        return JSONResponse(alert)
    else:
        return JSONResponse({
            "alert_type": None,
            "message": "No new goals",
            "timestamp": datetime.now().isoformat()
        })

# 💰 SMART MONEY ALERTS (Asian markets)
@app.get("/api/trigger_smartmoney_alert")
async def smartmoney_alert():
    results = detect_smart_money()
    if results:
        alert = results[0]
        log_alert(alert["alert_type"], alert["message"])
        return JSONResponse(alert)
    else:
        return JSONResponse({
            "alert_type": None,
            "message": "No Smart Money movements",
            "timestamp": datetime.now().isoformat()
        })

# 🧠 HEALTH CHECK
@app.get("/health")
async def health():
    return {"status": "ok", "version": "8.5", "time": datetime.now().isoformat()}

# ==============================================
# LOCAL RUN
# ==============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_5:app", host="0.0.0.0", port=8000, reload=True)
