# ==========================================================
# EURO_GOALS_v6f_debug.py  (Render working version - UI Ready)
# ==========================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os, sys, time, json, random, threading, requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

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

print("🌍 EURO_GOALS ξεκινά κανονικά...")
