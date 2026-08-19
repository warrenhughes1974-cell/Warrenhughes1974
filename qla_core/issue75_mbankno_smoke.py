"""Issue #75 / #45 always-on Bank Acct smoke (quikmstr.MBANKNO).

Closed v58.35: PAC (MBILLFRM=2) Bank Acct must be QLA-safe ABA/ACCOUNT.
A later quikmstr rebatch that cannot resolve 9-digit ABA blanks every PAC
row — this smoke is the hard stop so that drop cannot ship.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

MIN_PAC_FILLED = 2000
MAX_PAC_BLANK = 80
FLEET_PAC_MIN = 500

TRACE_EXPECT = {
    "9010161748C": "091303855/0000002000581",
    "9010157076C": "104910135/212919",
    "9010348734C": "081518113/208787",
    "9010713704C": "104000016/47374579",
}

LOOKUP_NAME = "aba_routing_lookup.csv"


def mbankno_is_ql_safe(mbankno: str) -> bool:
    mb = str(mbankno or "").strip()
    if not mb or mb.count("/") != 1:
        return False
    aba, acct = mb.split("/", 1)
    if re.search(r"\D", aba) or re.search(r"\D", acct):
        return False
    return len(aba) == 9 and len(acct) >= 4


def find_aba_lookup(source_dir: Path) -> Path | None:
    direct = source_dir / LOOKUP_NAME
    if direct.is_file():
        return direct
    if not source_dir.is_dir():
        return None
    for child in sorted(source_dir.iterdir()):
        if child.is_dir() and child.name.startswith("LifePRO_Extracts_"):
            nested = child / LOOKUP_NAME
            if nested.is_file():
                return nested
    return None


def evaluate_quikmstr(path: Path) -> tuple[bool, list[str], dict]:
    errors: list[str] = []
    stats = {
        "rows": 0,
        "pac": 0,
        "pac_filled": 0,
        "pac_blank": 0,
        "pac_invalid": 0,
        "traces": {},
    }
    if not path.is_file():
        return False, [f"Missing output: {path}"], stats

    traces_needed = set(TRACE_EXPECT)
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            stats["rows"] += 1
            pol = (row.get("MPOLICY") or "").strip()
            bf = (row.get("MBILLFRM") or "").strip()
            mb = (row.get("MBANKNO") or "").strip()
            if pol in traces_needed:
                stats["traces"][pol] = mb
            if bf != "2":
                continue
            stats["pac"] += 1
            if not mb:
                stats["pac_blank"] += 1
                continue
            stats["pac_filled"] += 1
            if not mbankno_is_ql_safe(mb):
                stats["pac_invalid"] += 1
                if len(errors) < 8:
                    errors.append(f"{pol}: invalid MBANKNO={mb!r}")

    if stats["pac"] >= FLEET_PAC_MIN:
        if stats["pac_filled"] < MIN_PAC_FILLED:
            errors.append(
                f"PAC Bank Acct dropped: filled={stats['pac_filled']} "
                f"(need >={MIN_PAC_FILLED}) blank={stats['pac_blank']} pac={stats['pac']}. "
                f"Restore {LOOKUP_NAME} in Source and re-emit quikmstr."
            )
        if stats["pac_blank"] > MAX_PAC_BLANK:
            errors.append(
                f"PAC Bank Acct blank={stats['pac_blank']} exceeds leftover cap {MAX_PAC_BLANK} "
                f"(filled={stats['pac_filled']} pac={stats['pac']})"
            )
    if stats["pac_invalid"]:
        errors.insert(0, f"invalid_filled={stats['pac_invalid']}")

    for pol, expected in TRACE_EXPECT.items():
        got = stats["traces"].get(pol, "")
        if got != expected:
            errors.append(f"{pol}: expected {expected!r} got {got!r}")

    ok = not errors
    return ok, errors, stats
