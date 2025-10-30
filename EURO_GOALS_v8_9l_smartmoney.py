# ============================================================
# EURO_GOALS v8_9l_smartmoney.py
# FastAPI main app — SmartMoney Monitor (real APIs) + Manual League Updates
# ============================================================

from fastapi import FastAPI, Request, Path
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from dotenv import load_dotenv
from threading import Thread
from datetime import datetime
import os

# Modules
from modules.smartmoney_monitor import SmartMoneyMonitor
from modules.api_reader import SUPPORTED_LEAGUES, update_single_league

# ------------------------------------------------------------
# ENV
# ------------------------------------------------------------
load_dotenv()
APIFOOTBALL_API_KEY   = os.getenv("APIFOOTBALL_API_KEY", "")
SPORTMONKS_API_KEY    = os.getenv("SPORTMONKS_API_KEY", "")
FOOTBALLDATA_API_KEY  = os.getenv("FOOTBALLDATA_API_KEY", "")
THESPORTSDB_API_KEY   = os.getenv("THESPORTSDB_API_KEY", "")
SMARTMONEY_REFRESH_INTERVAL = int(os.getenv("SMARTMONEY_REFRESH_INTERVAL", "60"))

# ------------------------------------------------------------
# FASTAPI + PATHS (Render-safe)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="EURO_GOALS v8.9l – Main App")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ------------------------------------------------------------
# GLOBALS
# ------------------------------------------------------------
monitor: SmartMoneyMonitor | None = None
STARTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------
@app.on_event("startup")
def _startup():
    global monitor
    print("[EURO_GOALS] 🚀 Boot v8.9l")
    monitor = SmartMoneyMonitor(
        refresh_interval=SMARTMONEY_REFRESH_INTERVAL,
        apifootball_key=APIFOOTBALL_API_KEY,
        sportmonks_key=SPORTMONKS_API_KEY
    )
    t = Thread(target=monitor.run_forever, daemon=True)
    t.start()
    print(f"[EURO_GOALS] ✅ SmartMoney loop: every {SMARTMONEY_REFRESH_INTERVAL}s")
    print("[EURO_GOALS] ✅ Endpoints: /smartmoney_monitor  /smartmoney_feed  /leagues  /update_league/{code}  /health  /debug_templates  /")

# ------------------------------------------------------------
# ROOT – mini status
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    last = monitor.last_refresh_str() if monitor else "—"
    html = f"""
    <html><head>
      <meta charset="utf-8"><meta http-equiv="refresh" content="60">
      <title>EURO_GOALS v8.9l</title>
      <style>
        body {{ background:#0d1117;color:#e6e6e6;font-family:'Segoe UI',Arial; display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;}}
        h1 {{ color:#00b0ff;margin:0 0 6px }}
        a {{ color:#00d4ff; text-decoration:none; font-weight:600 }}
        .card {{ background:#161b22; border:1px solid #243041; border-radius:12px; padding:18px 24px; box-shadow:0 0 10px rgba(0,0,0,.35); text-align:center }}
        .muted {{ color:#9aa4ad; font-size:13px; margin-top:10px }}
      </style>
    </head><body>
      <div class="card">
        <h1>EURO_GOALS v8.9l</h1>
        <p>✅ Service running since <b>{STARTED_AT}</b></p>
        <p>SmartMoney last refresh: <b>{last}</b></p>
        <p><a href="/smartmoney_monitor">Open SmartMoney Monitor →</a></p>
        <p><a href="/leagues">Λίστες Λιγκών (χειροκίνητη ενημέρωση) →</a></p>
        <p class="muted">Auto-refresh every 60s</p>
      </div>
    </body></html>
    """
    return HTMLResponse(html)

# ------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------
@app.get("/health", response_class=PlainTextResponse)
def health():
    return "OK"

# ------------------------------------------------------------
# SMARTMONEY – UI + FEED
# ------------------------------------------------------------
@app.get("/smartmoney_monitor", response_class=HTMLResponse)
def smartmoney_monitor_page(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request})

@app.get("/smartmoney_feed")
def smartmoney_feed():
    if not monitor:
        return JSONResponse([])
    return JSONResponse(monitor.get_feed())

# ------------------------------------------------------------
# LEAGUES – UI
# ------------------------------------------------------------
@app.get("/leagues", response_class=HTMLResponse)
def leagues_page(request: Request):
    rows = []
    for code, meta in SUPPORTED_LEAGUES.items():
        rows.append(f"""
            <tr>
              <td>{meta['country']}</td>
              <td>{meta['name']}</td>
              <td>{meta['tier']}</td>
              <td><a href="/update_league/{code}" style="color:#00d4ff;text-decoration:none;font-weight:600">🔄 Ενημέρωση</a></td>
            </tr>
        """)
    html = f"""
    <html><head><meta charset="utf-8"><title>Λίγκες</title>
    <style>
      body{{background:#0d1117;color:#e6e6e6;font-family:'Segoe UI',Arial}}
      h1{{color:#00b0ff}}
      table{{width:100%;max-width:980px;margin:20px auto;border-collapse:collapse}}
      th,td{{border-bottom:1px solid #243041;padding:10px 8px}}
      th{{text-align:left;color:#8ccfff}}
    </style></head>
    <body>
      <div style="max-width:980px;margin:32px auto">
        <h1>Λίγκες – Χειροκίνητη Ενημέρωση</h1>
        <table>
          <thead><tr><th>Χώρα</th><th>Λίγκα</th><th>Tier</th><th>Ενέργεια</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        <p><a href="/" style="color:#00d4ff;text-decoration:none">← Επιστροφή</a></p>
      </div>
    </body></html>
    """
    return HTMLResponse(html)

# ------------------------------------------------------------
# UPDATE SINGLE LEAGUE (manual)
# ------------------------------------------------------------
@app.get("/update_league/{code}")
def update_league(code: str = Path(..., description="Κωδικός π.χ. ENG1, GER2, GRE1")):
    code = code.upper().strip()
    if code not in SUPPORTED_LEAGUES:
        return JSONResponse({"ok": False, "error": f"Άγνωστος κωδικός λίγκας: {code}"}, status_code=404)
    meta = SUPPORTED_LEAGUES[code]
    print(f"[API_READER] 🔄 Manual update: {code} – {meta['name']}")
    try:
        result = update_single_league(
            league_code=code,
            meta=meta,
            apifootball_key=APIFOOTBALL_API_KEY,
            footballdata_key=FOOTBALLDATA_API_KEY,
            sportmonks_key=SPORTMONKS_API_KEY,
            thesportsdb_key=THESPORTSDB_API_KEY
        )
        return JSONResponse({"ok": True, "code": code, "meta": meta, "summary": result})
    except Exception as e:
        print("[API_READER] ❌ Update error:", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ------------------------------------------------------------
# DEBUG ROUTE (για έλεγχο templates στο Render)
# ------------------------------------------------------------
@app.get("/debug_templates")
def debug_templates():
    folder = BASE_DIR / "templates"
    files = [f.name for f in folder.glob("*.html")]
    print("[DEBUG] Templates found:", files)
    return {"found_templates": files, "base_dir": str(folder)}
