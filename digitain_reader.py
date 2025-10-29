# ============================================================
# DIGITAIN READER MODULE (Smart Money Detector)
# v1.0 – Mock + API-ready
# ============================================================
# Περιγραφή:
# - Τραβά δεδομένα από το Digitain API (όταν υπάρξει demo key)
# - Ενδιάμεσα λειτουργεί σε "Mock Mode"
# - Υπολογίζει Money Flow Index (0–100)
# - Επιστρέφει λίστα ύποπτων αγώνων για το SmartMoney panel
# ============================================================

import os
import random
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DIGITAIN_API_URL = os.getenv("DIGITAIN_API_URL", "")
DIGITAIN_API_KEY = os.getenv("DIGITAIN_API_KEY", "")
MOCK_MODE = not (DIGITAIN_API_URL and DIGITAIN_API_KEY)

LOG_FILE = "logs/smartmoney_log.txt"

# ------------------------------------------------------------
# Helper: Καταγραφή συμβάντων
# ------------------------------------------------------------
def log_event(message: str):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    print(message)


# ------------------------------------------------------------
# Υπολογισμός Money Flow Index (0–100)
# ------------------------------------------------------------
def calculate_flow_change(old_odds: float, new_odds: float) -> int:
    if not old_odds or not new_odds:
        return random.randint(30, 70)
    diff = old_odds - new_odds
    flow = int(50 + (diff * 200))  # όσο πιο πολύ πέφτει, τόσο πιο μεγάλο flow
    return max(0, min(flow, 100))


# ------------------------------------------------------------
# Mock Data Generator – χρησιμοποιείται αν δεν υπάρχει API key
# ------------------------------------------------------------
def generate_mock_data():
    sample_matches = [
        ("Urawa Reds", "Kawasaki Frontale"),
        ("Johor DT", "BG Pathum United"),
        ("Buriram Utd", "Port FC"),
        ("Al Hilal", "Al Nassr"),
        ("Guangzhou FC", "Shanghai SIPG"),
    ]
    data = []
    for home, away in sample_matches:
        flow_ah = random.randint(40, 95)
        flow_ou = random.randint(30, 90)
        data.append({
            "match": f"{home} vs {away}",
            "asian_handicap": f"{random.choice(['-0.5', '+0.5', '-0.25', '+0.25'])}",
            "ah_flow": flow_ah,
            "over_under": random.choice(["2.25", "2.5", "3.0"]),
            "ou_flow": flow_ou,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
    return data


# ------------------------------------------------------------
# Κύρια συνάρτηση: Ανάγνωση από API ή Mock
# ------------------------------------------------------------
def get_digitain_smartmoney():
    try:
        if MOCK_MODE:
            log_event("[DIGITAIN] 🧩 Mock mode ενεργό – χρησιμοποιούνται προσομοιωμένα δεδομένα.")
            matches = generate_mock_data()
        else:
            headers = {"Authorization": f"Bearer {DIGITAIN_API_KEY}"}
            resp = requests.get(f"{DIGITAIN_API_URL}/odds", headers=headers, timeout=15)
            if resp.status_code != 200:
                raise Exception(f"API error {resp.status_code}")
            raw_data = resp.json()
            matches = []

            # Μετατροπή API → simplified structure
            for m in raw_data.get("data", [])[:10]:
                home = m.get("home_team")
                away = m.get("away_team")
                ah_old = float(m.get("ah_old", 0))
                ah_new = float(m.get("ah_new", 0))
                ou_old = float(m.get("ou_old", 0))
                ou_new = float(m.get("ou_new", 0))
                matches.append({
                    "match": f"{home} vs {away}",
                    "asian_handicap": m.get("ah_line", "-0.5"),
                    "ah_flow": calculate_flow_change(ah_old, ah_new),
                    "over_under": m.get("ou_line", "2.5"),
                    "ou_flow": calculate_flow_change(ou_old, ou_new),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                })

        # Φιλτράρουμε "ύποπτα" με flow > 75
        suspicious = [m for m in matches if m["ah_flow"] > 75 or m["ou_flow"] > 75]

        for m in suspicious:
            log_event(f"[SMART MONEY] ⚠️ {m['match']} | AH {m['asian_handicap']}={m['ah_flow']}% | O/U {m['over_under']}={m['ou_flow']}%")

        return suspicious

    except Exception as e:
        log_event(f"[DIGITAIN] ❌ Σφάλμα: {e}")
        return []


# ------------------------------------------------------------
# Εφόσον τρέξει standalone
# ------------------------------------------------------------
if __name__ == "__main__":
    print("\n=== DIGITAIN SMART MONEY DETECTOR ===")
    suspicious_matches = get_digitain_smartmoney()
    print(json.dumps(suspicious_matches, indent=2, ensure_ascii=False))
