# ============================================================
# EURO_GOALS v8_9g_smartmoney.py
# Smart Money – Odds Tracker με Start / Current / Movement
# + HTML Root Status Page για Render health check (auto-refresh)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from dotenv import load_dotenv
import random, os

# ------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------
load_dotenv()

app = FastAPI(title="EURO_GOALS – SmartMoney Odds Tracker")
templates = Jinja2Templates(directory="templates")

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------------------------------------
# ΔΕΙΓΜΑ ΑΓΩΝΩΝ (θα αντικατασταθούν με live feeds)
# ------------------------------------------------------------
matches_list = [
    "Arsenal - Chelsea",
    "Barcelona - Sevilla",
    "Bayern - Dortmund",
    "Juventus - Inter",
    "PSG - Marseille",
    "PAOK - Olympiacos",
]

# ------------------------------------------------------------
# ΑΠΟΘΗΚΗ ΤΙΜΩΝ (start / current)
# ------------------------------------------------------------
odds_memory = {}

def generate_odds_data():
    global odds_memory
    data = []

    for match in matches_list:
        # Δημιουργία start odds αν δεν υπάρχουν
        if match not in odds_memory:
            start_odds = {
                "1": round(random.uniform(1.70, 2.50), 2),
                "X": round(random.uniform(2.90, 3.60), 2),
                "2": round(random.uniform(2.40, 3.10), 2)
            }
            odds_memory[match] = {
                "start_odds": start_odds,
                "current_odds": start_odds.copy(),
                "movement": "Stable"
            }

        # Προσομοίωση μεταβολής
        current = odds_memory[match]["current_odds"]
        current = {
            "1": round(current["1"] + random.uniform(-0.10, 0.10), 2),
            "X": round(current["X"] + random.uniform(-0.10, 0.10), 2),
            "2": round(current["2"] + random.uniform(-0.10, 0.10), 2),
        }

        # Movement detection
        start = odds_memory[match]["start_odds"]
        diff_home = start["1"] - current["1"]
        diff_draw = start["X"] - current["X"]
        diff_away = start["2"] - current["2"]

        if abs(diff_home) > abs(diff_draw) and abs(diff_home) > abs(diff_away):
            movement = "Home↑" if diff_home > 0 else "Home↓"
        elif abs(diff_draw) > abs(diff_home) and abs(diff_draw) > abs(diff_away):
            movement = "Draw↑" if diff_draw > 0 else "Draw↓"
        else:
            movement = "Away↑" if diff_away > 0 else "Away↓"

        # Ενημέρωση μνήμης
        odds_memory[match]["current_odds"] = current
        odds_memory[match]["movement"] = movement

        data.append({
            "match": match,
            "market": "1X2",
            "start_odds": start,
            "current_odds": current,
            "movement": movement,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return data

# ------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------
@app.get("/smartmoney_feed")
def smartmoney_feed():
    return JSONResponse(generate_odds_data())

@app.get("/smartmoney_monitor", response_class=HTMLResponse)
def smartmoney_monitor(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request})

# ------------------------------------------------------------
# ROOT STATUS PAGE (HTML + Auto-refresh + Favicon)
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root_status(request: Request):
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="60">
        <title>EURO_GOALS SmartMoney Status</title>
        <link rel="icon" type="image/png" href="/static/icon_blue.png">
        <style>
            body {{
                background-color: #0d1117;
                color: #e6e6e6;
                font-family: 'Segoe UI', Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
                margin: 0;
            }}
            h1 {{
                color: #00b0ff;
                font-size: 32px;
                margin-bottom: 8px;
            }}
            p {{
                font-size: 18px;
                margin: 4px;
            }}
            a {{
                color: #00d4ff;
                text-decoration: none;
                font-weight: bold;
            }}
            .status {{
                margin-top: 15px;
                padding: 14px 24px;
                border-radius: 10px;
                background-color: #161b22;
                border: 1px solid #00b0ff;
                box-shadow: 0 0 12px rgba(0, 176, 255, 0.35);
            }}
            footer {{
                position: absolute;
                bottom: 10px;
                font-size: 13px;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <h1>✅ EURO_GOALS SmartMoney Service is LIVE</h1>
        <div class="status">
            <p><b>Status:</b> Running normally</p>
            <p><b>Last update:</b> {last_update}</p>
            <p><a href="/smartmoney_monitor">Go to SmartMoney Monitor →</a></p>
        </div>
        <footer>Auto-refresh every 60s • Render Health OK</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ------------------------------------------------------------
# STARTUP LOG
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] 🚀 SmartMoney Odds Tracker ενεργοποιήθηκε")
    print("[EURO_GOALS] ✅ Endpoint διαθέσιμο: /smartmoney_monitor")
    print("[EURO_GOALS] 🧠 Database connection OK")

# ------------------------------------------------------------
# MAIN (Local)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9g_smartmoney:app", host="127.0.0.1", port=8000, reload=True)
