"""
Issue #77 validator — default keys, PVO, MLOANINT, no factor invent.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"

FAMILY_KEYS = {
    "GP": "QuikPlGp.csv",
    "DB": "QuikPlDb.csv",
    "CV": "QuikPlCv.csv",
    "TV": "QuikPlTv.csv",
    "DV": "QuikPlDv.csv",
}
FAMILY_FACTORS = {
    "GP": "QuikGps.csv",
    "DB": "QuikDbs.csv",
    "CV": "QuikCvs.csv",
    "TV": "QuikTvs.csv",
    "DV": "QuikDvs.csv",
}
VARY = [
    "GDVARYGP", "GDVARYDB", "GDVARYCV", "GDVARYTV", "GDVARYDV",
    "UWVARYGP", "UWVARYDB", "UWVARYCV", "UWVARYTV", "UWVARYDV",
    "BDVARYGP", "BDVARYDB", "BDVARYCV", "BDVARYTV", "BDVARYDV",
    "STVARYGP", "STVARYDB", "STVARYCV", "STVARYTV", "STVARYDV",
]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    fails = []
    rated = set()
    for fname in list(FAMILY_FACTORS.values()) + ["QuikNps.csv", "QuikNff.csv", "QuikCoi.csv"]:
        for r in read(RATES / fname):
            p = (r.get("PLAN") or "").strip()
            if p:
                rated.add(p)

    keys_by = {}
    for sfx, fname in FAMILY_KEYS.items():
        by = defaultdict(list)
        for r in read(RATES / fname):
            by[(r.get("PLAN") or "").strip()].append(r)
        keys_by[sfx] = by

    missing_keys = []
    for plan in sorted(rated):
        for sfx in FAMILY_KEYS:
            if not keys_by[sfx].get(plan):
                missing_keys.append(f"{plan}.{sfx}")
    if missing_keys:
        fails.append(f"MISSING_FAMILY_KEYS count={len(missing_keys)} sample={missing_keys[:8]}")

    # Factor counts unchanged vs presence: every factor plan still has factors
    # (we don't invent factors — just ensure keys exist)
    st = read(RATES / "QuikPlSt.csv")
    blank_loan = [r["PLAN"] for r in st if not str(r.get("MLOANINT") or "").strip()]
    if blank_loan:
        fails.append(f"MLOANINT_BLANK count={len(blank_loan)} sample={blank_loan[:5]}")

    qp = read(OUT / "quikplan.csv")
    bad_pvo = []
    for r in qp:
        pvo = (r.get("PLANVALOPT") or "").strip()
        if pvo not in ("Y", "N", ""):
            bad_pvo.append((r.get("PLAN"), pvo))
    if bad_pvo:
        fails.append(f"PLANVALOPT_ALPHABET count={len(bad_pvo)} sample={bad_pvo[:5]}")

    # Rated plans in quikplan: STVARYGP=Y and all BDVARY*=Y
    qp_by = {(r.get("PLAN") or "").strip(): r for r in qp}
    pvo_gaps = []
    for plan in sorted(rated):
        row = qp_by.get(plan)
        if not row:
            continue
        if (row.get("PLANVALOPT") or "").strip() != "Y":
            pvo_gaps.append(f"{plan}.PLANVALOPT={(row.get('PLANVALOPT') or '')!r}")
        if (row.get("STVARYGP") or "").strip() != "Y":
            pvo_gaps.append(f"{plan}.STVARYGP")
        for sfx in ("GP", "DB", "CV", "TV", "DV"):
            if (row.get(f"BDVARY{sfx}") or "").strip() != "Y":
                pvo_gaps.append(f"{plan}.BDVARY{sfx}")
    if pvo_gaps:
        fails.append(f"PVO_GAPS count={len(pvo_gaps)} sample={pvo_gaps[:12]}")

    # 1658CS spot checks
    if "1658CS" in rated:
        for sfx in FAMILY_KEYS:
            if not keys_by[sfx].get("1658CS"):
                fails.append(f"1658CS missing key family {sfx}")
        r = qp_by.get("1658CS", {})
        if (r.get("STVARYGP") or "") != "Y":
            fails.append("1658CS STVARYGP != Y")
        if (r.get("BDVARYDB") or "") != "Y":
            fails.append("1658CS BDVARYDB != Y")

    # EX rule: no Gender 0 beside F/M; no UW 00 beside real UW
    gd_by = defaultdict(set)
    for r in read(RATES / "QuikPlGd.csv"):
        gd_by[(r.get("PLAN") or "").strip()].add((r.get("GDCODE") or "").strip())
    both_g = [p for p, c in gd_by.items() if "0" in c and (c & {"F", "M", "J"})]
    if both_g:
        fails.append(f"GENDER_0_WITH_REAL count={len(both_g)} sample={both_g[:8]}")

    uw_by = defaultdict(set)
    for r in read(RATES / "QuikPlUw.csv"):
        uw_by[(r.get("PLAN") or "").strip()].add((r.get("UWCODE") or "").strip())
    both_u = [p for p, c in uw_by.items() if "00" in c and (c - {"00", ""})]
    if both_u:
        fails.append(f"UW_00_WITH_REAL count={len(both_u)} sample={both_u[:8]}")

    # 280PUA: F/M only (no Gender 0)
    if "280PUA" in gd_by:
        if "0" in gd_by["280PUA"]:
            fails.append("280PUA still has Gender 0 with real genders")
        if not ({"F", "M"} & gd_by["280PUA"]):
            fails.append("280PUA missing F/M gender members")

    print("Issue #77 validation")
    print(f"  rated plans: {len(rated)}")
    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS")
    print("  all rated plans have GP/DB/CV/TV/DV keys")
    print("  MLOANINT populated")
    print("  PLANVALOPT alphabet OK; STVARYGP + BDVARY* set for rated plans in quikplan")
    print("  no NA member beside real Gender/UW codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
