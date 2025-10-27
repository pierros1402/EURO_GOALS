# ==============================================
# EURO_GOALS – Render Monitor v3
# ==============================================
# Ελέγχει περιοδικά το health status του EURO_GOALS
# και κάνει αυτόματο restart στο Render αν χρειαστεί.
# Ειδοποιεί ΜΟΝΟ σε περίπτωση προβλήματος ή επιτυχούς επαναφοράς.
# ==============================================

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from win10toast import ToastNotifier
from modules.health_check import check_health, log_message

# --------------------------------------------------
# 1. Φόρτωση μεταβλητών περιβάλλοντος (.env)
# --------------------------------------------------
load_dotenv()
API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
HEALTH_URL = os.getenv("EUROGOALS_HEALTH_URL", "https://eurogoals.onrender.com/health")

# --------------------------------------------------
# 2. Ρυθμίσεις
# --------------------------------------------------
CHECK_INTERVAL = 600   # Έλεγχος κάθε 10 λεπτά (600 δευτ.)
MAX_RETRIES = 3        # Πόσες φορές να δοκιμάσει πριν επανεκκίνηση
RETRY_DELAY = 15       # Δευτερόλεπτα μεταξύ προσπαθειών

toaster = ToastNotifier()


def restart_render_service():
    """Κάνει restart το Render service μέσω API."""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {"clearCache": False}

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            log_message("[RENDER] 🔁 Restart triggered successfully.")
            toaster.show_toast("EURO_GOALS", "🔁 Το Render service επανεκκινήθηκε επιτυχώς.", duration=6)
            return True
        else:
            log_message(f"[RENDER] ❌ Restart failed ({response.status_code}): {response.text}")
            toaster.show_toast("EURO_GOALS", "❌ Αποτυχία επανεκκίνησης Render service.", duration=6)
            return False
    except Exception as e:
        log_message(f"[RENDER] ⚠️ Exception during restart: {e}")
        return False


def monitor_loop():
    """Κεντρική λούπα παρακολούθησης EURO_GOALS."""
    log_message("🔍 [MONITOR] Starting Render Monitor v3...")
    toaster.show_toast("EURO_GOALS", "🟢 Παρακολούθηση Render ξεκίνησε.", duration=5)

    while True:
        try:
            healthy = False
            for attempt in range(1, MAX_RETRIES + 1):
                if check_health(HEALTH_URL):
                    healthy = True
                    break
                else:
                    log_message(f"[MONITOR] Retry {attempt}/{MAX_RETRIES} failed, waiting {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)

            if not healthy:
                toaster.show_toast("EURO_GOALS", "🔴 Πρόβλημα ανιχνεύτηκε – γίνεται επανεκκίνηση...", duration=8)
                log_message("[MONITOR] 🚨 Health check failed repeatedly. Initiating Render restart.")
                restart_render_service()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            log_message(f"[MONITOR] ❌ Unexpected exception in loop: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_loop()
