# ==============================================
# EURO_GOALS v8.7_SM – Smart Money Only + Logger + Excel Export
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import pandas as pd

# Μόνο το Smart Money module
from modules.asian_reader import detect_smart_money

# ==============================================
# APP INIT
# ==============================================
app = FastAPI(title="EURO_GOALS v8.7_SM – Smart Money Only")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==============================================
# LOGGER
# ==============================================
def log_alert(alert_type, message):
    """Αποθηκεύει κάθε Smart Money alert σε αρχείο κειμένου με timestamp."""
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

# 💰 SMART MONEY ALERTS
@app.get("/api/trigger_smartmoney_alert")
async def smartmoney_alert():
    results = detect_smart_money()
    if results:
        alert = results[0]
        log_alert(alert["alert_type"], alert["message"])
        return JSONResponse(alert)
    return JSONResponse({"alert_type": None, "message": "No Smart Money movements"})

# 📜 ALERT HISTORY (UI Panel)
@app.get("/api/alert_history", response_class=PlainTextResponse)
async def alert_history():
    log_file = "alert_log.txt"
    if not os.path.exists(log_file):
        return "No alerts logged yet."
    with open(log_file, "r", encoding="utf-8") as f:
        return f.read()

# 📦 EXPORT TO EXCEL
@app.get("/export_excel")
async def export_excel():
    log_file = "alert_log.txt"
    if not os.path.exists(log_file):
        return JSONResponse({"error": "No alert_log.txt found."})

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

    df = pd.DataFrame(rows)
    filename = f"alert_log_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
    df.to_excel(filename, index=False)
    print(f"[EXPORT] Excel file created: {filename}")
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=filename)

# 🧠 HEALTH CHECK
@app.get("/health")
async def health():
    return {"status": "ok", "version": "8.7_SM", "time": datetime.now().isoformat()}

# ==============================================
# LOCAL RUN
# ==============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_7_SM:app", host="0.0.0.0", port=8000, reload=True)
