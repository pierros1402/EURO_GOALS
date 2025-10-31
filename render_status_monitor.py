# ===========================================================
# EURO_GOALS Render Status Monitor (Final with Logging)
# ===========================================================
# Ελέγχει την κατάσταση του Render service EURO_GOALS
# μέσω του Render API και της HEALTH URL.
# Καταγράφει αποτελέσματα σε logs/render_monitor_log.txt
# ===========================================================

import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from win10toast import ToastNotifier

# -----------------------------------------------------------
# 1. Φόρτωση .env μεταβλητών
# -----------------------------------------------------------
load_dotenv()

API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
HEALTH_URL = os.getenv("RENDER_HEALTH_URL")

# -----------------------------------------------------------
# 2. Ρυθμίσεις / Δομή φακέλων logs
# -----------------------------------------------------------
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "render_monitor_log.txt")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_message(message: str):
    """Αποθηκεύει μήνυμα με timestamp στο log αρχείο"""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
    print(f"{timestamp} {message}")

# -----------------------------------------------------------
# 3. Ειδοποιήσεις Windows
# -----------------------------------------------------------
toaster = ToastNotifier()

def toast(title, message):
    """Απλή ειδοποίηση στα Windows"""
    try:
        toaster.show_toast(title, message, duration=5, threaded=True)
    except Exception as e:
        print(f"[TOAST ERROR] {e}")

# -----------------------------------------------------------
# 4. Έλεγχος Render health
# -----------------------------------------------------------
def check_render_health():
    if not HEALTH_URL or HEALTH_URL.strip() == "":
        log_message("❌ No HEALTH_URL defined in .env")
        return None, None

    try:
        resp = requests.get(HEALTH_URL, timeout=10)
        return resp.status_code, resp.text.strip()
    except Exception as e:
        log_message(f"⚠️ Connection error: {e}")
        return None, None

# -----------------------------------------------------------
# 5. Επανεκκίνηση υπηρεσίας Render (αν χρειάζεται)
# -----------------------------------------------------------
def restart_render_service():
    try:
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"clearCache": True}
        r = requests.post(url, headers=headers, json=data)

        if r.status_code == 401:
            log_message("⚠️ Restart failed (401): Unauthorized")
            toast("EURO_GOALS Render", "Restart failed: Unauthorized (401)")
        elif r.status_code in [200, 201]:
            log_message("🔄 Restart triggered successfully.")
            toast("EURO_GOALS Render", "Service restart triggered.")
        else:
            log_message(f"⚠️ Restart failed ({r.status_code}): {r.text}")
    except Exception as e:
        log_message(f"❌ Error triggering restart: {e}")

# -----------------------------------------------------------
# 6. Κύρια ρουτίνα ελέγχου
# -----------------------------------------------------------
def main():
    print("==========================================")
    print("   EURO_GOALS - Render Status Monitor")
    print("   Checking Render service health...")
    print("==========================================\n")

    log_message("🟢 EURO_GOALS Render Monitor started.")
    log_message(f"🌐 Health URL: {HEALTH_URL if HEALTH_URL else 'None'}")

    while True:
        log_message("🔵 Checking Render Health...")
        status, content = check_render_health()

        if status == 200:
            log_message("✅ Service is healthy and running.")
            toast("EURO_GOALS Render", "Service is healthy ✅")
        elif status:
            log_message(f"⚠️ Service returned status {status}. Content: {content[:120]}")
            toast("EURO_GOALS Render", f"Service warning ({status}) ⚠️")
            restart_render_service()
        else:
            log_message("❌ Service unreachable or invalid response.")
            toast("EURO_GOALS Render", "Service unreachable ❌")
            restart_render_service()

        log_message("⏰ Next check in 15 minutes...\n")
        time.sleep(900)  # 15 λεπτά

# -----------------------------------------------------------
if __name__ == "__main__":
    main()
