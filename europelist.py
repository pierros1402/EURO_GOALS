# -*- coding: utf-8 -*-
"""
Ευρωπαϊκές Λίγκες Ποδοσφαίρου — europelist.py

Ενημερωμένη έκδοση με ΟΛΕΣ τις βασικές χώρες της Ευρώπης (επίπεδα 1–2, όπου ισχύει).
"""
from __future__ import annotations
import argparse
import csv
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Iterable


@dataclass(frozen=True)
class Division:
    level: int
    name: str
    code: Optional[str] = None


@dataclass
class CountryLeagues:
    country: str
    divisions: List[Division]

    def by_level(self, level: Optional[int] = None) -> List[Division]:
        if level is None:
            return self.divisions
        return [d for d in self.divisions if d.level == level]


# --- Χώρες και Λίγκες ---
ENGLAND = CountryLeagues("England", [
    Division(1, "Premier League", "EPL"),
    Division(2, "Championship", "EFL CH"),
    Division(3, "League One", "EFL L1"),
    Division(4, "League Two", "EFL L2"),
    Division(5, "National League", "NL"),
])
GERMANY = CountryLeagues("Germany", [
    Division(1, "Bundesliga", "BULI"),
    Division(2, "2. Bundesliga", "BL2"),
    Division(3, "3. Liga", "BL3"),
])
GREECE = CountryLeagues("Greece", [
    Division(1, "Super League 1", "SL1"),
    Division(2, "Super League 2", "SL2"),
    Division(3, "Gamma Ethniki", "G Ethniki"),
])
SPAIN = CountryLeagues("Spain", [
    Division(1, "LaLiga", "LL"),
    Division(2, "LaLiga 2", "LL2"),
])
ITALY = CountryLeagues("Italy", [
    Division(1, "Serie A", "SA"),
    Division(2, "Serie B", "SB"),
])
FRANCE = CountryLeagues("France", [
    Division(1, "Ligue 1", "L1"),
    Division(2, "Ligue 2", "L2"),
])
NETHERLANDS = CountryLeagues("Netherlands", [
    Division(1, "Eredivisie", "NED1"),
    Division(2, "Eerste Divisie", "NED2"),
])
PORTUGAL = CountryLeagues("Portugal", [
    Division(1, "Primeira Liga", "POR1"),
    Division(2, "Liga Portugal 2", "POR2"),
])
BELGIUM = CountryLeagues("Belgium", [
    Division(1, "Pro League", "BEL1"),
    Division(2, "Challenger Pro League", "BEL2"),
])
SCOTLAND = CountryLeagues("Scotland", [
    Division(1, "Scottish Premiership", "SCO1"),
    Division(2, "Scottish Championship", "SCO2"),
])
TURKEY = CountryLeagues("Turkey", [
    Division(1, "Süper Lig", "TR1"),
    Division(2, "TFF First League", "TR2"),
])
AUSTRIA = CountryLeagues("Austria", [
    Division(1, "Bundesliga", "AUT1"),
    Division(2, "2. Liga", "AUT2"),
])
SWITZERLAND = CountryLeagues("Switzerland", [
    Division(1, "Super League", "SUI1"),
    Division(2, "Challenge League", "SUI2"),
])
DENMARK = CountryLeagues("Denmark", [
    Division(1, "Superliga", "DEN1"),
    Division(2, "1st Division", "DEN2"),
])
NORWAY = CountryLeagues("Norway", [
    Division(1, "Eliteserien", "NOR1"),
    Division(2, "OBOS-ligaen", "NOR2"),
])
SWEDEN = CountryLeagues("Sweden", [
    Division(1, "Allsvenskan", "SWE1"),
    Division(2, "Superettan", "SWE2"),
])
FINLAND = CountryLeagues("Finland", [
    Division(1, "Veikkausliiga", "FIN1"),
    Division(2, "Ykkönen", "FIN2"),
])
ICELAND = CountryLeagues("Iceland", [
    Division(1, "Besta deild karla", "ISL1"),
    Division(2, "1. deild karla", "ISL2"),
])
IRELAND = CountryLeagues("Ireland", [
    Division(1, "Premier Division", "IRL1"),
    Division(2, "First Division", "IRL2"),
])
POLAND = CountryLeagues("Poland", [
    Division(1, "Ekstraklasa", "POL1"),
    Division(2, "I liga", "POL2"),
])
CZECHIA = CountryLeagues("Czechia", [
    Division(1, "Czech First League", "CZE1"),
    Division(2, "FNL", "CZE2"),
])
SLOVAKIA = CountryLeagues("Slovakia", [
    Division(1, "Super Liga", "SVK1"),
    Division(2, "2. Liga", "SVK2"),
])
SLOVENIA = CountryLeagues("Slovenia", [
    Division(1, "PrvaLiga", "SLO1"),
    Division(2, "2. SNL", "SLO2"),
])
CROATIA = CountryLeagues("Croatia", [
    Division(1, "HNL", "CRO1"),
    Division(2, "Prva NL", "CRO2"),
])
SERBIA = CountryLeagues("Serbia", [
    Division(1, "SuperLiga", "SRB1"),
    Division(2, "Prva Liga", "SRB2"),
])
ROMANIA = CountryLeagues("Romania", [
    Division(1, "Liga I", "ROU1"),
    Division(2, "Liga II", "ROU2"),
])
HUNGARY = CountryLeagues("Hungary", [
    Division(1, "NB I", "HUN1"),
    Division(2, "NB II", "HUN2"),
])
BULGARIA = CountryLeagues("Bulgaria", [
    Division(1, "First League", "BUL1"),
    Division(2, "Second League", "BUL2"),
])
CYPRUS = CountryLeagues("Cyprus", [
    Division(1, "First Division", "CYP1"),
    Division(2, "Second Division", "CYP2"),
])
MALTA = CountryLeagues("Malta", [
    Division(1, "Premier League", "MLT1"),
    Division(2, "Challenge League", "MLT2"),
])
LUXEMBOURG = CountryLeagues("Luxembourg", [
    Division(1, "National Division", "LUX1"),
    Division(2, "Division of Honour", "LUX2"),
])
ESTONIA = CountryLeagues("Estonia", [
    Division(1, "Meistriliiga", "EST1"),
    Division(2, "Esiliiga", "EST2"),
])
LATVIA = CountryLeagues("Latvia", [
    Division(1, "Virsliga", "LAT1"),
    Division(2, "1. Liga", "LAT2"),
])
LITHUANIA = CountryLeagues("Lithuania", [
    Division(1, "A Lyga", "LTU1"),
    Division(2, "I Lyga", "LTU2"),
])
UKRAINE = CountryLeagues("Ukraine", [
    Division(1, "Premier League", "UKR1"),
    Division(2, "First League", "UKR2"),
])

