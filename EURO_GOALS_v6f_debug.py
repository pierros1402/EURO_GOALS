# ==========================================================
# EURO_GOALS_v6f_debug.py  (Render working version - UI + Smart Money)
# ==========================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os, json
from datetime import datetime
from typing import Dict

# Εισαγωγή Smart Money Module
from asian_reader import detect_smart_money, get_smart_money_data

print("🚀 Render new deploy check")

# -----------------------------------------
# FastAPI initialization
# -----------------------------------------
app = FastAPI()

# -----------------------------------------
# Templates & Static folders
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# -----------------------------------------
# Root route (main UI)
# -----------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -----------------------------------------
# Healthcheck route
# -----------------------------------------
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "EURO_GOALS Render online ✅"}

# -----------------------------------------
# Smart Money route (UI + auto-refresh)
# -----------------------------------------
@app.get("/smart_money")
def smart_money_check():
    """
    Επιστρέφει τα τελευταία αποθηκευμένα δεδομένα Smart Money
    (από το asian_reader.py background thread).
    """
    data = get_smart_money_data()
    return JSONResponse({
        "status": "ok",
        "last_update": data["last_update"],
        "results": data["results"]
    })

# -----------------------------------------
# Startup message
# -----------------------------------------
print("🌍 EURO_GOALS ξεκινά κανονικά με Smart Money auto-refresh ✅")
