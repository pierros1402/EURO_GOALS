# ================================================================
# EURO_GOALS – Goal Matrix Module (v1.0)
# ================================================================
# Παρουσιάζει στατιστικά γκολ (Over/Under, BTTS, SmartMoney flags)
# σε μορφή πίνακα. Αρχικά χρησιμοποιεί dummy δεδομένα.
# ================================================================

from datetime import datetime

def get_goal_matrix_data():
    """
    Επιστρέφει λίστα λεξικών με στατιστικά ομάδων.
    (προς το παρόν mock data – αργότερα θα έρθουν από API / DB)
    """
    data = [
        {
            "team": "Arsenal",
            "league": "Premier League",
            "avg_goals_for": 2.1,
            "avg_goals_against": 0.8,
            "btts": "68%",
            "over25": "72%",
            "smart_flag": "✅",
        },
        {
            "team": "Chelsea",
            "league": "Premier League",
            "avg_goals_for": 1.4,
            "avg_goals_against": 1.5,
            "btts": "61%",
            "over25": "59%",
            "smart_flag": "⚠️",
        },
        {
            "team": "Real Madrid",
            "league": "La Liga",
            "avg_goals_for": 2.3,
            "avg_goals_against": 0.7,
            "btts": "54%",
            "over25": "70%",
            "smart_flag": "✅",
        },
        {
            "team": "Bayern Munich",
            "league": "Bundesliga",
            "avg_goals_for": 2.9,
            "avg_goals_against": 1.1,
            "btts": "73%",
            "over25": "81%",
            "smart_flag": "⚠️",
        },
    ]

    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": data,
    }
