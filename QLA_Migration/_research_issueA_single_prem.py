"""Issue A — read-only scan: SINGLE PREMIUM in plan description + modal compliance."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATHS = [
    ROOT / "Output" / "quikplan.csv",
    ROOT / "Output" / "Test_Validation" / "quikplan.csv",
]

MODE_COLS = ("SEMI", "QTRL", "MTHD", "MTHB")


def desc_blob(r: dict) -> str:
    parts = []
    for k, v in r.items():
        ku = k.upper()
        if any(x in ku for x in ("DESCR", "FRIEND", "NAME", "LONG")):
            parts.append(str(v or ""))
    return " ".join(parts).upper()


def is_single_prem_desc(r: dict) -> bool:
    b = desc_blob(r)
    return "SINGLE PREM" in b or "SINGLE-PREM" in b


def fnum(v) -> float | None:
    try:
        return float(str(v).strip())
    except Exception:
        return None


def analyze(path: Path) -> None:
    print("=" * 72)
    if not path.exists():
        print("MISSING", path)
        return
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"{path}  plans={len(rows)}")
    print("columns:", ",".join(list(rows[0].keys())[:40]) if rows else "(empty)")

    sp = [r for r in rows if is_single_prem_desc(r)]
    print(f"\nPlans with SINGLE PREM in description/friendly: {len(sp)}")
    print(
        f"{'PLAN':<10} {'PAYYRS':>6} {'PAYAGE':>6} {'SEMI':>10} {'QTRL':>10} "
        f"{'MTHD':>10} {'MTHB':>10}  A1_OK?  DESCR"
    )
    for r in sorted(sp, key=lambda x: x.get("PLAN", "")):
        payyrs = r.get("PAYYRS", "")
        payage = r.get("PAYAGE", "")
        semi = fnum(r.get("SEMI"))
        qtrl = fnum(r.get("QTRL"))
        mthd = fnum(r.get("MTHD"))
        mthb = fnum(r.get("MTHB"))
        # PAYYRS may emit as "1" or "01"; treat numeric == 1 as OK
        payyrs_n = fnum(payyrs)
        payyrs_ok = payyrs_n == 1.0
        modes = (semi, qtrl, mthd, mthb)
        modes_ok = all(v is not None and v == 0.0 for v in modes)
        a1_ok = payyrs_ok and modes_ok
        descr = (r.get("DESCR") or "")[:40]
        print(
            f"{r.get('PLAN',''):<10} {str(payyrs):>6} {str(payage):>6} "
            f"{semi if semi is not None else '':>10} "
            f"{qtrl if qtrl is not None else '':>10} "
            f"{mthd if mthd is not None else '':>10} "
            f"{mthb if mthb is not None else '':>10}  "
            f"{'PASS' if a1_ok else 'FAIL':<6}  {descr}"
        )
        if not a1_ok:
            reasons = []
            if not payyrs_ok:
                reasons.append(f"PAYYRS={payyrs!r} need 1")
            if not modes_ok:
                reasons.append(f"S/Q/M={semi}/{qtrl}/{mthd}/{mthb} need 0")
            print(f"           -> {'; '.join(reasons)}")

    # Also flag SP / SPWL in PLAN code without description hit
    code_hits = [
        r
        for r in rows
        if not is_single_prem_desc(r)
        and (
            "SPWL" in (r.get("PLAN") or "").upper()
            or (r.get("PLAN") or "").upper().endswith("SP")
            or "SPWL" in desc_blob(r)
        )
    ]
    if code_hits:
        print(f"\nPossible SP by code (not in DESCR): {len(code_hits)}")
        for r in code_hits:
            print(f"  {r.get('PLAN')} DESCR={r.get('DESCR')}")


def main() -> None:
    for p in PATHS:
        analyze(p)


if __name__ == "__main__":
    main()
