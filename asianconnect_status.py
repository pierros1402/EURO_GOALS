# ============================================================
# asianconnect_status.py – v4
# EURO_GOALS – Asianconnect API Monitor + Auto-Recovery
# ============================================================

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ASIANCONNECT_API_KEY")
BASE_URL = "https://api.asianodds88.com"     # placeholder

LOG_FILE = "EURO_GOALS_log.txt"
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "fallback_asianconnect.state")
LAST_GOOD_FILE = os.path.join(DATA_DIR, "asianconnect_last_good.txt")

# ------------------------------------------------------------
def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_event(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{_now()}] {msg}\n")
    print(msg)

def _write_state(on: bool):
    _ensure_data_dir()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("ON" if on else "OFF")

def _read_state() -> bool:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip().upper() == "ON"
    except FileNotFoundError:
        return False

def _write_last_good():
    _ensure_data_dir()
    with open(LAST_GOOD_FILE, "w", encoding="utf-8") as f:
        f.write(_now())

def _read_last_good() -> str:
    try:
        with open(LAST_GOOD_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "—"

def get_recent_logs(n=6):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if "[ASIANCONNECT]" in ln]
        return lines[-n:] if lines else []
    except FileNotFoundError:
        return []

# ------------------------------------------------------------
def check_asianconnect_status():
    """
    Ελέγχει το Asianodds API – χειρίζεται fallback, recovery και logging.
    """
    _ensure_data_dir()
    try:
        if not API_KEY:
            _write_state(True)
            msg = "[ASIANCONNECT] ⚠️ No API key – Auto-Fallback ON"
            log_event(msg)
            return {
                "status": "NO_KEY",
                "message": "API key not set in environment (.env)",
                "timestamp": _now(),
                "logs": get_recent_logs(),
                "fallback": True,
                "banner": "Asianconnect: NO KEY – Auto-Fallback ενεργό",
                "last_good": _read_last_good(),
            }

        # --- δοκιμαστικό endpoint (mock) ---
        test_url = f"{BASE_URL}/status?apiKey={API_KEY}"
        resp = requests.get(test_url, timeout=8)

        if resp.status_code == 200:
            if _read_state():
                log_event("[ASIANCONNECT] ✅ API RESTORED – Auto-Fallback OFF")
            _write_state(False)
            _write_last_good()
            log_event("[ASIANCONNECT] ✅ API reachable")
            return {
                "status": "OK",
                "message": "API reachable",
                "timestamp": _now(),
                "logs": get_recent_logs(),
                "fallback": False,
                "banner": "",
                "last_good": _read_last_good(),
            }

        _write_state(True)
        msg = f"[ASIANCONNECT] ⚠️ API responded {resp.status_code} – Auto-Fallback ON"
        log_event(msg)
        return {
            "status": "DOWN",
            "message": f"API responded {resp.status_code}",
            "timestamp": _now(),
            "logs": get_recent_logs(),
            "fallback": True,
            "banner": "Asianconnect: DOWN – Auto-Fallback ενεργό",
            "last_good": _read_last_good(),
        }

    except Exception as e:
        _write_state(True)
        msg = f"[ASIANCONNECT] ❌ Connection error: {e} – Auto-Fallback ON"
        log_event(msg)
        return {
            "status": "DOWN",
            "message": f"Connection error: {e}",
            "timestamp": _now(),
            "logs": get_recent_logs(),
            "fallback": True,
            "banner": "Asianconnect: DOWN – Auto-Fallback ενεργό",
            "last_good": _read_last_good(),
        }
