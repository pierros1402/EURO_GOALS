# ==============================================
# MARKET READER MODULE (Stake Volume Detector)
# EURO_GOALS v6f – Mock Edition (Pinnacle + Betfair)
# ==============================================

import threading
import time
from datetime import datetime
import random

# -----------------------------
# Global cache
# -----------------------------
MARKET_CACHE = {
    "last_update": None,
    "markets": []
}

# -----------------------------
# Mock data sources (θα αντικατασταθούν με APIs)
# -----------------------------
def fetch_from_pinnacle():
    """
    Εικονικά δεδομένα Pinnacle – odds + volume
    """
    sample = [
        {
            "match": "Olympiacos - AEK",
            "market": "1X2",
            "home_odds": 2.10,
            "draw_odds": 3.45,
            "away_odds": 3.00,
            "home_volume": random.randint(50000, 150000),
            "draw_volume": random.randint(20000, 80000),
            "away_volume": random.randint(40000, 120000),
        },
        {
            "match": "PAOK - Aris",
            "market": "1X2",
            "home_odds": 2.05,
            "draw_odds": 3.20,
            "away_odds": 3.50,
            "home_volume": random.randint(60000, 180000),
            "draw_volume": random.randint(30000, 70000),
            "away_volume": random.randint(45000, 100000),
        }
    ]
    return sample


def fetch_from_betfair():
    """
    Εικονικά δεδομένα Betfair – back/lay volumes
    """
    sample = [
        {
            "match": "Manchester City - Liverpool",
            "market": "1X2",
            "home_odds": 1.90,
            "draw_odds": 3.60,
            "away_odds": 4.00,
            "home_volume": random.randint(200000, 400000),
            "draw_volume": random.randint(80000, 150000),
            "away_volume": random.randint(120000, 250000),
        }
    ]
    return sample


def fetch_from_sbobet():
    """
    Εικονικά δεδομένα SBOBET – Asian Handicap / Over-Under
    """
    sample = [
        {
            "match": "Panathinaikos - Lamia",
            "market": "Asian Handicap",
            "line": "-0.75",
            "home_odds": 1.93,
            "away_odds": 1.95,
            "home_volume": random.randint(40000, 100000),
            "away_volume": random.randint(40000, 90000),
        }
    ]
    return sample


# -----------------------------
# Core detector function
# -----------------------------
def detect_market_volumes():
    """
    Συλλέγει δεδομένα από πολλαπλές πηγές (mock)
    και υπολογίζει πού πέφτει το "βαρύ" στοίχημα.
    """
    print("[MARKET READER] 🔍 Checking volume data...")

    try:
        sources = []
        sources.extend(fetch_from_pinnacle())
        sources.extend(fetch_from_betfair())
        sources.extend(fetch_from_sbobet())

        # Υπολογισμός “dominant side” (ποιο σημείο έχει το μεγαλύτερο stake)
        results = []
        for s in sources:
            side_volumes = {
                "1": s.get("home_volume", 0),
                "X": s.get("draw_volume", 0),
                "2": s.get("away_volume", 0)
            }
            dominant = max(side_volumes, key=side_volumes.get)
            s["dominant_side"] = dominant
            s["total_volume"] = sum(side_volumes.values())
            results.append(s)

        MARKET_CACHE["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        MARKET_CACHE["markets"] = results

        print(f"[MARKET READER] ✅ Updated {len(results)} market entries.")
        return results

    except Exception as e:
        print("[MARKET READER] ❌ Error:", e)
        return []


# -----------------------------
# Auto-refresh thread
# -----------------------------
def auto_refresh(interval_minutes=5):
    def loop():
        while True:
            detect_market_volumes()
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"[MARKET READER] 🔁 Auto-refresh active (every {interval_minutes} minutes)")


# -----------------------------
# Getter for Render routes
# -----------------------------
def get_market_data():
    return {
        "last_update": MARKET_CACHE["last_update"],
        "markets": MARKET_CACHE["markets"]
    }


# -----------------------------
# Start background auto-refresh
# -----------------------------
auto_refresh(5)
