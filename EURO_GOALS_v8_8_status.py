# ============================================================
"cpu": cpu,
"ram": ram,
"disk": disk,
"errors": errors,
"logs": log_lines,
}
except Exception as e:
return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/feeds", response_class=JSONResponse)
async def get_feeds():
feeds = load_feeds()
return {"feeds": feeds, "count": len(feeds)}


@app.post("/api/feeds/save", response_class=JSONResponse)
async def save_feeds_endpoint(payload: dict = Body(...)):
feeds = payload.get("feeds", [])
ok = save_feeds(feeds)
if ok:
global feeds_cache
feeds_cache = feeds
return {"ok": True, "count": len(feeds)}
return JSONResponse({"ok": False, "error": "write_failed"}, status_code=500)


@app.post("/api/feeds/toggle", response_class=JSONResponse)
async def toggle_feed(payload: dict = Body(...)):
alias = payload.get("alias")
active = bool(payload.get("active", True))
feeds = load_feeds()
changed = False
for f in feeds:
if f.get("alias") == alias:
f["active"] = active
changed = True
break
if not changed:
return JSONResponse({"ok": False, "error": "alias_not_found"}, status_code=404)
if save_feeds(feeds):
global feeds_cache
feeds_cache = feeds
return {"ok": True}
return JSONResponse({"ok": False, "error": "write_failed"}, status_code=500)


# Health check for Render
@app.get("/api/health")
async def health_check():
return {"status": "ok"}


# ------------------------------------------------------------
# 6. Startup
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
print("[EURO_GOALS] 🚀 System Status (Dynamic Feeds + Admin) starting…")
with engine.connect() as conn:
conn.execute(text("SELECT 1"))
print(f"[EURO_GOALS] 📡 feeds.json loaded: {len(feeds_cache)} feeds")


# Local run
if __name__ == "__main__":
import uvicorn
uvicorn.run("EURO_GOALS_v8_8_status:app", host="0.0.0.0", port=8000, reload=True)