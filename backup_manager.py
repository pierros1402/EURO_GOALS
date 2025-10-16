import os, sqlite3, shutil, requests, json
from datetime import datetime

# === ΡΥΘΜΙΣΕΙΣ ===
FOLDER = os.path.join(os.path.expanduser("~"), "Desktop", "EURO_GOALS")
DB_FILE = os.path.join(FOLDER, "euro_goals_local.db")   # ή euro_goals.db
BACKUP_FOLDER = os.path.join(FOLDER, "BACKUPS")

# API κλειδιά Render (αν έχεις ήδη)
RENDER_API_KEY = "βάλε_το_κλειδί_σου_εδώ"  # π.χ. από https://dashboard.render.com/u/settings
RENDER_SERVICE_ID = "βάλε_το_ID_του_web_service_σου"   # θα σου δείξω πώς το βρίσκεις

# Αν δεν θες να φτιάχνει νέα βάση κάθε μήνα, βάλε False
AUTO_REFRESH = False


def create_backup():
    """Δημιουργεί .sql αντίγραφο της τοπικής βάσης"""
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    now = datetime.now()
    backup_name = f"EURO_GOALS_BACKUP_{now.year}_{now.month:02d}.sql"
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)

    print(f"🕓 Δημιουργία backup: {backup_name}")
    conn = sqlite3.connect(DB_FILE)
    with open(backup_path, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    conn.close()
    print("✅ Το backup ολοκληρώθηκε!")
    return backup_path


def create_new_render_db(backup_path):
    """Δημιουργεί νέα βάση στο Render & κάνει restore"""
    now = datetime.now()
    new_name = f"football_predictor_db_{now.year}_{now.month:02d}"
    print(f"🚀 Δημιουργία νέας Render DB: {new_name}")

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Βήμα 1: Δημιουργία νέας βάσης (Postgres free tier)
    url = "https://api.render.com/v1/databases"
    data = {
        "name": new_name,
        "databaseName": new_name,
        "user": "eurogoals",
        "plan": "free",
        "region": "frankfurt"
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))

    if r.status_code != 201:
        print("❌ Σφάλμα δημιουργίας βάσης:", r.text)
        return None

    db_info = r.json()
    new_db_url = db_info["connection"]["internalDatabaseUrl"]
    print("🔗 Νέο Database URL:", new_db_url)

    # Βήμα 2: Ενημέρωση .env
    env_file = os.path.join(FOLDER, ".env")
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith("DATABASE_URL="):
            lines[i] = f"DATABASE_URL={new_db_url}\n"
            found = True
            break

    if not found:
        lines.append(f"DATABASE_URL={new_db_url}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("🧠 Ενημερώθηκε το .env με το νέο Database URL")

    # Βήμα 3: Επαναφορά backup (restore)
    # (Για απλότητα εδώ απλώς εμφανίζουμε το path, στην τελική έκδοση μπορούμε
    #  να ανεβάσουμε το SQL απευθείας μέσω Render Connect ή psql restore.)
    print(f"📂 Backup file: {backup_path}")
    print("💾 Θα χρησιμοποιηθεί για restore της νέας βάσης μέσω Render dashboard.")

    return new_db_url


if __name__ == "__main__":
    print("🔁 EURO_GOALS Monthly Backup System")
    backup_path = create_backup()

    if AUTO_REFRESH:
        create_new_render_db(backup_path)

    print("🎯 Όλες οι ενέργειες ολοκληρώθηκαν επιτυχώς!")
import requests

# Ρυθμίσεις Render API
RENDER_API_URL = "https://football-predictor-g04v.onrender.com/upload_backup"
ADMIN_TOKEN = "12345"  # βάλε εδώ ένα απλό token που θα ορίσουμε και στο Render

def upload_backup_to_render(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            RENDER_API_URL,
            data={"token": ADMIN_TOKEN},
            files={"file": (os.path.basename(file_path), f, "application/octet-stream")}
        )
    print("🔹 Απάντηση Render:", response.text)

if __name__ == "__main__":
    latest_backup = max(
        [os.path.join("BACKUPS", f) for f in os.listdir("BACKUPS")],
        key=os.path.getctime
    )
    print(f"Ανεβάζω στο Render: {latest_backup}")
    print("🔗 Σύνδεση στο:", RENDER_API_URL)
    upload_backup_to_render(latest_backup)
