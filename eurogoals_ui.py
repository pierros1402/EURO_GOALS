
import os
import subprocess
from datetime import datetime

import pandas as pd
import streamlit as st

EXCEL_PATH = r"C:\EURO_GOALS\EURO_GOALS_v6d.xlsx"
MATCHES_SHEET = "Matches"

# --- Streamlit page config (dark mode friendly) ---
st.set_page_config(
    page_title="EURO_GOALS v6d — Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force dark theme via CSS
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .st-emotion-cache-1jicfl2, .st-emotion-cache-16idsys { color: #e5e7eb !important; }
    .stSidebar { background-color: #111827; }
    .block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("EURO_GOALS v6d — Dark Dashboard")
st.caption("Ζωντανά δεδομένα από Flashscore → Excel → Προβολή")

# --- Sidebar controls ---
with st.sidebar:
    st.subheader("📂 Πηγή δεδομένων")
    st.write(f"Excel: `{EXCEL_PATH}`")

    if st.button("🔄 Ανανέωση δεδομένων (Flashscore)"):
        with st.spinner("Γίνεται ενημέρωση από Flashscore…"):
            try:
                completed = subprocess.run(
                    ["python", "eurogoals_data.py"],
                    capture_output=True, text=True, timeout=60*20
                )
                st.toast("Ολοκληρώθηκε η ενημέρωση.", icon="✅")
                st.code(completed.stdout[-2000:], language="bash")
                if completed.returncode != 0:
                    st.error("Υπήρξε πρόβλημα στην ενημέρωση (δες logs παραπάνω).")
                    if completed.stderr:
                        st.code(completed.stderr[-2000:], language="bash")
            except Exception as e:
                st.error(f"Σφάλμα κατά την εκτέλεση: {e}")

    st.markdown("---")
    st.subheader("🔎 Φίλτρα")
    country_filter = st.multiselect("Χώρα", options=[])
    league_filter = st.multiselect("Λίγκα", options=[])
    date_from = st.date_input("Από", value=None)
    date_to = st.date_input("Έως", value=None)
    btts_only = st.checkbox("Μόνο BTTS=1")
    over25_only = st.checkbox("Μόνο Over 2.5=1")

# --- Load matches ---
def load_matches():
    if not os.path.exists(EXCEL_PATH):
        st.warning("Δεν βρέθηκε το Excel. Βεβαιώσου ότι υπάρχει στο C:\\EURO_GOALS\\")
        return pd.DataFrame()
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=MATCHES_SHEET, engine="openpyxl")
        for col in ["Date","Country","LeagueCode","LeagueName","HomeTeam","AwayTeam","HomeGoals","AwayGoals",
                    "BTTS","Over1_5","Over2_5","Over3_5","Odd_H","Odd_D","Odd_A","Odd_Over2_5","Odd_Btts"]:
            if col not in df.columns:
                df[col] = None
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Σφάλμα ανάγνωσης Excel: {e}")
        return pd.DataFrame()

df = load_matches()

# Populate sidebar filter options dynamically
with st.sidebar:
    if not df.empty:
        country_filter = st.multiselect("Χώρα", options=sorted(df["Country"].dropna().unique().tolist()), default=country_filter)
        league_filter = st.multiselect("Λίγκα", options=sorted(df["LeagueName"].dropna().unique().tolist()), default=league_filter)

# --- Apply filters ---
view = df.copy()
if not view.empty:
    if country_filter:
        view = view[view["Country"].isin(country_filter)]
    if league_filter:
        view = view[view["LeagueName"].isin(league_filter)]
    if date_from:
        view = view[view["Date"] >= pd.to_datetime(date_from)]
    if date_to:
        view = view[view["Date"] <= pd.to_datetime(date_to)]
    if btts_only:
        view = view[view["BTTS"] == 1]
    if over25_only:
        view = view[view["Over2_5"] == 1]

# --- Main layout ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📅 Αγώνες")
    if view.empty:
        st.info("Δεν υπάρχουν αγώνες για τα τρέχοντα φίλτρα.")
    else:
        view = view.sort_values(["Date","Country","LeagueName","HomeTeam"])
        display_cols = ["Date","Country","LeagueName","HomeTeam","AwayTeam","HomeGoals","AwayGoals","BTTS","Over2_5","Odd_H","Odd_D","Odd_A"]
        st.dataframe(view[display_cols], use_container_width=True, hide_index=True)

        csv = view.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV (τα τρέχοντα)", data=csv, file_name="euro_goals_filtered.csv", mime="text/csv")

with col_right:
    st.subheader("📰 Live / Τελευταία νέα")
    st.caption("Προαιρετικά: μπορεί να συνδεθεί σε RSS ή Flashscore news.")
    st.write("- Σήμερα:", datetime.now().strftime("%Y-%m-%d %H:%M"))

st.markdown("---")
st.caption("EURO_GOALS v6d — Streamlit UI (Dark). Πατήστε «Ανανέωση» για ενημέρωση από Flashscore.")
