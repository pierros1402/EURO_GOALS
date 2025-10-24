# ==============================================
# GOAL TRACKER MODULE – Sofascore Live Goals
# ==============================================
import requests
from datetime import datetime

def fetch_live_goals():
    """
    Ελέγχει για live αγώνες και ανιχνεύει νέα goals.
    Επιστρέφει λίστα με alerts.
    """
    alerts = []
    try:
        url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        res = requests.get(url, timeout=8)
        data = res.json()

        for event in data.get("events", []):
            home = event["homeTeam"]["name"]
            away = event["awayTeam"]["name"]
            score_home = event["homeScore"]["current"]
            score_away = event["awayScore"]["current"]

            # Αν ο αγώνας έχει πρόσφατα γκολ (ή σημαντική αλλαγή)
            if event.get("changes", {}).get("homeScore") or event.get("changes", {}).get("awayScore"):
                msg = f"⚽ Goal in {home} vs {away} ({score_home}-{score_away})"
                alerts.append({
                    "alert_type": "goal",
                    "message": msg,
                    "timestamp": datetime.now().isoformat()
                })
    except Exception as e:
        print("[GOAL TRACKER] ❌ Error:", e)
    return alerts
