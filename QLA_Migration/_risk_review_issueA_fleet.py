"""Issue A — read-only fleet risk counts for A1–A9 (quikplan + rates)."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QP = ROOT / "Output" / "quikplan.csv"
RATES = ROOT / "Output" / "rates"


def fnum(v):
    try:
        return float(str(v).strip())
    except Exception:
        return None


def load_qp():
    with QP.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def has_rate_family(plan: str, stems: list[str]) -> bool:
    if not RATES.exists():
        return False
    plan_u = plan.upper()
    for stem in stems:
        # QuikGps.csv, QuikPlGp.csv etc.
        for p in RATES.glob(f"{stem}*.csv"):
            try:
                with p.open(newline="", encoding="utf-8-sig") as f:
                    for row in csv.DictReader(f):
                        if (row.get("PLAN") or "").strip().upper() == plan_u:
                            return True
            except Exception:
                continue
    return False


def main():
    rows = load_qp()
    print(f"quikplan rows: {len(rows)}  path={QP}")

    # A1 description-based SP
    sp = [r for r in rows if "SINGLE PREM" in ((r.get("DESCR") or "") + " " + (r.get("FRIENDLY") or "")).upper()]
    print(f"\nA1 DESCR SINGLE PREM: {len(sp)}")
    a1_fail = 0
    for r in sp:
        ok = fnum(r.get("PAYYRS")) == 1 and all(
            fnum(r.get(c)) == 0 for c in ("SEMI", "QTRL", "MTHD", "MTHB")
        )
        if not ok:
            a1_fail += 1
        print(
            f"  {r['PLAN']}: PAYYRS={r.get('PAYYRS')} "
            f"S/Q/M={r.get('SEMI')}/{r.get('QTRL')}/{r.get('MTHD')}/{r.get('MTHB')} "
            f"{'PASS' if ok else 'FAIL'}"
        )
    print(f"A1 would_change (modal/PAYYRS): {a1_fail}")

    # A7 VARGP vs any GP rates
    vargp4 = [r for r in rows if str(r.get("VARGP", "")).strip() == "4"]
    print(f"\nA7 VARGP=4: {len(vargp4)} / {len(rows)}")

    # A8 annuity heuristics: PRODUCT or DESCR
    ann = [
        r
        for r in rows
        if (r.get("PLAN") or "").upper().startswith("A")
        or "ANNUITY" in (r.get("DESCR") or "").upper()
    ]
    print(f"\nA8 annuity-like plans: {len(ann)}")
    for r in ann:
        print(
            f"  {r['PLAN']}: PAR={r.get('PAR')} VARDB={r.get('VARDB')} "
            f"VARGP={r.get('VARGP')} DESCR={r.get('DESCR')}"
        )

    # A9 prefix 9
    p9 = [r for r in rows if (r.get("PLAN") or "").startswith("9")]
    par_bad = [r for r in p9 if str(r.get("PAR", "")).strip() == "1"]
    print(f"\nA9 prefix-9: {len(p9)}; PAR=1 among them: {len(par_bad)}")

    # A3 missing Pl* — quick file presence
    pl_stems = ["QuikPlGd", "QuikPlBd", "QuikPlUw", "QuikPlSt"]
    plans_with = defaultdict(set)
    if RATES.exists():
        for stem in pl_stems:
            for p in RATES.glob(f"{stem}*.csv"):
                with p.open(newline="", encoding="utf-8-sig") as f:
                    for row in csv.DictReader(f):
                        pl = (row.get("PLAN") or "").strip()
                        if pl:
                            plans_with[pl].add(stem)
    missing_all = [r["PLAN"] for r in rows if not plans_with.get(r["PLAN"])]
    print(f"\nA3 plans with NO PlGd/Bd/Uw/St rows: {len(missing_all)}")
    if missing_all:
        print(" ", ", ".join(missing_all[:40]))

    # blank PLAN in QuikPl*
    blank = 0
    if RATES.exists():
        for p in RATES.glob("QuikPl*.csv"):
            with p.open(newline="", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    if not (row.get("PLAN") or "").strip():
                        blank += 1
                        break  # count files with at least one
        print(f"\nA4 QuikPl* files with ≥1 blank PLAN row: {blank}")


if __name__ == "__main__":
    main()
