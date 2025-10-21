# ==============================================
# KEEP ALIVE PINGER
# EURO_GOALS v6f – Keeps Render always awake
# ==============================================

import threading
import time
import requests

PING_URL = "https://euro-goals-v6f.onrender.com/ping"

def keep_alive():
    def loop():
        while True:
            try:
                response = requests.get(PING_URL, timeout=10)
                print(f"[KEEP ALIVE] 🔁 Pinged Render: {response.status_code}")
            except Exception as e:
                print("[KEEP ALIVE] ❌ Error:", e)
            time.sleep(600)  # κάθε 10 λεπτά
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print("[KEEP ALIVE] 🟢 Auto-ping thread active (every 10 min)")

# Ξεκινά αυτόματα
keep_alive()
