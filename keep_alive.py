# ==============================================
# EURO_GOALS NextGen – Render Keep-Alive System
# ==============================================

import os
import time
import threading
import requests

# Αν θέλεις να αλλάξεις το διάστημα μεταξύ των checks (σε λεπτά)
INTERVAL_MINUTES = 10

# Το Render URL της πλατφόρμας σου
URL = "https://euro-goals-nextgen.onrender.com"

def keep_alive():
    while True:
        try:
            print("[KEEP-ALIVE] 🌍 Sending ping to:", URL)
            r = requests.get(URL, timeout=10)
            if r.status_code == 200:
                print("[KEEP-ALIVE] ✅ Service is awake and healthy")
            else:
                print(f"[KEEP-ALIVE] ⚠️ Unexpected status: {r.status_code}")
        except Exception as e:
            print("[KEEP-ALIVE] ❌ Error:", e)
        time.sleep(INTERVAL_MINUTES * 60)

# Εκκίνηση του keep-alive σε ξεχωριστό thread
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()
