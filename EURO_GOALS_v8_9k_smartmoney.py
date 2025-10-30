# ============================================================
# EURO_GOALS v8_9k_smartmoney.py
# SmartMoney Monitor – targeted European leagues (Render debug)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from datetime import datetime
from threading import Thread
from pathlib import Path
import os, requests, random, time

# ------------------------------------------------------------
# ENV
# ------------------------------------------------------------
load_dotenv()
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY", "")

# ------------------------------------------------------------
# PATH FIX FOR RENDER
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="EURO_GOALS SmartMoney v8.9k")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
REFRESH_INTERVAL = 60
FEED_CACHE = []
START_ODDS = {}
LAST_REFRESH = None

# ------------------------------------------------------------
# LEAGUES
# ------------------------------------------------------------
LEAGUE_IDS = [39,40,41,42,78,79,80,135,136,140,141,61,62,197,566,94,95,88,89,144,145,203,204,207,208,103,104,113,114,120,121,106,107]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def safe_float(x):
    try: return float(x)
    except: return None

def dec_to_imp(o): return 1/o if o and o>1 else 0
def norm3(a,b,c):
    s=a+b+c
    return (a/s,b/s,c/s) if s>0 else (0,0,0)
def flow(start,cur):
    p1s,pxs,p2s = norm3(*[dec_to_imp(start[k]) for k in ["1","X","2"]])
    p1c,pxc,p2c = norm3(*[dec_to_imp(cur[k]) for k in ["1","X","2"]])
    d=(abs(p1c-p1s)+abs(pxc-pxs)+abs(p2c-p2s))/3
    return round(min(100,100*d*3.5),1)
def trend(start,cur):
    d={k:start[k]-cur[k] for k in ["1","X","2"]}
    k=max(d,key=lambda x:abs(d[x]))
    return f"{k}{'↑' if d[k]>0 else '↓'}"
def match_key(h,a): return f"{h.strip()} - {a.strip()}"

# ------------------------------------------------------------
# API-FOOTBALL
# ------------------------------------------------------------
def fetch_apifootball():
    if not APIFOOTBALL_API_KEY: return []
    headers={"x-apisports-key":APIFOOTBALL_API_KEY}
    season=datetime.now().year
    data=[]
    for lid in LEAGUE_IDS:
        try:
            r=requests.get("https://v3.football.api-sports.io/odds",
                          headers=headers,
                          params={"league":lid,"season":season,"bookmaker":8},
                          timeout=10)
            if r.status_code!=200: continue
            resp=r.json().get("response") or []
            for it in resp:
                t=it.get("teams") or {}
                home=(t.get("home") or {}).get("name") or ""
                away=(t.get("away") or {}).get("name") or ""
                mk=match_key(home,away)
                odds=it.get("odds") or []
                o1=oX=o2=None
                for book in odds:
                    for m in book.get("markets") or []:
                        if "1x2" in (m.get("name") or "").lower():
                            for s in m.get("outcomes") or []:
                                nm=(s.get("name") or "").lower()
                                pr=safe_float(s.get("price"))
                                if pr:
                                    if nm in ["home","1",home.lower()]: o1=pr
                                    elif nm in ["draw","x"]: oX=pr
                                    elif nm in ["away","2",away.lower()]: o2=pr
                if o1 and oX and o2:
                    data.append({"match":mk,"odds":{"1":o1,"X":oX,"2":o2}})
        except Exception as e:
            print(f"[SMARTMONEY] ⚠️ League {lid} skipped: {e}")
    print(f"[SMARTMONEY] ✅ API-Football fetched {len(data)} matches")
    return data

# ------------------------------------------------------------
# SIMULATION
# ------------------------------------------------------------
SIM_MATCHES=[
 "Arsenal - Chelsea","Bayern - Dortmund","PAOK - Olympiacos",
 "Juventus - Inter","Barcelona - Sevilla","PSG - Marseille"]
def simulate(n=10):
    out=[]
    for _ in range(n):
        m=random.choice(SIM_MATCHES)
        o1,oX,o2=[round(random.uniform(1.7,3.6),2) for _ in range(3)]
        out.append({"match":m,"odds":{"1":o1,"X":oX,"2":o2}})
    return out

# ------------------------------------------------------------
# ENRICH & REFRESH
# ------------------------------------------------------------
def enrich(items):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged={}
    for it in items:
        mk=it.get("match")
        o=it.get("odds") or {}
        if not all(k in o for k in ["1","X","2"]): continue
        merged[mk]=o
    out=[]
    for mk,o in merged.items():
        START_ODDS.setdefault(mk,o.copy())
        s=START_ODDS[mk]
        out.append({
            "match":mk,
            "market":"1X2",
            "start_odds":s,
            "current_odds":o,
            "movement":trend(s,o),
            "money_flow":flow(s,o),
            "timestamp":now
        })
    return out

def refresh_once():
    items=fetch_apifootball()
    if not items: items=simulate()
    unified=enrich(items)
    print(f"[SMARTMONEY] ✅ Unified {len(unified)} matches")
    return unified

def loop():
    global FEED_CACHE,LAST_REFRESH
    while True:
        try:
            FEED_CACHE=refresh_once()
            LAST_REFRESH=datetime.now()
        except Exception as e:
            print("[SMARTMONEY] ❌ Error:",e)
        time.sleep(REFRESH_INTERVAL)

# ------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------
@app.get("/smartmoney_feed")
def feed():
    if not FEED_CACHE:
        try: return JSONResponse(refresh_once())
        except: return JSONResponse(enrich(simulate()))
    return JSONResponse(FEED_CACHE)

@app.get("/smartmoney_monitor",response_class=HTMLResponse)
def monitor(request:Request):
    return templates.TemplateResponse("smartmoney_monitor.html",{"request":request})

@app.get("/",response_class=HTMLResponse)
def root(request:Request):
    last=LAST_REFRESH.strftime("%Y-%m-%d %H:%M:%S") if LAST_REFRESH else "—"
    html=f"""
    <html><head><meta charset='utf-8'><meta http-equiv='refresh' content='60'>
    <title>EURO_GOALS SmartMoney</title>
    <style>body{{background:#0d1117;color:#eee;font-family:'Segoe UI';text-align:center;padding-top:10%}}
    h1{{color:#00b0ff}}a{{color:#00d4ff;text-decoration:none}}</style></head>
    <body><h1>EURO_GOALS SmartMoney Monitor</h1>
    <p>✅ Service Active</p><p>Last Refresh: {last}</p>
    <p><a href='/smartmoney_monitor'>Open Dashboard →</a></p></body></html>"""
    return HTMLResponse(html)

# ------------------------------------------------------------
# DEBUG ROUTE (v8.9k verified)
# ------------------------------------------------------------
@app.get("/debug_templates")
def debug_templates():
    folder = BASE_DIR / "templates"
    files = [f.name for f in folder.glob("*.html")]
    print("[DEBUG] Templates found:", files)
    return {"found_templates": files, "base_dir": str(folder)}

# ------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------
@app.on_event("startup")
def start():
    print("[EURO_GOALS] 🚀 SmartMoney v8.9k started (targeted leagues)")
    Thread(target=loop,daemon=True).start()

# ------------------------------------------------------------
# MAIN (Local run)
# ------------------------------------------------------------
if __name__=="__main__":
    import uvicorn
    uvicorn.run("EURO_GOALS_v8_9k_smartmoney:app",host="127.0.0.1",port=8000,reload=True)
