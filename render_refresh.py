# ==============================================
# EURO_GOALS – Render Auto-Refresh (v3 – fixed)
# ==============================================
# Επανεκκινεί το Render service EURO_GOALSv7.9
# χρησιμοποιώντας έγκυρο API Key και Service ID
# ==============================================

import os
import requests
from dotenv import load_dotenv
from win10toast import ToastNotifier

# --------------------------------------------------
# 1. Φόρτωση .env
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")

toaster = ToastNotifier()

print("[RENDER] 🚀 Εκκίνηση auto-refresh...")

if not API_KEY or not SERVICE_ID:
    print("[RENDER] ❌ Δεν βρέθηκαν μεταβλητές API στο .env!")
    toaster.show_toast(
        "EURO_GOALS Render ❌",
        "Δεν βρέθηκαν API στοιχεία (.env).",
        duration=6
    )
    raise SystemExit()

# --------------------------------------------------
# 2. Ενέργεια επανεκκίνησης στο Render (με έλεγχο owner)
# --------------------------------------------------
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

payload = {
    "clearCache": False,
    "triggerReason": "Manual refresh from EURO_GOALS desktop"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("[RENDER] ✅ Επιτυχής ανανέωση Render service.")
        toaster.show_toast(
            "EURO_GOALS Render ✅",
            "Η υπηρεσία Render ανανεώθηκε επιτυχώς!",
            duration=6
        )
    elif response.status_code == 401:
        print("[RENDER] ❌ 401 Unauthorized – πιθανόν API key από λάθος workspace.")
        print("➡ Έλεγξε στο Render αν το key ανήκει στο ίδιο account με το project.")
        toaster.show_toast(
            "EURO_GOALS Render ❌",
            "Λάθος API Key ή μη εξουσιοδοτημένο αίτημα (401).",
            duration=6
        )
    elif response.status_code == 403:
        print("[RENDER] ❌ 403 Forbidden – το key δεν έχει δικαιώματα για αυτό το service.")
        toaster.show_toast(
            "EURO_GOALS Render ❌",
            "Το API key δεν έχει δικαιώματα για αυτό το service (403).",
            duration=6
        )
    else:
        print(f"[RENDER] ⚠️ Σφάλμα {response.status_code}: {response.text}")
        toaster.show_toast(
            "EURO_GOALS Render ⚠️",
            f"Σφάλμα {response.status_code} κατά την ανανέωση.",
            duration=6
        )

except Exception as e:
    print("[RENDER] ❌ Εξαίρεση:", e)
    toaster.show_toast(
        "EURO_GOALS Render ❌",
        "Απροσδόκητο σφάλμα κατά την εκτέλεση.",
        duration=6
    )

print("[RENDER] 💤 Ολοκλήρωση διαδικασίας.\n")
