# =============================================================
# EURO_GOALS – Data Router (Auto-Fallback System)
# =============================================================
# Επιτρέπει αυτόματη εναλλαγή μεταξύ πηγών (Flashscore, Sofascore, κ.λπ.)
# όταν μια πηγή δεν ανταποκρίνεται.
# Καταγράφει τα αποτελέσματα σε log_dualsource.txt
# =============================================================

import json, time, requests, random
from datetime import datetime

FEEDS_FILE = "feeds.json"
LOG_FILE = "log_dualsource.txt"

def log_event(message: str):
    """Γράφει γεγονότα στο αρχείο καταγραφής"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {message}\n")
    print(message)


def load_feeds():
    """Φόρτωση feeds.json"""
    try:
        with open(FEEDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("feeds", [])
    except Exception as e:
        log_event(f"❌ Σφάλμα ανάγνωσης feeds.json: {e}")
        return []


def save_feeds(feeds):
    """Αποθήκευση feeds.json (αν αλλάξει ενεργή πηγή)"""
    with open(FEEDS_FILE, "w", encoding="utf-8") as f:
        json.dump({"feeds": feeds, "count": len(feeds)}, f, indent=2, ensure_ascii=False)


def fetch_from(source):
    """Προσομοίωση fetch ανά πηγή"""
    alias = source.get("alias")
    base_url = source.get("base_url")
    timeout = 3

    try:
        r = requests.get(base_url, timeout=timeout)
        if r.status_code == 200:
            log_event(f"✅ {alias} ανταποκρίθηκε κανονικά.")
            return {"status": "ok", "source": alias}
        else:
            raise Exception(f"Status {r.status_code}")
    except Exception as e:
        log_event(f"⚠️ {alias} απέτυχε ({e})")
        raise


def get_next_available(feeds, current_alias):
    """Επιστρέφει την επόμενη διαθέσιμη ενεργή πηγή"""
    for f in feeds:
        if f["alias"] != current_alias and f.get("active", True):
            return f
    return None


def get_data_auto():
    """Κύρια συνάρτηση με auto-fallback λογική"""
    feeds = load_feeds()
    primary = next((f for f in feeds if f.get("active") and f.get("status") == "OK"), None)
    if not primary:
        log_event("❌ Δεν υπάρχει ενεργή πηγή στο feeds.json.")
        return None

    current_alias = primary["alias"]

    try:
        result = fetch_from(primary)
        return result
    except Exception:
        fallback = get_next_available(feeds, current_alias)
        if fallback:
            log_event(f"🔁 AUTO-FALLBACK → Μετάβαση από {current_alias} σε {fallback['alias']}")
            try:
                result = fetch_from(fallback)
                return result
            except Exception:
                log_event(f"❌ Και η εφεδρική πηγή {fallback['alias']} απέτυχε.")
                return None
        else:
            log_event("❌ Δεν βρέθηκε καμία εφεδρική πηγή διαθέσιμη.")
            return None
