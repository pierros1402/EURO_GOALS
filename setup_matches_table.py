# ==============================================
# EURO_GOALS – Setup / Upgrade Matches Table
# ==============================================
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def ensure_matches_table():
    print("⚙️ Έλεγχος/αναβάθμιση πίνακα 'matches'...")

    with engine.begin() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 1️⃣ Αν δεν υπάρχει καθόλου πίνακας, τον δημιουργούμε εξ αρχής
        if "matches" not in tables:
            print("🆕 Δημιουργία νέου πίνακα 'matches'...")
            conn.execute(text("""
                CREATE TABLE matches (
                    id SERIAL PRIMARY KEY,
                    league TEXT,
                    season TEXT,
                    date TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    home_odds FLOAT,
                    draw_odds FLOAT,
                    away_odds FLOAT,
                    score TEXT,
                    result TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("✅ Ο πίνακας 'matches' δημιουργήθηκε επιτυχώς.")
            return

        # 2️⃣ Αν υπάρχει ήδη, ελέγχουμε ποιες στήλες λείπουν
        existing_cols = [c["name"] for c in inspector.get_columns("matches")]
        print(f"📋 Υπάρχουσες στήλες: {existing_cols}")

        desired_cols = {
            "league": "TEXT",
            "season": "TEXT",
            "date": "TEXT",
            "home_team": "TEXT",
            "away_team": "TEXT",
            "home_odds": "FLOAT",
            "draw_odds": "FLOAT",
            "away_odds": "FLOAT",
            "score": "TEXT",
            "result": "TEXT",
            "source": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        added = []
        for col, col_type in desired_cols.items():
            if col not in existing_cols:
                conn.execute(text(f"ALTER TABLE matches ADD COLUMN {col} {col_type};"))
                added.append(col)

        if added:
            print(f"🧩 Προστέθηκαν νέες στήλες: {', '.join(added)}")
        else:
            print("✅ Ο πίνακας είναι ήδη πλήρης.")

if __name__ == "__main__":
    ensure_matches_table()
    print("🏁 Ολοκληρώθηκε η αναβάθμιση βάσης EURO_GOALS.\n")
