# ==============================================
# EURO_GOALS v8.1 – Alert Sounds Integration
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# ==============================================
# 🔧 INITIALIZATION
# ==============================================
app = FastAPI(title="EURO_GOALS v8.1 – Alert Center")

# Mount static folder (icons, sounds, css, js)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

# ==============================================
# 🏠 ROOT PAGE
# ==============================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Loads the main Alert Center interface.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# ==============================================
# ⚽ GOAL ALERT ENDPOINT
# ==============================================
@app.get("/api/trigger_goal_alert")
async def trigger_goal_alert():
    """
    Simulates a Goal alert.
    This can later be connected to the live scores feed (Flashscore/Sofascore).
    """
    print("[ALERT] ⚽ Goal Alert Triggered")
    return JSONResponse({
        "alert_type": "goal",
        "message": "Goal detected!",
        "timestamp": datetime.now().isoformat()
    })

# ==============================================
# 💰 SMART MONEY ALERT ENDPOINT
# ==============================================
@app.get("/api/trigger_smartmoney_alert")
async def trigger_smartmoney_alert():
    """
    Simulates a Smart Money alert.
    This can later be connected to asian_reader.py or betfair_reader.py.
    """
    print("[ALERT] 💰 Smart Money Movement Detected")
    return JSONResponse({
        "alert_type": "smartmoney",
        "message": "Smart Money movement detected!",
        "timestamp": datetime.now().isoformat()
    })

# ==============================================
# 🧠 HEALTH CHECK
# ==============================================
@app.get("/health")
async def health_check():
    """
    Simple health check for Render / monitoring.
    """
    return {"status": "ok", "version": "8.1", "time": datetime.now().isoformat()}

# ==============================================
# 🚀 LOCAL RUN
# ==============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8.1:app", host="0.0.0.0", port=8000, reload=True)
