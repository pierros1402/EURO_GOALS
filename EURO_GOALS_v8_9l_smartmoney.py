# ================================================
# EURO_GOALS v8.9l – SmartMoney + Health + GoalMatrix + Unified Dashboard
# ================================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Modules
from modules.health_check import run_full_healthcheck, check_asianconnect
from modules.goal_matrix import get_goal_matrix_data

# ------------------------------------------------
# 1️⃣  FastAPI initialization
# ------------------------------------------------
app = FastAPI(title="EURO_GOALS – SmartMoney Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Serve static assets
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ------------------------------------------------
# 2️⃣  STARTUP EVENT
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("===================================================")
    print("🚀 EURO_GOALS SmartMoney Server ξεκίνησε επιτυχώς")
    print("===================================================")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Εκκίνηση εφαρμογής...")
    print("[SYSTEM] ✅ System ready for SmartMoney, Health, GoalMatrix & Unified Dashboard")

# ------------------------------------------------
# 3️⃣  MAIN ROUTES
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Αρχική σελίδα - System Status Panel"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 User accessed System Dashboard")
    return templates.TemplateResponse("system_status.html", {"request": request})

@app.get("/status_feed", response_class=JSONResponse)
async def status_feed():
    """Δοκιμαστικό feed υπηρεσιών (μπορεί να συνδεθεί με DB αργότερα)"""
    now = datetime.utcnow().isoformat()
    data = [
        {"name": "Render Service", "status": "OK", "timestamp": now, "details": "Running"},
        {"name": "Database", "status": "OK", "timestamp": now, "details": "Active connection"},
        {"name": "SmartMoney Detector", "status": "OK", "timestamp": now, "details": "Stable"},
        {"name": "Asianconnect", "status": "OK", "timestamp": now, "details": "Included in Health Monitor"},
    ]
    return JSONResponse(data)

# ------------------------------------------------
# 4️⃣  HEALTH CHECK ENDPOINTS
# ------------------------------------------------
@app.get("/health")
def health_status():
    """Επιστρέφει συνολική κατάσταση όλων των modules."""
    result = run_full_healthcheck()
    print("---------------------------------------------------")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🩺 Health Check Executed:")
    for comp, status in result["components"].items():
        icon = "✅" if status == "OK" else ("⚠️" if status == "PENDING" else "❌")
        print(f"   {icon} {comp}: {status}")
    print(f"   ➤ Summary: {result['summary']}")
    print("---------------------------------------------------")
    return result

@app.get("/check_asianconnect")
def health_asianconnect():
    """Επιστρέφει άμεσο έλεγχο Asianconnect API"""
    status = check_asianconnect()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Asianconnect direct check → {status}")
    return {
        "status": "ok" if status == "OK" else "fail",
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------------------------------------
# 5️⃣  GOAL MATRIX PAGE
# ------------------------------------------------
@app.get("/goal_matrix", response_class=HTMLResponse)
async def goal_matrix(request: Request):
    """Σελίδα ανάλυσης Goal Trends / SmartMoney"""
    data = get_goal_matrix_data()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚽ Goal Matrix page loaded")
    return templates.TemplateResponse("goal_matrix.html", {"request": request, **data})

# ------------------------------------------------
# 5B️⃣  UNIFIED DASHBOARD PAGE (όλα τα modules μαζί)
# ------------------------------------------------
@app.get("/unified", response_class=HTMLResponse)
async def unified_dashboard(request: Request):
    """Ενοποιημένο Dashboard που περιλαμβάνει όλα τα modules"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧭 Unified Dashboard loaded")
    return templates.TemplateResponse("unified_dashboard.html", {"request": request})

# ------------------------------------------------
# 6️⃣  ERROR HANDLER
# ------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] ❌ {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "message": "Internal Server Error"}
    )

print("🧭 ROUTE /unified registered successfully!")
# ------------------------------------------------
# 7️⃣  UNIFIED DASHBOARD PAGE
# ------------------------------------------------
print("🧭 ROUTE /unified registered successfully!")

@app.get("/unified", response_class=HTMLResponse)
async def unified_dashboard(request: Request):
    """Ενιαία σελίδα EURO_GOALS – System + GoalMatrix + SmartMoney"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧭 Unified Dashboard opened")
    return templates.TemplateResponse("unified_dashboard.html", {"request": request})

# ------------------------------------------------
# 8️⃣ LOCAL TEST SERVER (SAFE MODE)
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting EURO_GOALS Unified Dashboard server on http://127.0.0.1:10000 ...")
    uvicorn.run(
        "EURO_GOALS_v8_9l_smartmoney:app",
        host="127.0.0.1",
        port=10000,
        reload=False
    )
