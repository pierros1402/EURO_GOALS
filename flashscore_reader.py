# ==============================================
# EURO_GOALS v7 – Flashscore Live Reader
# flashscore_reader.py
# ==============================================

import requests
import re
import time
from datetime import datetime
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# ----------------------------------------------
# Ρύθμιση .env και βάση δεδομένων
# ----------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# Πραγματικό Flashscore Live URL (ποδόσφαιρο)
# ----------------------------------------------
FLASHSCORE_URL = "https://www.flashscore.com/football/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0 Safari/537.36"
    )
}


def fetch_flashscore_html():
    """
    Λαμβάνει το HTML των ζωντανών αγώνων από το Flashscore.
    """
    try:
        response = requests.get(FLASHSCORE_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"[FLASHSCORE] ❌ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"[FLASHSCORE] ⚠️ Σφάλμα κατά τη λήψη: {e}")
    return None


def parse_flashscore(html):
    """
    Εξάγει δεδομένα αγώνων από το Flashscore HTML.
    Επιστρέφει λίστα με dicts: {id, home, away, score, status}.
    """
    matches = []

    try:
        # Κάθε match έχει τμήμα με 'event__match' HTML
        pattern = re.compile(
            r'data-event-id="(?P<id>\w+)"[\s\S]*?event__participant--home">(?P<home>[^<]+).*?'
            r'event__score--home">(?P<home_score>\d+|&nbsp;).*?'
            r'event__score--away">(?P<away_score>\d+|&nbsp;).*?'
            r'event__participant--away">(?P<away>[^<]+)',
            re.MULTILINE
        )
        for m in pattern.finditer(html):
            match_id = m.group("id")
            home = m.group("home").strip()
            away = m.group("away").strip()
            home_score = m.group("home_score").replace("&nbsp;", "-")
            away_score = m.group("away_score").replace("&nbsp;", "-")
            score = f"{home_score}-{away_score}"

            # Ελέγχουμε αν το παιχνίδι είναι live (συνήθως περιέχει "event__stage--live")
            status = "live" if f'data-event-id="{match_id}"' in html and "event__stage--live" in html else "finished"

            matches.append({
                "id": match_id,
                "home": home,
                "away": away,
                "score": score,
                "status": status
            })

    except Exception as e:
        print(f"[FLASHSCORE] ⚠️ Σφάλμα parsing: {e}")

    return matches


def update_database(matches):
    """
    Ενημερώνει τους πίνακες matches στη βάση.
    """
    if not matches:
        print("[FLASHSCORE] ⚠️ Δεν βρέθηκαν ενεργοί αγώνες.")
        return

    try:
        with engine.begin() as conn:
            for match in matches:
                conn.execute(text("""
                    INSERT INTO matches (match_id, home, away, score, status, source, updated_at)
                    VALUES (:id, :home, :away, :score, :status, 'Flashscore', :updated)
                    ON CONFLICT(match_id) DO UPDATE SET
                        score = excluded.score,
                        status = excluded.status,
                        updated_at = excluded.updated;
                """), {
                    "id": match["id"],
                    "home": match["home"],
                    "away": match["away"],
                    "score": match["score"],
                    "status": match["status"],
                    "updated": datetime.utcnow().isoformat()
                })
        print(f"[FLASHSCORE] ✅ Ενημερώθηκαν {len(matches)} αγώνες από Flashscore.")
    except Exception as e:
        print(f"[FLASHSCORE] ❌ Σφάλμα DB ενημέρωσης:", e)


def flashscore_updater(interval=180):
    """
    Κύριος βρόχος ενημέρωσης (ανά 3 λεπτά).
    """
    while True:
        print(f"\n[FLASHSCORE] 🔄 Checking live data ({datetime.now().strftime('%H:%M:%S')})")
        html = fetch_flashscore_html()
        if html:
            matches = parse_flashscore(html)
            update_database(matches)
        time.sleep(interval)


if __name__ == "__main__":
    print("[FLASHSCORE] 🚀 Starting Flashscore Live Reader...")
    flashscore_updater(interval=180)
