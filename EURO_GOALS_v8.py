# ============================================================
# EURO_GOALS v8.1 – MAIN APP (Asianconnect API Status)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from asianconnect_status import check_asianconnect_status, log_message

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------
# Static files (CSS, JS, icons)
# ---------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------
# Root page
# ---------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------
# Asianconnect API check route
# ---------------------------------------------
@app.get("/check_asianconnect", response_class=JSONResponse)
def check_asianconnect():
    """Επιστρέφει JSON με την τρέχουσα κατάσταση του API"""
    result = check_asianconnect_status()
    return JSONResponse(result)


# ---------------------------------------------
# Startup event
# ---------------------------------------------
@app.on_event("startup")
def startup_event():
    log_message("[SYSTEM] 🚀 EURO_GOALS started.")
    check_asianconnect_status()
    log_message("[SYSTEM] ✅ Asianconnect status checked at startup.")
