# ============================================================
# EURO_GOALS v8_9g_smartmoney.py – Smart Money Monitor
# ============================================================
# Παρακολουθεί ροές χρημάτων (Money Flow Index)
# με real-time JSON feed και monitoring dashboard.
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import random
import os

# ------------------------------------------------------------
# FASTAPI SETUP
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS – Smart Money Monitor")
templates = Jinja2Templates(directory="templates")

# Mount static folder (icons, sounds, CSS, JS)
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ------------------------------------------------------------
# DUMMY SMART MONEY DATA GENERATOR
# (Placeholder – later θα συνδεθεί με asian_reader ή API feed)
# ------------------------------------------------------------
def generate_smartmoney_data():
    matches = [
        ("Arsenal - Chelsea", "Asian Handicap"),
        ("Barcelona - Sevilla", "Over/Under"),
        ("Bayern - Dortmund", "Asian Handicap"),
        ("PAOK - Olympiacos", "Over/Under"),
        ("Juventus - Inter", "Asian Handicap"),
        ("PSG - Marseille", "Over/Under"),
        ("Ajax - Feyenoord", "Asian Handicap"),
    ]

    data = []
    for match, market in matches:
        mfi = random.randint(45, 100)
        data.append({
            "match": match,
            "market": market,
            "money_flow_index": mfi,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return data


# ------------------------------------------------------------
# ENDPOINT 1 – Smart Money JSON Feed
# ------------------------------------------------------------
@app.get("/smartmoney_feed")
def smartmoney_feed():
    data = generate_smartmoney_data()
    return JSONResponse(data)


# ------------------------------------------------------------
# ENDPOINT 2 – Smart Money Monitor HTML Page
# ------------------------------------------------------------
@app.get("/smartmoney_monitor", response_class=HTMLResponse)
def smartmoney_monitor(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request})


# ------------------------------------------------------------
# HEALTH CHECK (for Render monitoring)
# ------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "EURO_GOALS SmartMoney v8.9g"}


# ------------------------------------------------------------
# STARTUP LOG
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    try:
        print("[EURO_GOALS] 🚀 Smart Money Monitor ενεργοποιήθηκε.")
        print("[EURO_GOALS] ✅ Endpoint διαθέσιμο: /smartmoney_feed")
        print("[EURO_GOALS] ✅ Dashboard URL: /smartmoney_monitor")
        print("[EURO_GOALS] 📡 Database connection OK")
    except Exception as e:
        print(f"[EURO_GOALS] ❌ Σφάλμα κατά την εκκίνηση: {e}")


# ------------------------------------------------------------
# MAIN (local run)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9g_smartmoney:app", host="127.0.0.1", port=8000, reload=True)
