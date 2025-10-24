# ==============================================
# SOFASCORE READER – Live Football Feed (Clean v2)
# ==============================================
import requests
from datetime import datetime

def get_live_matches():
    try:
        url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        response = requests.get(url, timeout=10)
        data = response.json()

        events = data.get("events", [])
        matches = []

        for e in events:
            try:
                league = e["tournament"]["name"]
                home = e["homeTeam"]["name"]
                away = e["awayTeam"]["name"]
                score_home = e["homeScore"].get("current", 0)
                score_away = e["awayScore"].get("current", 0)
                status = e.get("status", {}).get("type", "")
                minute = e.get("time", {}).get("currentPeriodStartTimestamp", None)

                matches.append({
                    "league": league,
                    "home": f"{home} ({score_home})",
                    "away": f"{away} ({score_away})",
                    "status": status,
                    "minute": datetime.fromtimestamp(minute).strftime("%H:%M") if minute else "-"
                })
            except KeyError:
                continue

        print(f"[SOFASCORE] ✅ Retrieved {len(matches)} live matches.")
        return matches

    except Exception as e:
        print(f"[SOFASCORE] ❌ Error fetching live matches: {e}")
        return []