EURO_LEAGUES: Dict[str, CountryLeagues] = {c.country: c for c in [
    ENGLAND, GERMANY, GREECE, SPAIN, ITALY, FRANCE, NETHERLANDS, PORTUGAL, BELGIUM, SCOTLAND,
    TURKEY, AUSTRIA, SWITZERLAND, DENMARK, NORWAY, SWEDEN, FINLAND, ICELAND, IRELAND, POLAND,
    CZECHIA, SLOVAKIA, SLOVENIA, CROATIA, SERBIA, ROMANIA, HUNGARY, BULGARIA, CYPRUS, MALTA,
    LUXEMBOURG, ESTONIA, LATVIA, LITHUANIA, UKRAINE
]}


def list_countries() -> List[str]:
    return sorted(EURO_LEAGUES.keys())

def get_country(name: str) -> Optional[CountryLeagues]:
    name_low = name.strip().lower()
    for c in EURO_LEAGUES.values():
        if c.country.lower().startswith(name_low):
            return c
    return None

def search_all(term: str) -> List[Dict[str, str]]:
    t = term.lower().strip()
    results = []
    for country, bundle in EURO_LEAGUES.items():
        for d in bundle.divisions:
            if t in f"{country.lower()} {d.name.lower()} {d.code or ''}":
                results.append({"country": country, "level": str(d.level), "division": d.name, "code": d.code or ""})
    return results

def to_rows() -> List[Dict[str, str]]:
    rows = []
    for country, bundle in EURO_LEAGUES.items():
        for d in bundle.divisions:
            rows.append({"country": country, "level": str(d.level), "division": d.name, "code": d.code or ""})
    rows.sort(key=lambda r: (r["country"], int(r["level"])))
    return rows

def export_json(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({c: [asdict(d) for d in EURO_LEAGUES[c].divisions] for c in EURO_LEAGUES}, f, ensure_ascii=False, indent=2)

def export_csv(path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["country", "level", "division", "code"])
        writer.writeheader()
        writer.writerows(to_rows())

def main(argv: Optional[Iterable[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Κατάλογος ευρωπαϊκών λιγκών.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("countries")
    l = sub.add_parser("leagues"); l.add_argument("--country", required=True); l.add_argument("--level", type=int)
    s = sub.add_parser("search"); s.add_argument("--q", required=True)
    e = sub.add_parser("export"); e.add_argument("--format", choices=["json", "csv"], required=True); e.add_argument("--out", required=True)
    args = p.parse_args(argv)
    if args.cmd == "countries":
        for c in list_countries(): print(c)
    elif args.cmd == "leagues":
        c = get_country(args.country)
        if not c: print(f"❌ Δεν βρέθηκε χώρα {args.country}"); return
        for d in c.by_level(args.level): print(f"L{d.level}: {d.name} ({d.code or ''})")
    elif args.cmd == "search":
        for r in search_all(args.q): print(f"{r['country']} — L{r['level']}: {r['division']} ({r['code']})")
    elif args.cmd == "export":
        (export_json if args.format == 'json' else export_csv)(args.out); print(f"✅ Εξαγωγή ολοκληρώθηκε: {args.out}")

if __name__ == "__main__":
    main()
