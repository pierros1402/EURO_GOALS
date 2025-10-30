# ============================================================
# modules/smartmoney_monitor.py
# Real-time SmartMoney odds loop (API-Football 1X2) + MFI%
# ============================================================

from datetime import datetime
import time
import requests
import random

# Target league IDs (API-Football — Ευρώπη 1-2 + Γερμανία 3 + Ελλάδα 1-2)
TARGET_LEAGUES = [
    # England
    39, 40, 41, 42,
    # Germany
    78, 79, 80,
    # Greece
    197, 566,
    # Spain
    140, 141,
    # Italy
    135, 136,
    # France
    61, 62,
    # Netherlands
    88, 89,
    # Portugal
    94, 95,
    # Belgium
    144, 145,
    # Switzerland
    207, 208,
    # Austria
    218, 219,
    # Denmark
    13, 14,
    # Norway
    103, 104,
    # Sweden
    119, 120,
    # Poland
    106, 107,
    # Romania
    283, 284,
    # Serbia
    285, 286,
    # Turkey
    203, 204,
]

def _safe_float(x):
    try:
        return float(x)
    except:
        return None

def _dec_to_imp(o):
    if not o or o <= 1.0:
        return 0.0
    return 1.0 / o

def _norm3(a, b, c):
    s = a + b + c
    if s <= 0:
        return (0.0, 0.0, 0.0)
    return (a / s, b / s, c / s)

def _money_flow(start_odds, current_odds):
    p1s, pxs, p2s = _norm3(*[_dec_to_imp(start_odds[k]) for k in ("1","X","2")])
    p1c, pxc, p2c = _norm3(*[_dec_to_imp(current_odds[k]) for k in ("1","X","2")])
    d = (abs(p1c - p1s) + abs(pxc - pxs) + abs(p2c - p2s)) / 3.0
    return round(min(100.0, 100.0 * d * 3.5), 1)

def _movement_label(start_odds, current_odds):
    deltas = {
        "Home": start_odds["1"] - current_odds["1"],
        "Draw": start_odds["X"] - current_odds["X"],
        "Away": start_odds["2"] - current_odds["2"],
    }
    k = max(deltas, key=lambda x: abs(deltas[x]))
    up = deltas[k] > 0
    return f"{k}{'↑' if up else '↓'}"

def _match_key(home, away):
    return f"{(home or '').strip()} - {(away or '').strip()}"

class SmartMoneyMonitor:
    def __init__(self, refresh_interval: int, apifootball_key: str, sportmonks_key: str = ""):
        self.refresh_interval = max(15, int(refresh_interval))
        self.apifootball_key = apifootball_key
        self.sportmonks_key = sportmonks_key
        self._feed_cache = []
        self._start_odds = {}  # αρχικό snapshot ανά match
        self._last_refresh = None

    # -------- public --------
    def run_forever(self):
        print(f"[SMARTMONEY] ♻️ Loop started – every {self.refresh_interval}s")
        while True:
            try:
                self._refresh_once()
                self._last_refresh = datetime.now()
                print(f"[SMARTMONEY] ✅ Unified {len(self._feed_cache)} matches")
            except Exception as e:
                print("[SMARTMONEY] ❌ Refresh error:", e)
            time.sleep(self.refresh_interval)

    def get_feed(self):
        if not self._feed_cache:
            try:
                self._refresh_once()
            except Exception:
                pass
        return self._feed_cache

    def last_refresh_str(self):
        return self._last_refresh.strftime("%Y-%m-%d %H:%M:%S") if self._last_refresh else "—"

    # -------- internal --------
    def _refresh_once(self):
        items = self._fetch_apifootball()
        if not items:
            items = self._simulate(8)
            print("[SMARTMONEY] 🟡 Simulation mode")
        self._feed_cache = self._enrich(items)

    def _fetch_apifootball(self):
        if not self.apifootball_key:
            return []
        headers = {"x-apisports-key": self.apifootball_key}
        season = datetime.now().year
        out = []
        for lid in TARGET_LEAGUES:
            try:
                r = requests.get(
                    "https://v3.football.api-sports.io/odds",
                    headers=headers,
                    params={"league": lid, "season": season, "bookmaker": 8},  # 8: Pinnacle
                    timeout=10
                )
                if r.status_code != 200:
                    continue
                for it in r.json().get("response") or []:
                    teams = it.get("teams") or {}
                    home = (teams.get("home") or {}).get("name") or ""
                    away = (teams.get("away") or {}).get("name") or ""
                    mk = _match_key(home, away)

                    odds = it.get("odds") or []
                    o1 = oX = o2 = None
                    for book in odds:
                        for m in (book.get("markets") or []):
                            if "1x2" in (m.get("name") or "").lower():
                                for s in (m.get("outcomes") or []):
                                    nm = (s.get("name") or "").strip().lower()
                                    pr = _safe_float(s.get("price"))
                                    if pr:
                                        if nm in ["home", "1", home.lower()]: o1 = pr
                                        elif nm in ["draw", "x"]: oX = pr
                                        elif nm in ["away", "2", away.lower()]: o2 = pr
                    if o1 and oX and o2:
                        out.append({"match": mk, "odds": {"1": round(o1,2), "X": round(oX,2), "2": round(o2,2)}})
            except Exception as e:
                print(f"[SMARTMONEY] ⚠️ League {lid} skipped: {e}")
        print(f"[SMARTMONEY] 📡 API-Football fetched {len(out)} matches")
        return out

    def _simulate(self, n=10):
        demo = ["Arsenal - Chelsea","Bayern - Dortmund","PAOK - Olympiacos","Juventus - Inter","Barcelona - Sevilla","PSG - Marseille","Ajax - Feyenoord","Porto - Benfica"]
        out = []
        for _ in range(n):
            m = random.choice(demo)
            o1, oX, o2 = [round(random.uniform(1.7, 3.6), 2) for _ in range(3)]
            out.append({"match": m, "odds": {"1": o1, "X": oX, "2": o2}})
        return out

    def _enrich(self, items):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        merged = {}
        for it in items:
            mk = it.get("match")
            o = (it.get("odds") or {})
            if not mk or not all(k in o for k in ("1","X","2")):
                continue
            merged[mk] = o

        out = []
        for mk, cur in merged.items():
            if mk not in self._start_odds:
                self._start_odds[mk] = cur.copy()
            start = self._start_odds[mk]
            mfi = _money_flow(start, cur)
            mov = _movement_label(start, cur)
            out.append({
                "match": mk,
                "market": "1X2",
                "start_odds": start,
                "current_odds": cur,
                "movement": mov,
                "money_flow": mfi,
                "timestamp": now
            })
        return out
