# ============================================================
# ASIANCONNECT STATUS MODULE – EURO_GOALS v8.1
# ============================================================
# Ελέγχει την κατάσταση σύνδεσης με το Asianconnect / Asianodds API
# και ενημερώνει το log + το dashboard panel
# ============================================================

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ASIAN_API_URL = os.getenv("ASIAN_API_URL", "https://asianodds88.com/api/status")  # placeholder
ASIAN_API_KEY = os.getenv("ASIAN_API_KEY", "")
LOG_FILE = "EURO_GOALS_log.txt"


def log_message(message: str):
    """Καταγραφή μηνύματος στο EURO_GOALS_log.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def check_asianconnect_status():
    """
    Επιστρέφει dict με την κατάσταση API:
    {"status": "ok" | "error", "message": "..."}
    """
    try:
        if not ASIAN_API_KEY:
            msg = "⚠️ No API key defined for Asianconnect."
            log_message("[ASIANCONNECT] " + msg)
            return {"status": "error", "message": msg}

        headers = {"Authorization": f"Bearer {ASIAN_API_KEY}"}
        response = requests.get(ASIAN_API_URL, headers=headers, timeout=5)

        if response.status_code == 200:
            msg = "✅ Asianconnect API reachable."
            log_message("[ASIANCONNECT] " + msg)
            return {"status": "ok", "message": msg}
        else:
            msg = f"❌ Asianconnect API responded with status {response.status_code}"
            log_message("[ASIANCONNECT] " + msg)
            return {"status": "error", "message": msg}

    except Exception as e:
        msg = f"❌ Asianconnect API error: {e}"
        log_message("[ASIANCONNECT] " + msg)
        return {"status": "error", "message": msg}


if __name__ == "__main__":
    result = check_asianconnect_status()
    print(result)
