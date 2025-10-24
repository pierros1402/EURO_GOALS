# ==============================================
# LIVE FEEDS ALERTS MODULE (EURO_GOALS v8)
# ==============================================
# Ανιχνεύει αλλαγές από Flashscore / Sofascore
# (π.χ. Goal, Red Card, Start/End)
# και επιστρέφει alerts για την πλατφόρμα
# ==============================================

import time
import random
from datetime import datetime

# ------------------------------------------------
# Εσωτερικός buffer τελευταίων καταστάσεων
# ------------------------------------------------
last_state = {}

# ------------------------------------------------
# Συνάρτηση ανίχνευσης αλλαγών live δεδομένων
# ------------------------------------------------
def detect_live_alerts():
    """
    Ανιχνεύει γεγονότα (goal, red card, start, end)
    με βάση ψεύτικα δεδομένα mock μέχρι να ενεργοποιηθούν τα API.
    """
    print("[LIVE FEEDS] 🔍 Checking for live match updates...")
    alerts = []

    # Προσωρινά mock δεδομένα (προσομοίωση Flashscore/Sofascore)
    sample_matches = [
        {"match": "Real Madrid vs Barcelona", "minute": 64, "home": 2, "away": 1, "status": "LIVE"},
        {"match": "Juventus vs Milan", "minute": 72, "home": 1, "away": 1, "status": "LIVE"},
        {"match": "PAOK vs Olympiacos", "minute": 80, "home": 3, "away": 2, "status": "LIVE"},
    ]

    # Ελέγχει για αλλαγές έναντι της προηγούμενης κατάστασης
    for m in sample_matches:
        match_id = m["match"]
        prev = last_state.get(match_id)

        # Αν δεν υπήρχε προηγούμενη εγγραφή → νέα έναρξη
        if not prev:
            alerts.append({
                "type": "status",
                "message": f"🔵 Match started – {m['match']} (0’)",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            # Αν σκόραρε ομάδα
            if (m["home"], m["away"]) != (prev["home"], prev["away"]):
                alerts.append({
                    "type": "goal",
                    "message": f"⚽ Goal! {m['match']} ({m['home']}–{m['away']} at {m['minute']}’)",
                    "timestamp": datetime.utcnow().isoformat()
                })
            # Αν αλλάξει status (π.χ. λήξη)
            if m["status"] != prev["status"]:
                alerts.append({
                    "type": "status",
                    "message": f"🔁 Status changed: {m['match']} → {m['status']}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Τυχαίο γεγονός Red Card (demo)
        if random.random() < 0.1:
            alerts.append({
                "type": "card",
                "message": f"🟥 Red Card – {m['match']} (minute {m['minute']})",
                "timestamp": datetime.utcnow().isoformat()
            })

        # Ενημερώνει την τρέχουσα κατάσταση
        last_state[match_id] = m

    print(f"[LIVE FEEDS] ✅ {len(alerts)} new alerts detected.")
    return {"status": "ok", "count": len(alerts), "alerts": alerts}

# ------------------------------------------------
# Συνάρτηση δοκιμής
# ------------------------------------------------
if __name__ == "__main__":
    print("Running Live Feeds Alerts test mode...")
    while True:
        result = detect_live_alerts()
        print(result)
        time.sleep(10)
