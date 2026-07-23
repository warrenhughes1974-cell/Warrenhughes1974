"""Issue #95 read-only research: PDINT/PDINTTBL declared rates vs QuikUint emit."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output" / "rates"

PDINT = SOURCE / "PDINT_DeclaredInterestRates_Extract_20260630.csv"
PDINTTBL = SOURCE / "PDINTTBL_DeclaredInterestRates_Extract_20260630.csv"
UINT = OUT / "QuikUint.csv"
AINT = OUT / "QuikAint.csv"
QUIKPLAN = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"


def norm(row: dict) -> dict[str, str]:
    return {k.strip(): (v or "").strip() for k, v in row.items()}


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [norm(r) for r in csv.DictReader(f)]


def current_tier(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    return sorted(rows, key=lambda r: r.get("START_DATE", ""))[-1]


def main() -> None:
    print("=== PDINT headers ===")
    for r in load(PDINT):
        if r.get("IDENT") in ("", "-----"):
            continue
        print(
            f"  IDENT={r.get('IDENT')} TYPE={r.get('TYPE_CODE')} "
            f"DINT_RULE={r.get('DINT_RULE')} EFF={r.get('EFF_DATE')}"
        )

    print("\n=== PDINTTBL current tier by IDENT ===")
    by_ident: dict[str, list] = defaultdict(list)
    for r in load(PDINTTBL):
        if r.get("IDENT") in ("", "-----"):
            continue
        by_ident[r["IDENT"]].append(r)
    for ident in sorted(by_ident):
        cur = current_tier(by_ident[ident])
        rates = sorted({x.get("DECLARED_RATE", "") for x in by_ident[ident]})
        print(
            f"  {ident}: n={len(by_ident[ident])} rates={rates} "
            f"CURRENT type={cur.get('TYPE_CODE')} start={cur.get('START_DATE')} "
            f"end={cur.get('END_DATE')} rate={cur.get('DECLARED_RATE')} "
            f"rule={cur.get('DINT_RULE')}"
        )

    print("\n=== QuikUint current rates by MPLAN ===")
    if UINT.exists():
        by_plan: dict[str, list] = defaultdict(list)
        for r in load(UINT):
            by_plan[r.get("MPLAN", "")].append(r)
        for plan in sorted(by_plan):
            rows = sorted(by_plan[plan], key=lambda x: x.get("MEFFDATE", ""))
            cur = rows[-1]
            print(
                f"  {plan}: n={len(rows)} current MEFF={cur.get('MEFFDATE')} "
                f"MCUR={cur.get('MCURRATE')} MGTD={cur.get('MGTDRATE')}"
            )
    else:
        print("  MISSING")

    print("\n=== QuikAint sample (plans / rates) ===")
    if AINT.exists():
        by_plan = defaultdict(list)
        for r in load(AINT):
            plan = r.get("PLAN") or r.get("MPLAN") or ""
            by_plan[plan].append(r)
        print(f"  plans={len(by_plan)} rows={sum(len(v) for v in by_plan.values())}")
        for plan in sorted(by_plan)[:25]:
            rows = by_plan[plan]
            rates = sorted(
                {
                    (x.get("RATE") or x.get("MCURRATE") or x.get("INT_RATE") or "").strip()
                    for x in rows
                }
            )
            print(f"  {plan}: n={len(rows)} rate_fields={rates} keys={list(rows[0].keys())[:8]}")
    else:
        print("  MISSING")

    print("\n=== quikplan candidate families ===")
    if QUIKPLAN.exists():
        keys = load(QUIKPLAN)
        iswl = {
            "1658C1",
            "1658CS",
            "1659C2",
            "1659CR",
            "1659CS",
            "1659SR",
            "1669SR",
            "1679CS",
        }
        sal = {"1SALOL", "1SALML", "1SALMI"}
        print(f"  total_plans={len(keys)} iswl_in_catalog={sorted(iswl & {r.get('PLAN') for r in keys})}")
        print(f"  sal_in_catalog={sorted(sal & {r.get('PLAN') for r in keys})}")
        print(f"  depint_nonzero={[r.get('PLAN') for r in keys if (r.get('DEPINT') or '0').strip() not in ('', '0', '0.00')]}")
        for r in sorted(keys, key=lambda x: x.get("PLAN", "")):
            plan = r.get("PLAN", "")
            descr = r.get("DESCR", "") or ""
            family = "OTHER"
            if plan in iswl:
                family = "ISWL"
            elif plan in sal or "SAL" in plan.upper():
                family = "SAL"
            elif plan.startswith("1L10") or "L10" in descr.upper():
                family = "L10"
            elif "DAR" in plan.upper() or "DAR" in descr.upper():
                family = "DAR"
            elif plan == "1668SP":
                family = "SPWL?"
            if family != "OTHER":
                print(
                    f"  [{family}] PLAN={plan} DESCR={descr!r} "
                    f"DEPINT={r.get('DEPINT')!r} NFOINT={r.get('NFOINT')!r}"
                )


if __name__ == "__main__":
    main()
