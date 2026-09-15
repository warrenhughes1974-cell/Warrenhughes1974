"""Independent verification that the Issue #168 L14 replication is value-correct.

Row counts matching is not enough. This asserts that for every 1L14SC row, the
PQ / PR / ST copies are field-for-field identical to the NT row at the same
(AGE, CNTL, GENDER, BAND, ISSCNTRY, ISSUEST, EFFDATE), and that QuikGps still
genuinely varies by class (i.e. the premium table was NOT flattened).

Read-only.
"""
from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
PLAN = "1L14SC"
KEY = ("AGE", "CNTL", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")
TABLES = ["QuikTvs", "QuikNps", "QuikCvs", "QuikNff", "QuikPlTv", "QuikPlCv", "QuikPlDb", "QuikPlDv"]


def rows_for(fn: str):
    with open(os.path.join(RATES, fn + ".csv"), encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), [r for r in rd if (r.get("PLAN") or "").strip() == PLAN]


def main() -> int:
    failures = 0
    for fn in TABLES:
        cols, rows = rows_for(fn)
        keycols = [c for c in KEY if c in cols]
        valcols = [c for c in cols if c not in ("PLAN", "UWCLASS")]
        by_class: dict = {}
        for r in rows:
            by_class.setdefault((r.get("UWCLASS") or "").strip(), {})[
                tuple((r.get(c) or "").strip() for c in keycols)
            ] = r

        nt = by_class.get("NT", {})
        line = f"  {fn:<10} NT={len(nt)}"
        for cls in ("PQ", "PR", "ST"):
            other = by_class.get(cls, {})
            mism = 0
            missing = 0
            for key, ntrow in nt.items():
                orow = other.get(key)
                if orow is None:
                    missing += 1
                    continue
                if any((ntrow.get(c) or "") != (orow.get(c) or "") for c in valcols):
                    mism += 1
            line += f"  {cls}: n={len(other)} missing={missing} value_mismatch={mism}"
            failures += missing + mism
        print(line)

    # QuikGps must still vary by class
    cols, rows = rows_for("QuikGps")
    keycols = [c for c in KEY if c in cols]
    gpcols = [c for c in cols if c.startswith("GP")]
    byc: dict = {}
    for r in rows:
        byc.setdefault((r.get("UWCLASS") or "").strip(), {})[
            tuple((r.get(c) or "").strip() for c in keycols)
        ] = r
    nt = byc.get("NT", {})
    pq = byc.get("PQ", {})
    differing = sum(
        1
        for key, ntrow in nt.items()
        if key in pq and any((ntrow.get(c) or "") != (pq[key].get(c) or "") for c in gpcols)
    )
    shared = sum(1 for key in nt if key in pq)
    print(f"\n  QuikGps: {shared} shared NT/PQ keys, {differing} differ on premium values")
    if shared and differing == 0:
        print("  FAIL: premium table looks flattened across classes")
        failures += 1

    print()
    if failures:
        print(f"RESULT: FAIL ({failures} problems)")
        return 1
    print("RESULT: PASS - PQ/PR/ST are exact copies of NT, and QuikGps still varies by class")
    return 0


if __name__ == "__main__":
    sys.exit(main())
