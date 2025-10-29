# ==============================================
# asianconnect_status.py – v2
# EURO_GOALS – Asianconnect / Asianodds API Status Panel
# ==============================================

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ASIANCONNECT_API_KEY")
BASE_URL = "https://api.asianodds88.com"  # placeholder

LOG_FILE = "EURO_GOALS_log.txt"

def log_event(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def get_recent_logs(n=5):
    """Επιστρέφει τα τελευταία n log entries που περιέχουν [ASIANCONNECT]"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if "[ASIANCONNECT]" in line]
        return lines[-n:] if lines else []
    except FileNotFoundError:
        return []

def check_asianconnect_status():
    """Ελέγχει τη σύνδεση με το Asianconnect/Asianodds API"""
    try:
        if not API_KEY:
            msg = "[ASIANCONNECT] ⚠️ No API key set in environment (.env)"
            log_event(msg)
            return {
                "status": "NO_KEY",
                "message": "API key not set in environment (.env)",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "logs": get_recent_logs()
            }

        test_url = f"{BASE_URL}/status?apiKey={API_KEY}"
        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            msg = f"[ASIANCONNECT] ✅ API reachable ({datetime.now().strftime('%H:%M:%S')})"
            status = "OK"
        else:
            msg = f"[ASIANCONNECT] ⚠️ API responded with code {response.status_code}"
            status = "DOWN"

        log_event(msg)

        return {
            "status": status,
            "message": msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logs": get_recent_logs()
        }

    except Exception as e:
        msg = f"[ASIANCONNECT] ❌ Connection error: {e}"
        log_event(msg)
        return {
            "status": "DOWN",
            "message": msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logs": get_recent_logs()
        }
