# ==============================================
# EURO_GOALS – API Aggregator (v1)
# ==============================================
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from modules.health_check import log_message

# --------------------------------------------------
# 1. Εισαγωγή επιμέρους readers
# --------------------------------------------------
from modules.football_data_reader import get_fixtures as fd_fixtures
from modules.apifootball_reader import get_fixtures as af_fixtures

# --------------------------------------------------
# 2. Φόρτωση .env
# --------------------------------------------------
load_dotenv()
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --------------------------------------------------
# 3. Συνάρτηση συλλογής δεδομένων
# --------------------------------------------------
def aggregate_all_data():
    log_message("[AGGREGATOR] 🚀 Starting full data aggregation...")
    all_data = []

    # --- Football-Data.org ---
    if os.getenv("FOOTBALLDATA_API_KEY"):
        try:
            fd_data = fd_fixtures()
            log_message(f"[AGGREGATOR] ⚽ Football-Data.org returned {len(fd_data)} fixtures.")
            all_data.extend(fd_data)
        except Exception as e:
            log_message(f"[AGGREGATOR] ❌ Football-Data.org error: {e}")
    else:
        log_message("[AGGREGATOR] ⚠️ No Football-Data API key found.")

    # --- API-Football ---
    if os.getenv("APIFOOTBALL_API_KEY"):
        try:
            af_data = af_fixtures(league_id=39)
            log_message(f"[AGGREGATOR] 🏆 API-Football returned {len(af_data)} fixtures.")
            all_data.extend(af_data)
        except Exception as e:
            log_message(f"[AGGREGATOR] ❌ API-Football error: {e}")
    else:
        log_message("[AGGREGATOR] ⚠️ No API-Football key found.")

    # --- (Placeholder για Sportmonks / TheSportsDB) ---
    # Θα προστεθούν στη v2

    # --------------------------------------------------
    # 4. Δημιουργία dataframe & αποθήκευση
    # --------------------------------------------------
    try:
        if not all_data:
            log_message("[AGGREGATOR] ⚠️ No data collected from any source.")
            return

        df = pd.DataFrame(all_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        csv_path = os.path.join(DATA_DIR, f"aggregated_fixtures_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        log_message(f"[AGGREGATOR] ✅ Aggregated data saved to {csv_path}")
    except Exception as e:
        log_message(f"[AGGREGATOR] ❌ Error creating CSV: {e}")


# --------------------------------------------------
# 5. Εκτέλεση script
# --------------------------------------------------
if __name__ == "__main__":
    aggregate_all_data()
