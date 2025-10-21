# ==============================================
# BETFAIR LIVE STATUS TEST
# EURO_GOALS v6g – Manual API check utility
# ==============================================

from betfair_client import BetfairClient
from datetime import datetime

def main():
    print("⚽ [EURO_GOALS v6g] Betfair Live Status Test")
    print("=============================================")
    bf = BetfairClient()

    if not bf.is_configured():
        print("⚠️ Betfair credentials not found in environment (.env)")
        print("   → Add BETFAIR_APP_KEY and BETFAIR_SESSION if available.")
        print("   → Running in mock/offline mode.")
        return

    try:
        print(f"🕒 Starting test at {datetime.now().strftime('%H:%M:%S')} ...")
        markets = bf.get_match_odds_snapshot(max_results=5)

        if not markets:
            print("⚠️ No markets found (check competition IDs or API limits).")
        else:
            print(f"✅ Retrieved {len(markets)} markets successfully.")
            for m in markets[:5]:
                print(
                    f"   {m['match']:<35} "
                    f"1:{m['home_odds']}  X:{m['draw_odds']}  2:{m['away_odds']}  "
                    f"Vol:{m['total_volume']}"
                )

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
