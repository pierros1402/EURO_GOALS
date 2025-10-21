# ==============================================
# CROSS VERIFIER MODULE (EURO_GOALS v7.2 – Safe)
# ==============================================
# Συγκρίνει Sofascore & Flashscore από τον πίνακα `matches`
# Αποθηκεύει αποτέλεσμα σε `verifier_state` (ΔΕΝ αλλάζει matches)
# και γράφει διαγνωστικά logs για αποκλίσεις.
# ==============================================

from sqlalchemy import create_engine, text
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

LIVE_STATUSES = ("live", "inprogress", "1st_half", "2nd_half", "extra_time")

def log(msg: str) -> None:
    print(f"[CROSS_VERIFIER] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def ensure_tables():
    """Δημιουργεί τον πίνακα κατάστασης επαλήθευσης αν λείπει."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS verifier_state (
                match_key   TEXT PRIMARY KEY,
                home        TEXT,
                away        TEXT,
                sofa_score  TEXT,
                flash_score TEXT,
                decided     TEXT,
                note        TEXT,
                updated_at  TEXT
            )
        """))

def _mk_key(home: str, away: str) -> str:
    return f"{home.strip().lower()}__{away.strip().lower()}"

def _pick_decision(sofa_score: str | None, flash_score: str | None) -> tuple[str | None, str]:
    """
    Επιλογή "καλύτερης" τιμής σκορ.
    Κανόνας v1:
      - Αν υπάρχει μόνο μία τιμή → αυτή.
      - Αν διαφέρουν → προτεραιότητα Sofascore, αλλιώς Flashscore.
    Επιστρέφει (decided, note).
    """
    if sofa_score and not flash_score:
        return sofa_score, "only_sofascore"
    if flash_score and not sofa_score:
        return flash_score, "only_flashscore"
    if not sofa_score and not flash_score:
        return None, "no_data"

    if sofa_score == flash_score:
        return sofa_score, "agree"
    # Διαφέρουν → προτεραιότητα Sofascore (v1 απλός κανόνας)
    return sofa_score, f"disagree_sofa_pref (sofa={sofa_score}, flash={flash_score})"

def verify_and_update():
    """
    Φορτώνει τα πιο πρόσφατα live rows ανά (home, away) για κάθε source,
    υπολογίζει απόφαση και ενημερώνει τον πίνακα verifier_state.
    """
    ensure_tables()

    with engine.begin() as conn:
        # Φέρνουμε τα πιο πρόσφατα live rows (τελευταίο update σε προτεραιότητα)
        rows = conn.execute(text(f"""
            SELECT home, away, score, source, updated_at
            FROM matches
            WHERE status IN :st
            ORDER BY updated_at DESC
        """), {"st": LIVE_STATUSES}).mappings().all()

    # Ομαδοποίηση: (home, away) -> { 'Sofascore': {...}, 'Flashscore': {...} }
    latest: dict[tuple[str, str], dict[str, dict]] = {}
    for r in rows:
        key = (r["home"], r["away"])
        src = (r["source"] or "").strip()
        if src not in ("Sofascore", "Flashscore", "Verified"):
            continue
        # Κρατάμε το πρώτο (είναι ήδη ταξινομημένα DESC κατά updated_at)
        if key not in latest:
            latest[key] = {}
        if src not in latest[key]:
            latest[key][src] = dict(r)

    # Υπολογισμός αποφάσεων & αποθήκευση κατάστασης
    upserts = 0
    discrepancies = 0
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with engine.begin() as conn:
        for (home, away), sources in latest.items():
            sofa_score = sources.get("Sofascore", {}).get("score")
            flash_score = sources.get("Flashscore", {}).get("score")

            decided, note = _pick_decision(sofa_score, flash_score)
            if note.startswith("disagree"):
                discrepancies += 1
                log(f"⚠️ Διαφορά σκορ για {home} – {away}: Sofascore={sofa_score}, Flashscore={flash_score}")

            match_key = _mk_key(home, away)
            conn.execute(text("""
                INSERT INTO verifier_state (match_key, home, away, sofa_score, flash_score, decided, note, updated_at)
                VALUES (:k, :h, :a, :sofa, :flash, :decided, :note, :ts)
                ON CONFLICT(match_key) DO UPDATE SET
                    sofa_score = excluded.sofa_score,
                    flash_score = excluded.flash_score,
                    decided    = excluded.decided,
                    note       = excluded.note,
                    updated_at = excluded.updated_at
            """), {
                "k": match_key,
                "h": home,
                "a": away,
                "sofa": sofa_score,
                "flash": flash_score,
                "decided": decided,
                "note": note,
                "ts": now
            })
            upserts += 1

    log(f"🟢 Cross Verification ολοκληρώθηκε: {upserts} matches, {discrepancies} discrepancies.")
    # Επιστρέφουμε μικρή σύνοψη για πιθανή χρήση από API/monitor
    return {"processed": upserts, "discrepancies": discrepancies, "timestamp": now}

if __name__ == "__main__":
    verify_and_update()
