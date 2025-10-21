# ==============================================
# MARKET READER MODULE – Betfair Volumes Integration
# EURO_GOALS v6g – Live Data + Safe Fallback
# ==============================================

from datetime import datetime
from betfair_client import BetfairClient
import random

MARKET_CACHE = {
    "last_update": None,
    "markets": []
}

def get_market_data():
    """
    Προσπαθεί να αντλήσει live markets από Betfair Exchange.
    Αν δεν υπάρχουν credentials ή αποτύχει το API, γυρίζει mock δεδομένα.
    """
    try:
        bf = BetfairClient()
        if not bf.is_configured():
            print("[MARKET READER] ⚠️ Betfair keys not found – using mock data.")
            return _generate_mock()

        print("[MARKET READER] 🔍 Fetching live Betfair markets...")
        data = bf.get_match_odds_snapshot(max_results=6)

        if not data:
            print("[MARKET READER] ⚠️ Empty response – fallback to mock.")
            return _generate_mock()

        MARKET_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        MARKET_CACHE["markets"] = data

        print(f"[MARKET READER] ✅ Updated {len(data)} markets from Betfair.")
        return MARKET_CACHE

    except Exception as e:
        print("[MARKET READER] ❌ Error fetching Betfair data:", e)
        return _generate_mock()


# -----------------------------
# Mock fallback (default mode)
# -----------------------------
def _generate_mock():
    sample_matches = [
        "Olympiacos - AEK", "PAOK - Aris", "Panathinaikos - Lamia",
        "Man City - Liverpool", "Real Madrid - Barcelona", "PSG - Lyon",
        "Bayern - Dortmund", "Juventus - Inter", "Porto - Benfica"
    ]

    rows = []
    for m in random.sample(sample_matches, k=5):
        home, away = m.split(" - ")
        rows.append({
            "match": m,
            "home_odds": round(random.uniform(1.75, 2.40), 2),
            "draw_odds": round(random.uniform(3.00, 3.70), 2),
            "away_odds": round(random.uniform(2.80, 3.60), 2),
            "total_volume": random.randint(15000, 80000),
            "kickoff": datetime.now().strftime("%H:%M:%S")
        })

    MARKET_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    MARKET_CACHE["markets"] = rows
    print(f"[MARKET READER] 🧩 Mock data active – {len(rows)} markets.")
    return MARKET_CACHE
