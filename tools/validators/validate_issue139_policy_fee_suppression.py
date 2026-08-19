#!/usr/bin/env python3
"""Issue 139 — ISWL/UNKNOWN fee withhold vs non-ISWL passthrough.

Fail-closed. Missing Output or ISWL fees back on = exit 1.
Does not PASS just because QLA_SUPPRESS_POLICY_FEES=0.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.issue139_fee_smoke import evaluate_fee_withhold  # noqa: E402

OUTPUT = REPO / "QLA_Migration" / "Output"
RIDR = OUTPUT / "quikridr.csv"
MSTR = OUTPUT / "quikmstr.csv"


def main() -> int:
    ok, errors, stats = evaluate_fee_withhold(RIDR, MSTR if MSTR.is_file() else None)
    print(
        f"phase1={stats.get('phase1')} ISWL={stats.get('iswl')} "
        f"ISWL_fee>0={stats.get('iswl_fee')} NON_ISWL_MANNLFEE>0={stats.get('non_iswl_fee')} "
        f"UNKNOWN={stats.get('unknown')}"
    )
    gold = (stats.get("traces") or {}).get("9010713704C")
    if gold:
        print(f"gold 9010713704C fees={gold}")
    mm = (stats.get("traces") or {}).get("9010713704C_MMODEPREM")
    if mm is not None:
        print(f"gold 9010713704C MMODEPREM={mm}")
    if not ok:
        print("FAIL")
        for err in errors:
            print(" ", err)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
