# ==========================================================
# EURO_GOALS_v6f_debug.py – Render + Smart Money + League Selection
# ==========================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Import από το Smart Money module
from asian_reader import get_smart_money_data

print("🚀 EURO_GOALS v6f (Smart Money League Edition) starting...")

# -----------------------------------------
# FastAPI app setup
# -----------------------------------------
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# -----------------------------------------
# Root route (UI)
# -----------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------------------
# Healthcheck
# -----------------------------------------
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "EURO_GOALS online ✅"}


# -----------------------------------------
# Smart Money route – με επιλογή λίγκας
# -----------------------------------------
@app.get("/smart_money")
def smart_money(league: str = "epl"):
    """
    Επιστρέφει live odds για τη συγκεκριμένη λίγκα.
    Παράδειγμα: /smart_money?league=greece
    """
    data = get_smart_money_data(league)
    return JSONResponse({
        "status": "ok",
        "league": league,
        "last_update": data["last_update"],
        "results": data["results"]
    })


print("🌍 EURO_GOALS_v6f Debug server ready (Render Edition)")
