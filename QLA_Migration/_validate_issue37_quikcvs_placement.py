"""
Issue #37 — QuikCvs CV duration placement validation.

Verifies LifePRO-style grid placement (G3 approved):
  - Maturity end: last LifePRO duration = 100 - issue_age
  - Variable start offset from proof matrix (960 PO anchor)

Run from repo root:
  python QLA_Migration/_validate_issue37_quikcvs_placement.py
"""
from __future__ import annotations

import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from qla_core import rate_factor_loader as L
from qla_core import rate_pipeline as P

CONFIG = os.path.join(_REPO, "plan_analysis", "phase_r5_rate_loader", "rate_loader_config.json")

PROOF_CASES = [
    # plan, gender, age, first_value, first_lp_dur, last_value, last_lp_dur
    ("1960PO", "M", "22", 8.32, 4, 1000.0, 78),
    ("1960PO", "M", "00", 3.07, 7, 1000.0, 100),
    ("1960PO", "M", "18", None, 4, None, 82),
    ("1960PO", "M", "24", 0.71, 3, 1000.0, 76),
    ("1960PO", "F", "00", 1.48, 7, 937.11, 100),
]


def _cell(grid, plan, age, gender, ql_dur):
    cntl = str(ql_dur // 10).zfill(2)
    col = ql_dur % 10
    key = None
    for k in grid:
        if k[0] == plan and k[1] == age and k[2] == cntl and k[3] == gender:
            key = k
            break
    if key is None:
        return None
    cell = grid[key].get(col)
    return cell[0] if cell else None


def _lp_to_ql(lp_dur):
    return lp_dur - 1


def main():
    if not os.path.isfile(CONFIG):
        print("FAIL: missing rate_loader_config.json")
        return 1

    res = P.run(CONFIG, _REPO)
    grid = res.grids.get("QuikCvs", {})
    if not grid:
        print("FAIL: no QuikCvs grid produced")
        return 1

    failures = []
    for plan, gender, age, first_val, first_lp, last_val, last_lp in PROOF_CASES:
        if first_val is not None:
            got = _cell(grid, plan, age, gender, _lp_to_ql(first_lp))
            if got is None or round(got, 2) != round(first_val, 2):
                failures.append(
                    f"{plan} {gender} age {age}: first rate expected {first_val} at LP dur {first_lp}, got {got}"
                )
        if last_val is not None:
            got = _cell(grid, plan, age, gender, _lp_to_ql(last_lp))
            if got is None or round(got, 2) != round(last_val, 2):
                failures.append(
                    f"{plan} {gender} age {age}: last rate expected {last_val} at LP dur {last_lp}, got {got}"
                )

    # M22 anchor: 8.32 must NOT remain at ql duration 1 (old bug)
    old_bug = _cell(grid, "1960PO", "22", "M", 1)
    if old_bug is not None and round(old_bug, 2) == 8.32:
        failures.append("1960PO M22: 8.32 still at ql duration 1 (regression)")

    # Non-CV families unchanged path: QuikNps grid still populated
    np_keys = len(res.grids.get("QuikNps", {}))
    if np_keys == 0:
        failures.append("QuikNps grid empty — possible pipeline regression")

    trunc = res.row_status.get("EXCLUDED", 0)
    print(f"Pipeline blockers: {res.blocker_count}")
    print(f"QuikCvs distinct keys: {len(grid)}")
    print(f"QuikNps distinct keys: {np_keys}")
    print(f"CV truncated rows (past maturity): {trunc}")

    if res.blocker_count:
        failures.append(f"pipeline blockers: {res.blocker_count}")

    if failures:
        print("FAIL")
        for f in failures:
            print(" ", f)
        return 1

    print("PASS — Issue #37 QuikCvs placement proof cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
