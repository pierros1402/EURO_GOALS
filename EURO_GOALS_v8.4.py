# ==============================================
# EURO_GOALS v8.4 – Real Live Feeds Integration
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from modules.goal_tracker import fetch_live_goals
from modules.asian_reader import detect_smart_money

app = FastAPI(title="EURO_GOALS v8.4 – Real Alerts")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ✅ Goal Alerts (Live Sofascore)
@app.get("/api/trigger_goal_alert")
async def goal_alert():
    results = fetch_live_goals()
    if results:
        return JSONResponse(results[0])
    else:
        return JSONResponse({"alert_type": None, "message": "No new goals", "timestamp": datetime.now().isoformat()})

# ✅ Smart Money Alerts (Asian markets)
@app.get("/api/trigger_smartmoney_alert")
async def smartmoney_alert():
    results = detect_smart_money()
    if results:
        return JSONResponse(results[0])
    else:
        return JSONResponse({"alert_type": None, "message": "No Smart Money movements", "timestamp": datetime.now().isoformat()})

@app.get("/health")
async def health():
    return {"status": "ok", "version": "8.4", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_4:app", host="0.0.0.0", port=8000, reload=True)
