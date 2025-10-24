# ==============================================
# SMART MONEY REFINER v8
# Ανίχνευση “έξυπνου χρήματος” & αυτόματη ειδοποίηση
# ==============================================

import requests
import json
from datetime import datetime
from EURO_GOALS_v8 import add_alert_direct  # ✅ νέα εισαγωγή για απευθείας ειδοποιήσεις

def detect_smart_money():
    """
    Ανιχνεύει ύποπτες μεταβολές αποδόσεων από κύριες πηγές (Pinnacle, SBOBET, 188BET)
    και δημιουργεί ειδοποίηση στην βάση δεδομένων.
    """
    print("[SMART MONEY] 🔍 Checking for suspicious odds movements...")

    try:
        # 🔸 Προσωρινές ψεύτικες πηγές (θα αντικατασταθούν με κανονικά APIs)
        sources = [
            {"book": "Pinnacle", "match": "Chelsea vs Arsenal", "old": 1.92, "new": 1.78},
            {"book": "SBOBET", "match": "Barcelona vs Atletico", "old": 2.05, "new": 1.98}
        ]

        detected = []

        for s in sources:
            # Αν η απόδοση έπεσε πάνω από 0.10 → Smart Money alert
            if s["old"] - s["new"] >= 0.10:
                change = round(s["old"] - s["new"], 2)
                msg = f"Smart Money Detected – {s['book']}: {s['match']} odds moved {s['old']} → {s['new']} (Δ-{change})"
                detected.append(msg)

                # ✅ Δημιουργεί alert απευθείας στη βάση
                add_alert_direct(msg, "SmartMoney", "warning")
                print(f"[SMART MONEY] ⚠️ {msg}")

        if not detected:
            print("[SMART MONEY] ✅ No major movements detected.")
        else:
            print(f"[SMART MONEY] {len(detected)} Smart Money signals stored.")

        return {"status": "ok", "count": len(detected), "alerts": detected}

    except Exception as e:
        print(f"[SMART MONEY] ❌ Error: {e}")
        add_alert_direct(f"Smart Money module error: {e}", "SmartMoney", "danger")
        return {"status": "error", "message": str(e)}

# ------------------------------------------------
# Manual test entry point (for local testing)
# ------------------------------------------------
if __name__ == "__main__":
    result = detect_smart_money()
    print(json.dumps(result, indent=2, ensure_ascii=False))
