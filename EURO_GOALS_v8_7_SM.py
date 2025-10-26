# ==============================================
# EURO_GOALS v8.7_SM – Smart Money Integration (Render ready)
# ==============================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

from modules.asian_reader import detect_smart_money

app = FastAPI(title="EURO_GOALS v8.7_SM – Smart Money Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return HTMLResponse(
        """
        <h2>⚽ EURO_GOALS v8.7_SM is Live!</h2>
        <p>Health: <a href="/api/health" target="_blank">/api/health</a></p>
        <p>Manual scan: <a href="/api/smartmoney/scan" target="_blank">/api/smartmoney/scan</a></p>
        """
    )

# Health Check για Render
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "EURO_GOALS_SM", "timestamp": datetime.now().isoformat()}

# Χειροκίνητη σάρωση
@app.get("/api/smartmoney/scan")
def manual_smartmoney_scan():
    res = detect_smart_money()
    return JSONResponse({"status": "ok", "data": res})

# Scheduler ανά 60"
scheduler = BackgroundScheduler()
def scheduled_smartmoney_check():
    print(f"[SCHEDULER] 🕒 auto-scan {datetime.now().strftime('%H:%M:%S')}")
    detect_smart_money()

scheduler.add_job(scheduled_smartmoney_check, "interval", seconds=60)
scheduler.start()

@app.on_event("startup")
def on_start():
    print("[EURO_GOALS] 🚀 App startup OK.")

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
    print("[EURO_GOALS] 📴 Shutdown complete.")

# Local run / Render uses Start Command
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render δίνει αυτόματα PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
