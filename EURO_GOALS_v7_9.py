# ==============================================
# EURO_GOALS v7.9e – FastAPI Backend (Notifications)
# ==============================================
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# -------------------------
# App & Templates
# -------------------------
app = FastAPI(title="EURO_GOALS v7.9e")
templates = Jinja2Templates(directory="templates")

if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -------------------------
# Database
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# -------------------------
# Root page
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------
# Service Worker route
# -------------------------
@app.get("/service-worker.js")
async def service_worker():
    path = os.path.join("static", "js", "service-worker.js")
    if not os.path.exists(path):
        return PlainTextResponse("// service-worker missing", media_type="application/javascript")
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    return FileResponse(path, media_type="application/javascript", headers=headers)

# -------------------------
# Notification endpoint
# -------------------------
class NotifyPayload(BaseModel):
    title: str
    body: str | None = None
    icon: str | None = None
    url: str | None = None
    tag: str | None = None
    sound: bool | None = True

@app.post("/notify")
async def notify(payload: NotifyPayload):
    return JSONResponse({
        "ok": True,
        "data": payload.dict(),
        "ts": datetime.utcnow().isoformat()
    })

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "7.9e"}

@app.on_event("startup")
def startup_event():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """))
