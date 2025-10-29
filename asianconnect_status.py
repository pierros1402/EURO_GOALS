# ==============================================
# asianconnect_status.py – v3
# EURO_GOALS – Asianconnect / Asianodds API Status Panel
# - Auto fallback ON/OFF όταν API είναι DOWN/OK
# - Logs + recent entries
# ==============================================

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ASIANCONNECT_API_KEY")
BASE_URL = "https://api.asianodds88.com"  # placeholder μέχρι να δοθούν πραγματικά endpoints

LOG_FILE = "EURO_GOALS_log.txt"
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "fallback_asianconnect.state")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _ensure_data_dir():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_event(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{_now()}] {msg}\n")
    # Επίσης εκτύπωση στην κονσόλα Render
    print(msg)

def get_recent_logs(n=5):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if "[ASIANCONNECT]" in ln]
        return lines[-n:] if lines else []
    except FileNotFoundError:
        return []

def _write_fallback_state(on: bool):
    _ensure_data_dir()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("ON" if on else "OFF")

def _read_fallback_state() -> bool:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip().upper() == "ON"
    except FileNotFoundError:
        return False

# --------------------------------------------------
# Core check
# --------------------------------------------------
def check_asianconnect_status():
    """
    Ελέγχει τη σύνδεση με το Asianodds API.
    Επιστρέφει JSON για το UI + ενημερώνει fallback state και log.
    """
    try:
        if not API_KEY:
            msg = "[ASIANCONNECT] ⚠️ No API key set in environment (.env) – Auto-Fallback ON"
            _write_fallback_state(True)
            log_event(msg)
            return {
                "status": "NO_KEY",
                "message": "API key not set in environment (.env)",
                "timestamp": _now(),
                "logs": get_recent_logs(),
                "fallback": True,
                "banner": "Asianconnect: NO KEY – Auto-Fallback ενεργό"
            }

        # Placeholder δοκιμαστικό endpoint (θα αλλαχθεί όταν δοθεί επίσημο)
        test_url = f"{BASE_URL}/status?apiKey={API_KEY}"
        resp = requests.get(test_url, timeout=10)

        if resp.status_code == 200:
            if _read_fallback_state():
                log_event("[ASIANCONNECT] ✅ API restored – Auto-Fallback OFF")
            _write_fallback_state(False)
            msg = "[ASIANCONNECT] ✅ API reachable"
            log_event(msg)
            return {
                "status": "OK",
                "message": "API reachable",
                "timestamp": _now(),
                "logs": get_recent_logs(),
                "fallback": False,
                "banner": ""
            }

        # Μη-200 απάντηση
        _write_fallback_state(True)
        msg = f"[ASIANCONNECT] ⚠️ API responded with code {resp.status_code} – Auto-Fallback ON"
        log_event(msg)
        return {
            "status": "DOWN",
            "message": f"API responded with code {resp.status_code}",
            "timestamp": _now(),
            "logs": get_recent_logs(),
            "fallback": True,
            "banner": "Asianconnect: DOWN – Auto-Fallback ενεργό"
        }

    except Exception as e:
        _write_fallback_state(True)
        msg = f"[ASIANCONNECT] ❌ Connection error: {e} – Auto-Fallback ON"
        log_event(msg)
        return {
            "status": "DOWN",
            "message": f"Connection error: {e}",
            "timestamp": _now(),
            "logs": get_recent_logs(),
            "fallback": True,
            "banner": "Asianconnect: DOWN – Auto-Fallback ενεργό"
        }
