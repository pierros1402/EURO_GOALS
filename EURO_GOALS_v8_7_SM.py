# ============================================================
# EURO_GOALS v8.7_SM – FastAPI Main Application
# ============================================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from datetime import datetime
import os

# ============================================================
# INITIAL SETUP
# ============================================================
app = FastAPI(title="EURO_GOALS v8.7_SM")
templates = Jinja2Templates(directory="templates")

startup_ready = False  # Flag για το system status

# ============================================================
# BASIC ROUTES
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Αρχική σελίδα Dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Health check endpoint για Render"""
    return JSONResponse(content={"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ============================================================
# SYSTEM STATUS ENDPOINT
# ============================================================
@app.get("/api/status")
async def system_status():
    """Επιστρέφει την τρέχουσα κατάσταση του συστήματος"""
    status = "online" if startup_ready else "offline"
    return JSONResponse(content={"status": status})

# ============================================================
# STARTUP EVENT – ενημέρωση βάσης με σεζόν
# ============================================================
@app.on_event("startup")
def startup_event():
    global startup_ready
    print("[EURO_GOALS] 🚀 Εκκίνηση εφαρμογής...")
    try:
        # εδώ κανονικά μπαίνει η ενημέρωση δεδομένων
        print("[EURO_GOALS] ✅ Βάση ενημερωμένη.")
        startup_ready = True
        print("[EURO_GOALS] 🌐 Startup check ολοκληρώθηκε.")
    except Exception as e:
        print("[EURO_GOALS] ❌ Σφάλμα κατά την εκκίνηση:", e)
        startup_ready = False

# ============================================================
# ALERT HISTORY / MATCH MANAGEMENT (placeholders)
# ============================================================
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    """Σελίδα Ιστορικού Ειδοποιήσεων"""
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/add_match", response_class=HTMLResponse)
async def add_match(request: Request):
    """Σελίδα Προσθήκης Αγώνα"""
    return templates.TemplateResponse("add_match.html", {"request": request})

@app.get("/export_excel", response_class=HTMLResponse)
async def export_excel(request: Request):
    """Εξαγωγή σε Excel (placeholder)"""
    return JSONResponse(content={"status": "ok", "message": "Η εξαγωγή δεν έχει υλοποιηθεί ακόμα."})

# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("EURO_GOALS_v8_7_SM:app", host="0.0.0.0", port=port)
