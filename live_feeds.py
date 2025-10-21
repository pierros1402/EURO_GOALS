# ==============================================
# EURO_GOALS v7 – Live Feeds Module
# live_feeds.py
# ==============================================

import requests
import json
import time
from datetime import datetime
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# ----------------------------------------------
# Φόρτωση .env και βάση δεδομένων
# ----------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# Πραγματικό Sofascore Live Feed
# ----------------------------------------------
SOFASCORE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"


def fetch_feed(source_url):
    """
    Κάνει λήψη δεδομένων από ένα endpoint.
    Επιστρέφει JSON ή None.
    """
    try:
        response = requests.get(source_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[LIVE_FEEDS] ❌ Error {response.status_code} από {source_url}")
    except Exception as e:
        print(f"[LIVE_FEEDS] ⚠️ Σφάλμα κατά τη λήψη: {e}")
    return None


def update_sofascore_data():
    """
    Ενημερώνει τη βάση με ζωντανά δεδομένα από Sofascore.
    """
    data = fetch_feed(SOFASCORE_URL)
    if not data:
        print("[LIVE_FEEDS] ⚠️ Δεν βρέθηκαν δεδομένα από Sofascore.")
        return

    events = data.get("events", [])
    updated_count = 0

    try:
        with engine.begin() as conn:
            for ev in events:
                match_id = ev.get("id")
                home = ev["homeTeam"]["name"]
                away = ev["awayTeam"]["name"]
                home_score = ev.get("homeScore", {}).get("current", 0)
                away_score = ev.get("awayScore", {}).get("current", 0)
                score = f"{home_score}-{away_score}"
                status = ev.get("status", {}).get("type", "unknown")
                start_time = datetime.utcfromtimestamp(ev.get("startTimestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(
                    text("""
                        INSERT INTO matches (match_id, home, away, score, status, start_time, source, updated_at)
                        VALUES (:id, :home, :away, :score, :status, :start, 'Sofascore', :updated)
                        ON CONFLICT(match_id) DO UPDATE SET
                            score = excluded.score,
                            status = excluded.status,
                            updated_at = excluded.updated;
                    """),
                    {
                        "id": match_id,
                        "home": home,
                        "away": away,
                        "score": score,
                        "status": status,
                        "start": start_time,
                        "updated": datetime.utcnow().isoformat()
                    }
                )
                updated_count += 1

        print(f"[LIVE_FEEDS] ✅ Sofascore ενημερώθηκε ({updated_count} αγώνες)")
    except Exception as e:
        print(f"[LIVE_FEEDS] ❌ Σφάλμα DB ενημέρωσης:", e)


def live_updater(interval=120):
    """
    Κύριος βρόχος ανανέωσης ανά X δευτερόλεπτα.
    """
    while True:
        print(f"\n[LIVE_FEEDS] 🔄 Checking live data ({datetime.now().strftime('%H:%M:%S')})")
        update_sofascore_data()
        time.sleep(interval)


if __name__ == "__main__":
    print("[LIVE_FEEDS] 🚀 Starting live updater (Sofascore)...")
    live_updater(interval=120)
