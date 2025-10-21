# ==============================================
# CROSS VERIFIER MODULE (EURO_GOALS v7.1)
# ==============================================
# Συγκρίνει Sofascore και Flashscore δεδομένα
# και ενημερώνει τη βάση με την πιο αξιόπιστη πηγή.
# ==============================================

from sqlalchemy import create_engine, text
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ----------------------------------------------
# Helper: Καταγραφή στο log αρχείο
# ----------------------------------------------
def log(msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[CROSS_VERIFIER] {timestamp} - {msg}")

# ----------------------------------------------
# Συνάρτηση Cross Verification
# ----------------------------------------------
def verify_and_update():
    """
    Συγκρίνει τις εγγραφές Sofascore και Flashscore στη βάση
    και κρατά την πιο πρόσφατη/αξιόπιστη.
    """

    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT home, away,
                       MAX(CASE WHEN source='Sofascore' THEN score END) AS sofa_score,
                       MAX(CASE WHEN source='Flashscore' THEN score END) AS flash_score,
                       MAX(updated_at) AS last_update
                FROM matches
                WHERE status IN ('live', 'inprogress', '1st_half', '2nd_half')
                GROUP BY home, away
            """)).mappings().all()

            for row in result:
                home = row["home"]
                away = row["away"]
                s_score = row["sofa_score"]
                f_score = row["flash_score"]

                # Αν οι δύο πηγές έχουν διαφορετικό σκορ
                if s_score != f_score and s_score and f_score:
                    log(f"⚠️ Διαφορά σκορ για {home} - {away}: Sofascore={s_score}, Flashscore={f_score}")

                    # Επιλογή πιο πρόσφατης εγγραφής (ή προτεραιότητα Sofascore)
                    preferred = s_score if len(s_score) >= len(f_score) else f_score

                    conn.execute(text("""
                        UPDATE matches
                        SET score = :preferred,
                            source = 'Verified',
                            updated_at = :updated_at
                        WHERE home = :home AND away = :away
                    """), {
                        "preferred": preferred,
                        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "home": home,
                        "away": away
                    })

                    log(f"✅ Ενημερώθηκε ως τελικό σκορ ({preferred}) για {home} - {away}")

                else:
                    # Καμία διαφορά – όλα οκ
                    if s_score:
                        conn.execute(text("""
                            UPDATE matches
                            SET source='Verified', updated_at=:updated_at
                            WHERE home=:home AND away=:away
                        """), {
                            "home": home,
                            "away": away,
                            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        })

            log("🟢 Cross Verification ολοκληρώθηκε επιτυχώς.")

    except Exception as e:
        log(f"❌ Σφάλμα κατά τον έλεγχο: {e}")

# ----------------------------------------------
# Manual Run (τοπικός έλεγχος)
# ----------------------------------------------
if __name__ == "__main__":
    verify_and_update()
