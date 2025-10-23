# ==========================================================
# LIVE ODDS ENDPOINT (Sofascore Integration)
# ==========================================================
from sofascore_reader import get_live_matches

@app.get("/api/live_odds")
async def live_odds():
    """
    Παίρνει live δεδομένα από Sofascore και τα επιστρέφει στο Live Center.
    """
    try:
        data = get_live_matches()
        if not data:
            return [{"league": "No live matches", "home": "-", "away": "-", "odds": "-"}]
        print(f"[LIVE] ✅ Returned {len(data)} live events from Sofascore.")
        return data
    except Exception as e:
        print(f"[LIVE] ❌ Error: {e}")
        return [{"league": "Error loading live feed", "home": "-", "away": "-", "odds": "-"}]
