"""Issue A A4-A9 verification after quikplan conversion."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QP = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
RATES = ROOT / "QLA_Migration" / "Output" / "rates"

VARY_GP = ("GDVARYGP", "UWVARYGP", "BDVARYGP", "STVARYGP")
KEY_FAM = {"GP": "QuikPlGp", "DB": "QuikPlDb", "CV": "QuikPlCv", "TV": "QuikPlTv", "DV": "QuikPlDv"}


def y(val) -> bool:
    return str(val or "").strip().upper() in ("Y", "T", "1", "TRUE")


def keys_for_plan(plan: str) -> dict[str, int]:
    out = {fam: 0 for fam in KEY_FAM}
    for fam, tbl in KEY_FAM.items():
        p = RATES / f"{tbl}.csv"
        if not p.is_file():
            continue
        with p.open(newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if (r.get("PLAN") or "").strip() == plan:
                    out[fam] += 1
    return out


def main() -> int:
    if not QP.is_file():
        print(f"Missing {QP}")
        return 1

    with QP.open(newline="", encoding="utf-8-sig") as f:
        plans = {r["PLAN"]: r for r in csv.DictReader(f) if (r.get("PLAN") or "").strip()}

    blank = []
    for p in sorted(RATES.glob("QuikPl*.csv")):
        with p.open(newline="", encoding="utf-8-sig") as f:
            for i, r in enumerate(csv.DictReader(f)):
                if not (r.get("PLAN") or "").strip():
                    blank.append(p.name)

    a7 = [
        p for p, r in plans.items()
        if str(r.get("VARGP", "")).strip() == "4" and keys_for_plan(p).get("GP", 0) > 0
    ]
    ann_bad_par = [p for p in plans if p.startswith("A") and str(plans[p].get("PAR", "")).strip() != "0"]
    ann_bad_vardb = [p for p in plans if p.startswith("A") and str(plans[p].get("VARDB", "")).strip() != "0"]
    ann_bad_vary = [
        p for p in plans if p.startswith("A")
        and (y(plans[p].get("PLANVALOPT")) or any(y(plans[p].get(f)) for f in VARY_GP))
    ]
    p9_par = [p for p in plans if p.startswith("9") and str(plans[p].get("PAR", "")).strip() == "1"]
    a6 = []
    for plan, r in plans.items():
        k = keys_for_plan(plan)
        for fam in KEY_FAM:
            if k.get(fam, 0) == 0:
                for field in (f"GDVARY{fam}", f"UWVARY{fam}", f"BDVARY{fam}", f"STVARY{fam}"):
                    if y(r.get(field)):
                        a6.append((plan, field))

    print("=== Issue A A4-A9 verification ===")
    print(f"A4 blank PLAN rows in QuikPl*: {len(blank)} {'PASS' if not blank else 'FAIL'}")
    print(f"A6 orphan vary flags (no keys): {len(a6)} {'PASS' if not a6 else 'FAIL'}")
    if a6[:5]:
        print(f"  sample: {a6[:5]}")
    print(f"A7 VARGP=4 with GP keys: {len(a7)} (SME — not auto-fixed)")
    print(f"A8a PAR!=0 on A-prefix: {len(ann_bad_par)} {'PASS' if not ann_bad_par else 'FAIL'} {ann_bad_par}")
    print(f"A8b VARDB!=0 on A-prefix: {len(ann_bad_vardb)} {'PASS' if not ann_bad_vardb else 'FAIL'} {ann_bad_vardb}")
    print(f"A8e PLANVALOPT/VARY on A-prefix: {len(ann_bad_vary)} {'PASS' if not ann_bad_vary else 'FAIL'}")
    print(f"A9b prefix-9 PAR=1: {len(p9_par)} {'PASS' if not p9_par else 'FAIL'}")

    fail = bool(blank or a6 or ann_bad_par or ann_bad_vardb or ann_bad_vary or p9_par)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
