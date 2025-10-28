# ==============================================
# EURO_GOALS – Status Monitor
# ==============================================
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Έλεγχος κάθε module
# ============================================================
def check_status():
    result = []
    now = datetime.now().strftime("%H:%M")

    # 1️⃣ Core
    result.append({
        "module": "⚙️ Core",
        "status": "🟢 Online",
        "last_check": now
    })

    # 2️⃣ Football-Data.org
    fd_key = os.getenv("FOOTBALLDATA_API_KEY")
    if fd_key:
        try:
            r = requests.get("https://api.football-data.org/v4/status",
                             headers={"X-Auth-Token": fd_key}, timeout=5)
            if r.status_code in [200, 403]:  # 403 = free plan OK
                result.append({"module": "🏆 Football-Data.org", "status": "🟢 Active", "last_check": now})
            else:
                result.append({"module": "🏆 Football-Data.org", "status": "🔴 Error", "last_check": now})
        except:
            result.append({"module": "🏆 Football-Data.org", "status": "🔴 Unreachable", "last_check": now})
    else:
        result.append({"module": "🏆 Football-Data.org", "status": "⚪ No key", "last_check": now})

    # 3️⃣ API-Football
    af_key = os.getenv("APIFOOTBALL_API_KEY")
    if af_key:
        try:
            r = requests.get("https://v3.football.api-sports.io/status",
                             headers={"x-apisports-key": af_key}, timeout=5)
            if r.status_code == 200:
                result.append({"module": "📊 API-Football", "status": "🟢 Connected", "last_check": now})
            else:
                result.append({"module": "📊 API-Football", "status": "🔴 Error", "last_check": now})
        except:
            result.append({"module": "📊 API-Football", "status": "🔴 Unreachable", "last_check": now})
    else:
        result.append({"module": "📊 API-Football", "status": "⚪ No key", "last_check": now})

    # 4️⃣ BeSoccer
    bs_key = os.getenv("BESOCCER_API_KEY")
    if bs_key:
        result.append({"module": "📱 BeSoccer", "status": "🟡 Pending", "last_check": now})
    else:
        result.append({"module": "📱 BeSoccer", "status": "⚪ No key", "last_check": now})

    # 5️⃣ Smart Money Detector
    result.append({"module": "💰 Smart Money Detector", "status": "🟡 Idle", "last_check": now})

    return result
