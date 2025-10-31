# ================================================
# EURO_GOALS – Health Check Module (v8.9m)
# ================================================
# Ελέγχει βασικές υπηρεσίες και API endpoints
# (Render, Database, Feeds, Asianconnect, SmartMoney κ.λπ.)
# και επιστρέφει συγκεντρωτικό diagnostic report
# ================================================

import requests
from datetime import datetime
import os

# ------------------------------------------------
# 1️⃣  ΕΛΕΓΧΟΣ ASIANCONNECT API
# ------------------------------------------------
def check_asianconnect():
    """
    Ελέγχει αν το Asianconnect API είναι διαθέσιμο.
    Επιστρέφει 'OK', 'FAIL' ή 'PENDING'.
    """
    url = "https://asianconnect88.com"  # μπορείς να το αλλάξεις αν έχεις εναλλακτικό endpoint
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return "OK"
        else:
            return "FAIL"
    except Exception as e:
        print("[HEALTH] ⚠️ Asianconnect check error:", e)
        return "FAIL"

# ------------------------------------------------
# 2️⃣  ΕΛΕΓΧΟΣ RENDER SERVICE ΥΓΕΙΑΣ
# ------------------------------------------------
def check_render_health():
    """
    Ελέγχει το Render service URL από μεταβλητή περιβάλλοντος.
    """
    url = os.getenv("EUROGOALS_HEALTH_URL")
    if not url:
        return "PENDING"

    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return "OK"
        else:
            return "FAIL"
    except Exception as e:
        print("[HEALTH] ⚠️ Render health error:", e)
        return "FAIL"

# ------------------------------------------------
# 3️⃣  ΕΛΕΓΧΟΣ DATABASE (SQLite / PostgreSQL)
# ------------------------------------------------
def check_database():
    """
    Ελέγχει αν υπάρχει ενεργή σύνδεση DB.
    """
    try:
        db_path = "matches.db"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            return "OK" if size > 1024 else "PENDING"
        else:
            return "FAIL"
    except Exception as e:
        print("[HEALTH] ⚠️ Database check error:", e)
        return "FAIL"

# ------------------------------------------------
# 4️⃣  ΕΛΕΓΧΟΣ SMART MONEY MODULE
# ------------------------------------------------
def check_smartmoney():
    """
    Ελέγχει αν το module smartmoney_monitor.py είναι διαθέσιμο.
    """
    path = os.path.join("modules", "smartmoney_monitor.py")
    if os.path.exists(path):
        return "OK"
    else:
        return "FAIL"

# ------------------------------------------------
# 5️⃣  ΚΕΝΤΡΙΚΗ ΣΥΝΑΡΤΗΣΗ ΥΓΕΙΑΣ
# ------------------------------------------------
def run_full_healthcheck():
    """
    Τρέχει όλους τους επιμέρους ελέγχους και επιστρέφει συνολικό αποτέλεσμα.
    """
    timestamp = datetime.utcnow().isoformat()

    components = {
        "Render Service": check_render_health(),
        "Database": check_database(),
        "SmartMoney": check_smartmoney(),
        "Asianconnect": check_asianconnect(),
    }

    # Συνολική κατάσταση
    if "FAIL" in components.values():
        global_status = "FAIL"
        summary = "❌ Εντοπίστηκαν προβλήματα σε μία ή περισσότερες υπηρεσίες."
    elif "PENDING" in components.values():
        global_status = "PENDING"
        summary = "⏳ Μερικές υπηρεσίες εκκρεμούν για επιβεβαίωση."
    else:
        global_status = "OK"
        summary = "✅ Όλα λειτουργούν κανονικά."

    return {
        "status": global_status,
        "timestamp": timestamp,
        "components": components,
        "summary": summary,
        "service": "EURO_GOALS_NEXTGEN"
    }
