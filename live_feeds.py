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

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# ------------------------------
# Πηγή δεδομένων (placeholder)
# ------------------------------
FLASHCORE_URL = "https://example-flashscore-api.com/live_matches"
SOFASCORE_URL = "https://example-sofascore-api.com/live"
BETFAIR_URL = "https://example-betfair-api.com/live_odds"

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
        print(f"[LIVE_FEEDS] ⚠️ Σφάλμα: {e}")
    return None


def update_database(feed_data, source_name):
    """
    Ενημερώνει τους πίνακες matches/odds στη βάση.
    """
    try:
        with engine.begin() as conn:
            for match in feed_data.get("matches", []):
                conn.execute(
                    text("""
                        INSERT INTO matches (match_id, home, away, score, status, source, updated_at)
                        VALUES (:id, :home, :away, :score, :status, :source, :updated)
                        ON CONFLICT(match_id) DO UPDATE SET
                            score = excluded.score,
                            status = excluded.status,
                            updated_at = excluded.updated;
                    """),
                    {
                        "id": match.get("id"),
                        "home": match.get("home"),
                        "away": match.get("away"),
                        "score": match.get("score", "-"),
                        "status": match.get("status", "pending"),
                        "source": source_name,
                        "updated": datetime.utcnow().isoformat()
                    }
                )
        print(f"[LIVE_FEEDS] ✅ {source_name} ενημερώθηκε ({len(feed_data.get('matches', []))} αγώνες)")
    except Exception as e:
        print(f"[LIVE_FEEDS] ❌ Σφάλμα DB update ({source_name}):", e)


def live_updater(interval=60):
    """
    Κύριος βρόχος ανανέωσης ανά X δευτερόλεπτα.
    """
    while True:
        print(f"\n[LIVE_FEEDS] 🔄 Checking live data ({datetime.now().strftime('%H:%M:%S')})")
        
        # Ενημέρωση από Flashscore
        flash_data = fetch_feed(FLASHCORE_URL)
        if flash_data:
            update_database(flash_data, "Flashscore")

        # Ενημέρωση από Sofascore
        sofa_data = fetch_feed(SOFASCORE_URL)
        if sofa_data:
            update_database(sofa_data, "Sofascore")

        # Ενημέρωση από Betfair
        betfair_data = fetch_feed(BETFAIR_URL)
        if betfair_data:
            update_database(betfair_data, "Betfair")

        time.sleep(interval)  # αναμονή πριν τον επόμενο κύκλο


if __name__ == "__main__":
    print("[LIVE_FEEDS] 🚀 Starting live updater...")
    live_updater(interval=120)
