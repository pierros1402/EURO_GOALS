# =============================================================
# data_router.py – Auto Fallback Controller (v8.9d)
# =============================================================

import json
from datetime import datetime

# -------------------------------------------------------------
# Απλή λειτουργία καταγραφής γεγονότων
# -------------------------------------------------------------
def log_event(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log_dualsource.txt", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")
    print(f"[EURO_GOALS] {message}")

# -------------------------------------------------------------
# Auto feed router – ελέγχει αν χρειάζεται fallback
# -------------------------------------------------------------
def get_data_auto():
    """
    Προσομοίωση έξυπνου ελέγχου δεδομένων.
    Αν αποτύχει η κύρια πηγή (flashscore), 
    μεταβαίνει σε δευτερεύουσα (sofascore).
    """
    try:
        with open("feeds.json", "r", encoding="utf-8") as f:
            feeds = json.load(f).get("feeds", [])
    except FileNotFoundError:
        log_event("⚠️ Δεν βρέθηκε feeds.json")
        return None

    # Προτεραιότητα flashscore -> sofascore -> openfootball
    flash = next((f for f in feeds if f["alias"] == "flashscore"), None)
    sofa = next((f for f in feeds if f["alias"] == "sofascore"), None)
    backup = next((f for f in feeds if f["alias"] == "openfootball"), None)

    # Simulate status check
    if flash and flash["status"] == "OK":
        log_event("✅ Κύρια πηγή flashscore ενεργή.")
        return {"source": "flashscore"}

    elif sofa and sofa["status"] == "OK":
        log_event("⚠️ AUTO-FALLBACK → Μετάβαση από flashscore σε sofascore")
        return {"source": "sofascore"}

    elif backup:
        log_event("🔄 Όλες οι πηγές απέτυχαν, χρήση openfootball (backup).")
        return {"source": "openfootball"}

    log_event("❌ Καμία διαθέσιμη πηγή.")
    return None
