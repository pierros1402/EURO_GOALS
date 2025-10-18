# EURO_GOALS_UI_v6f.py
# ------------------------------------------------------------
# Streamlit Frontend for EURO_GOALS (Render API Integration)
# ------------------------------------------------------------

import requests
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# Βασικές ρυθμίσεις Streamlit
# ------------------------------------------------------------
st.set_page_config(page_title="EURO_GOALS Live", page_icon="⚽", layout="wide")

st.title("⚽ EURO_GOALS Live Odds")
st.caption("Real-time αποδόσεις από το Render API (TheOddsAPI + SofaScore combined)")

# ------------------------------------------------------------
# Λεξικό περιοχών / bundles
# ------------------------------------------------------------
bundles = {
    "Αγγλία (όλες οι κατηγορίες)": "england_all",
    "Ελλάδα 1-2-3": "greece_1_2_3",
    "Γερμανία 1-2-3": "germany_1_2_3",
    "Ευρώπη 1-2": "europe_1_2"
}

# Επιλογή χρήστη
choice = st.selectbox("🌍 Επίλεξε περιοχή:", list(bundles.keys()))

# ------------------------------------------------------------
# Συνάρτηση ανάγνωσης δεδομένων από Render
# ------------------------------------------------------------
def get_live_odds(bundle: str):
    url = f"https://euro-goals.onrender.com/odds_bundle/{bundle}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"⚠️ Σφάλμα {response.status_code} από το API.")
            return None
    except Exception as e:
        st.error(f"❌ Αποτυχία σύνδεσης με API: {e}")
        return None

# ------------------------------------------------------------
# Κουμπί φόρτωσης
# ------------------------------------------------------------
if st.button("🔄 Φόρτωση Αποδόσεων"):
    bundle_key = bundles[choice]
    data = get_live_odds(bundle_key)

    if data and data.get("events"):
        events = data["events"]
        df = pd.DataFrame([
            {"Αγώνας": e["match"], "1": e["odds"].get("1"), "X": e["odds"].get("X"), "2": e["odds"].get("2")}
            for e in events
        ])
        st.success(f"✅ Φορτώθηκαν {len(df)} αγώνες για {choice}")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Δεν βρέθηκαν δεδομένα για αυτή την επιλογή.")
