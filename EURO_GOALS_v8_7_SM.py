# ============================================================
# EURO_GOALS v8.7_SM – FastAPI Main Application (System Panel)
# ============================================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from datetime import datetime
import os

from modules.status_monitor import check_status

app = FastAPI(title="EURO_GOALS v8.7_SM")
templates = Jinja2Templates(directory="templates")

startup_ready = False

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})

@app.get("/api/status")
async def system_status():
    return JSONResponse(content={"status": "online" if startup_ready else "offline"})

# 🆕 Πίνακας κατάστασης modules
@app.get("/api/status_panel")
async def status_panel():
    return JSONResponse(content={"modules": check_status()})

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    global startup_ready
    print("[EURO_GOALS] 🚀 Εκκίνηση εφαρμογής...")
    try:
        print("[EURO_GOALS] ✅ Βάση ενημερωμένη.")
        startup_ready = True
        print("[EURO_GOALS] 🌐 Startup check ολοκληρώθηκε.")
    except Exception as e:
        print("[EURO_GOALS] ❌ Σφάλμα:", e)
        startup_ready = False

# ------------------------------------------------------------
# PLACEHOLDER ROUTES
# ------------------------------------------------------------
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/add_match", response_class=HTMLResponse)
async def add_match(request: Request):
    return templates.TemplateResponse("add_match.html", {"request": request})

@app.get("/export_excel", response_class=HTMLResponse)
async def export_excel(request: Request):
    return JSONResponse(content={"status": "ok", "message": "Η εξαγωγή δεν έχει υλοποιηθεί ακόμα."})

# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("EURO_GOALS_v8_7_SM:app", host="0.0.0.0", port=port)
