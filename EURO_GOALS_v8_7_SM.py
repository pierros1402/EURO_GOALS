# ==============================================
# EURO_GOALS v8.7_SM – Smart Money Integration (Render ready)
# ==============================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import json

# Εισαγωγή Smart Money module
from modules.asian_reader import detect_smart_money

# ----------------------------------------------
# FastAPI app setup
# ----------------------------------------------
app = FastAPI(title="EURO_GOALS v8.7_SM – Smart Money Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------
# Ριζικό endpoint (προαιρετικό)
# ----------------------------------------------
@app.get("/")
def root():
    return HTMLResponse(
        """
        <h2>⚽ EURO_GOALS v8.7_SM is Live!</h2>
        <p>Smart Money detector running on Render.</p>
        <p>Check health: <a href="/api/health" target="_blank">/api/health</a></p>
        <p>Trigger scan manually: <a href="/api/smartmoney/scan" target="_blank">/api/smartmoney/scan</a></p>
        """
    )

# ----------------------------------------------
# Health Check endpoint (Render)
# ----------------------------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "EURO_GOALS_SM", "timestamp": datetime.now().isoformat()}


# ----------------------------------------------
# Χειροκίνητο trigger Smart Money scan
# ----------------------------------------------
@app.get("/api/smartmoney/scan")
def manual_smartmoney_scan():
    print("[EURO_GOALS] 🧠 Manual Smart Money scan requested")
    results = detect_smart_money()
    return JSONResponse({"status": "ok", "data": results})


# ----------------------------------------------
# Αυτόματος scheduler κάθε 60 δευτερόλεπτα
# ----------------------------------------------
scheduler = BackgroundScheduler()

def scheduled_smartmoney_check():
    print(f"[SCHEDULER] 🕒 Smart Money auto-scan ενεργό ({datetime.now().strftime('%H:%M:%S')})")
    detect_smart_money()

scheduler.add_job(scheduled_smartmoney_check, "interval", seconds=60)
scheduler.start()


# ----------------------------------------------
# Εκκίνηση εφαρμογής
# ----------------------------------------------
@app.on_event("startup")
def startup_event():
    print("[EURO_GOALS] ✅ Database connection established (mock).")
    print("[EURO_GOALS] 🚀 Smart Money module ready.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("[EURO_GOALS] 📴 Application shutdown complete.")


# ----------------------------------------------
# Local run (μόνο για test)
# ----------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
