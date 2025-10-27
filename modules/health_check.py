# ==============================================
# EURO_GOALS – Health Check Module
# ==============================================
# Ελέγχει αν η πλατφόρμα EURO_GOALS στο Render
# απαντά σωστά στο /health endpoint.
# Επιστρέφει True (OK) ή False (πρόβλημα)
# ==============================================

import requests
from datetime import datetime

def check_health(url: str, timeout: int = 8) -> bool:
    """
    Ελέγχει τη διαθεσιμότητα του EURO_GOALS μέσω του endpoint /health.
    Αν η απόκριση είναι 200 και περιέχει 'ok', επιστρέφει True.
    Αν υπάρξει σφάλμα ή καθυστέρηση, επιστρέφει False.
    """
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200 and "ok" in response.text.lower():
            log_message(f"[HEALTH] ✅ OK ({response.status_code}) {url}")
            return True
        else:
            log_message(f"[HEALTH] ⚠️ Unexpected response: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"[HEALTH] ❌ Exception: {e}")
        return False


def log_message(message: str):
    """Γράφει μήνυμα στο EURO_GOALS_log.txt με timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("EURO_GOALS_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
    print(message)
