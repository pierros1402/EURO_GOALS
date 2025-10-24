# ==============================================
# EURO_GOALS v8.7 – Real Live Feeds + Alert Logger + Excel Export
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import pandas as pd

# Modules
from modules.goal_tracker import fetch_live_goals
from modules.asian_reader import detect_smart_money

app = FastAPI(title="EURO_GOALS v8.7 – Real Alerts + Excel Export")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==============================================
# LOGGER
# ==============================================
def log_alert(alert_type, message):
    log_file = "alert_log.txt"
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{time_now}] {alert_type.upper()} - {message}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[LOGGER] Logged {alert_type.upper()} alert.")

# ==============================================
# ROUTES
# ==============================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ⚽ Goal alerts
@app.get("/api/trigger_goal_alert")
async def goal_alert():
    results = fetch_live_goals()
    if results:
        alert = results[0]
        log_alert(alert["alert_type"], alert["message"])
        return JSONResponse(alert)
    return JSONResponse({"alert_type": None, "message": "No new goals"})

# 💰 Smart Money alerts
@app.get("/api/trigger_smartmoney_alert")
async def smartmoney_alert():
    results = detect_smart_money()
    if results:
        alert = results[0]
        log_alert(alert["alert_type"], alert["message"])
        return JSONResponse(alert)
    return JSONResponse({"alert_type": None, "message": "No Smart Money movements"})

# 📜 Alert history (for UI)
@app.get("/api/alert_history", response_class=PlainTextResponse)
async def alert_history():
    log_file = "alert_log.txt"
    if not os.path.exists(log_file):
        return "No alerts logged yet."
    with open(log_file, "r", encoding="utf-8") as f:
        return f.read()

# 📦 Export to Excel
@app.get("/export_excel")
async def export_excel():
    log_file = "alert_log.txt"
    if not os.path.exists(log_file):
        return JSONResponse({"error": "No alert_log.txt found."})

    # Ανάγνωση log αρχείου
    rows = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    date_part = line.split("]")[0][1:]
                    rest = line.split("]")[1].strip()
                    alert_type, message = rest.split(" - ", 1)
                    rows.append({
                        "Timestamp": date_part,
                        "Type": alert_type,
                        "Message": message
                    })
                except Exception:
                    pass

    if not rows:
        return JSONResponse({"error": "No valid entries found."})

    # Δημιουργία Excel
    df = pd.DataFrame(rows)
    filename = f"alert_log_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
    df.to_excel(filename, index=False)
    print(f"[EXPORT] Excel file created: {filename}")
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=filename)

# 🧠 Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": "8.7", "time": datetime.now().isoformat()}

# ==============================================
# LOCAL RUN
# ==============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_7:app", host="0.0.0.0", port=8000, reload=True)
