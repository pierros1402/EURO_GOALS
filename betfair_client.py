# ==============================================
# BETFAIR CLIENT (Official Exchange API – JSON-RPC)
# EURO_GOALS v6g – Live Market Volumes & Prices
# ==============================================

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any

BETFAIR_JSONRPC_URL = "https://api.betfair.com/exchange/betting/json-rpc/v1"

class BetfairClient:
    """
    Απλός JSON-RPC client για Betfair Exchange.
    Απαιτούνται:
      - BETFAIR_APP_KEY     (X-Application)
      - BETFAIR_SESSION     (X-Authentication) = SSO session token
    """
    def __init__(self, app_key: str = None, session_token: str = None):
        self.app_key = app_key or os.getenv("BETFAIR_APP_KEY")
        self.session = session_token or os.getenv("BETFAIR_SESSION")
        self.headers = {
            "X-Application": self.app_key or "",
            "X-Authentication": self.session or "",
            "content-type": "application/json"
        }

    def is_configured(self) -> bool:
        return bool(self.app_key and self.session)

    # -----------------------------
    # JSON-RPC call helper
    # -----------------------------
    def _rpc(self, method: str, params: Dict[str, Any]) -> Any:
        payload = [{
            "jsonrpc": "2.0",
            "method": f"SportsAPING/v1.0/{method}",
            "params": params,
            "id": 1
        }]
        resp = requests.post(BETFAIR_JSONRPC_URL, headers=self.headers, data=json.dumps(payload), timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and "result" in data[0]:
            return data[0]["result"]
        raise RuntimeError(f"Betfair RPC unexpected response: {data}")

    # -----------------------------
    # List markets (Match Odds) για ποδόσφαιρο
    # -----------------------------
    def list_match_odds_markets(
        self,
        competition_ids: List[int] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Επιστρέφει καταλόγους αγορών 'MATCH_ODDS' (1-X-2) για Soccer (eventTypeId=1).
        """
        market_filter = {
            "eventTypeIds": ["1"],  # 1 = Soccer
            "marketTypeCodes": ["MATCH_ODDS"]
        }
        if competition_ids:
            market_filter["competitionIds"] = [str(c) for c in competition_ids]

        params = {
            "filter": market_filter,
            "maxResults": str(max_results),
            "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "MARKET_START_TIME"],
            "sort": "FIRST_TO_START"
        }
        return self._rpc("listMarketCatalogue", params)

    # -----------------------------
    # Get prices & volumes για markets
    # -----------------------------
    def list_market_book(self, market_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Επιστρέφει live prices (best available) και totalMatched ανά market.
        """
        if not market_ids:
            return []
        params = {
            "marketIds": market_ids,
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_TRADED"],
                "virtualise": True
            }
        }
        return self._rpc("listMarketBook", params)

    # -----------------------------
    # Βοηθητική: Best back price για κάθε runner
    # -----------------------------
    @staticmethod
    def _best_back(runner: Dict[str, Any]) -> float | None:
        try:
            return runner["ex"]["availableToBack"][0]["price"]
        except Exception:
            return None

    # -----------------------------
    # High-level: Πάρε αγώνες + τιμές + συνολικά matched ποσά
    # -----------------------------
    def get_match_odds_snapshot(
        self,
        competition_ids: List[int] = None,
        max_results: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Ενώνει marketCatalogue + marketBook:
        Επιστρέφει [{"match", "home_odds","draw_odds","away_odds","total_volume"}...]
        """
        catalogues = self.list_match_odds_markets(competition_ids, max_results=max_results)
        market_ids = [m["marketId"] for m in catalogues]
        books = self.list_market_book(market_ids)

        # Map marketId -> book
        book_by_id = {b["marketId"]: b for b in books}

        rows = []
        for m in catalogues:
            event = m.get("event", {})
            home_team, away_team = _split_home_away(event.get("name", ""))

            book = book_by_id.get(m["marketId"])
            home_odds = draw_odds = away_odds = None
            total_matched = 0.0

            if book:
                total_matched = book.get("totalMatched", 0.0)
                runners = book.get("runners", [])
                # Συνήθως: 3 runners [Home, Away, Draw] ή [Home, Draw, Away] ανάλογα με σειρά καταλόγου
                # Θα προσπαθήσουμε να αναθέσουμε by selectionId mapping από το catalogue
                cat_runners = {r["selectionId"]: r["runnerName"] for r in m.get("runners", [])}
                for r in runners:
                    name = cat_runners.get(r["selectionId"], "")
                    price = self._best_back(r)
                    if name.lower() in ("home", home_team.lower()):
                        home_odds = price or home_odds
                    elif name.lower() in ("away", away_team.lower()):
                        away_odds = price or away_odds
                    elif name.lower() in ("draw", "x"):
                        draw_odds = price or draw_odds

                # Αν παραμείνουν None, κάνε graceful fallback από τη σειρά
                if home_odds is None and len(runners) >= 1:
                    home_odds = self._best_back(runners[0])
                if draw_odds is None and len(runners) >= 3:
                    draw_odds = self._best_back(runners[2])
                if away_odds is None and len(runners) >= 2:
                    away_odds = self._best_back(runners[1])

            rows.append({
                "match": f"{home_team} - {away_team}" if home_team and away_team else event.get("name", "-"),
                "home_odds": _round_or_dash(home_odds),
                "draw_odds": _round_or_dash(draw_odds),
                "away_odds": _round_or_dash(away_odds),
                "total_volume": int(total_matched) if total_matched else 0,
                "kickoff": m.get("marketStartTime")
            })

        return rows


# ------------------------------------------
# Helpers
# ------------------------------------------
def _split_home_away(event_name: str) -> tuple[str, str]:
    if not event_name:
        return "", ""
    if " v " in event_name:
        parts = event_name.split(" v ")
    elif " vs " in event_name:
        parts = event_name.split(" vs ")
    elif "-" in event_name:
        parts = event_name.split("-")
    else:
        parts = [event_name, ""]
    return parts[0].strip(), parts[-1].strip()

def _round_or_dash(value: float | None) -> float | str:
    if value is None:
        return "-"
    try:
        return round(float(value), 2)
    except Exception:
        return "-"
