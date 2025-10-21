# ==============================================
# LIVE_FEEDS MODULE (EURO_GOALS v7)
# ==============================================
# Συνδυάζει Sofascore + Flashscore για live δεδομένα.
# Περιλαμβάνει header spoofing ώστε να αποφεύγονται 403 από Sofascore.
# ==============================================

import requests
import json
import time
from datetime import datetime
from sqlalchemy import create_engine, text
import os

# ----------------------------------------------
# Database setup
# ----------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# Helper: Λήψη δεδομένων με User-Agent
# ----------------------------------------------
def fetch_feed(source_url):
    """
    Κάνει λήψη JSON δεδομένων με headers ώστε να αποφεύγονται 403 Forbidden errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    try:
        response = requests.get(source_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[LIVE_FEEDS] ❌ Error {response.status_code} από {source_url}")
    except Exception as e:
        print(f"[LIVE_FEEDS] ⚠️ Σφάλμα κατά τη λήψη ({source_url}): {e}")
    return None

# ----------------------------------------------
# Sofascore Feed
# ----------------------------------------------
def update_sofascore_data():
    print("[THREAD] 🟢 Sofascore feed running...")
    sofascore_url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    data = fetch_feed(sofascore_url)
    if not data or "events" not in data:
        print("[LIVE_FEEDS] ⚠️ Δεν βρέθηκαν δεδομένα από Sofascore.")
        return

    events = data["events"]
    print(f"[LIVE_FEEDS] ✅ Λήφθηκαν {len(events)} αγώνες από Sofascore.")

    try:
        with engine.begin() as conn:
            for e in events:
                match_id = f"sofa_{e['id']}"
                home = e["homeTeam"]["name"]
                away = e["awayTeam"]["name"]
                score_home = e.get("homeScore", {}).get("current", 0)
                score_away = e.get("awayScore", {}).get("current", 0)
                score = f"{score_home}-{score_away}"
                status = e["status"]["type"]
                updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(text("""
                    INSERT INTO matches (match_id, home, away, score, status, source, updated_at)
                    VALUES (:match_id, :home, :away, :score, :status, 'Sofascore', :updated_at)
                    ON CONFLICT(match_id) DO UPDATE SET
                        score=:score,
                        status=:status,
                        updated_at=:updated_at
                """), {
                    "match_id": match_id,
                    "home": home,
                    "away": away,
                    "score": score,
                    "status": status,
                    "updated_at": updated_at
                })
        print("[LIVE_FEEDS] 🟢 Sofascore database updated.")
    except Exception as e:
        print(f"[LIVE_FEEDS] ❌ Σφάλμα ενημέρωσης Sofascore DB: {e}")

# ----------------------------------------------
# Flashscore Feed (προαιρετικό / placeholder)
# ----------------------------------------------
def update_flashscore_data():
    print("[THREAD] 🔵 Flashscore feed running...")
    # Αντίστοιχη λογική θα προστεθεί με HTML scraping ή API relay
    # προς το παρόν παραμένει placeholder
    return

# ----------------------------------------------
# Συνδυασμός Feeds (Cross-Verification)
# ----------------------------------------------
def sync_live_feeds():
    """
    Συνδυάζει Sofascore + Flashscore για ενιαίο αποτέλεσμα.
    Μπορεί να καλείται από background thread ή manual trigger.
    """
    try:
        update_sofascore_data()
        update_flashscore_data()
        print("[LIVE_FEEDS] ✅ Combined feed sync complete.")
    except Exception as e:
        print(f"[LIVE_FEEDS] ❌ Error during sync: {e}")

# ----------------------------------------------
# Main (for local testing)
# ----------------------------------------------
if __name__ == "__main__":
    print("🔄 Testing live feed update...")
    sync_live_feeds()
