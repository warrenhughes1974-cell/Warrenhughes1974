"""Issue #169 Regression — rate tables before/after the PAAGERAT NP emit.

Hard requirement from Planning section 6: every plan other than 5667AT must be
byte-identical across every rate table. Only 5667AT may gain rows, and only in
QuikNps (the grid) and QuikPlTv (its derived key rows).

Compares QLA_Migration/Archive/rates_pre_issue169_20260915 against
QLA_Migration/Output/rates. Exit 1 on any unexpected drift.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BEFORE = os.path.join(ROOT, "QLA_Migration", "Archive", "rates_pre_issue169_20260915")
AFTER = os.path.join(ROOT, "QLA_Migration", "Output", "rates")

EXPECTED_PLAN = "5667AT"
EXPECTED_TABLES = {"QuikNps", "QuikPlTv"}
SKIP = {"rate_csv_manifest"}


def load(path):
    """rows as tuples, plus header."""
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh)
        try:
            hdr = next(rd)
        except StopIteration:
            return [], []
        return [tuple(r) for r in rd], hdr


def plan_of(row, hdr):
    try:
        return row[hdr.index("PLAN")]
    except (ValueError, IndexError):
        return ""


def main() -> int:
    tables = sorted({os.path.splitext(f)[0] for f in os.listdir(BEFORE) if f.endswith(".csv")}
                    | {os.path.splitext(f)[0] for f in os.listdir(AFTER) if f.endswith(".csv")})
    failures = []
    print("{:<18}{:>10}{:>10}{:>9}  {}".format("TABLE", "BEFORE", "AFTER", "DELTA", "VERDICT"))
    print("-" * 76)

    for table in tables:
        if table in SKIP:
            continue
        before, hdr_b = load(os.path.join(BEFORE, table + ".csv"))
        after, hdr_a = load(os.path.join(AFTER, table + ".csv"))
        if before is None or after is None:
            failures.append("{}: present in only one side".format(table))
            print("{:<18}{:>10}{:>10}{:>9}  MISSING SIDE".format(table, "-", "-", "-"))
            continue
        if hdr_b != hdr_a:
            failures.append("{}: header changed".format(table))
            print("{:<18}{:>10}{:>10}{:>9}  HEADER CHANGED".format(
                table, len(before), len(after), len(after) - len(before)))
            continue

        set_b, set_a = set(before), set(after)
        added, removed = set_a - set_b, set_b - set_a
        if not added and not removed:
            print("{:<18}{:>10}{:>10}{:>9}  identical".format(
                table, len(before), len(after), 0))
            continue

        add_plans = Counter(plan_of(r, hdr_a) for r in added)
        rem_plans = Counter(plan_of(r, hdr_b) for r in removed)
        offenders = {p for p in (set(add_plans) | set(rem_plans)) if p != EXPECTED_PLAN}

        verdict = []
        if table not in EXPECTED_TABLES:
            failures.append("{}: changed but is not an expected table".format(table))
            verdict.append("UNEXPECTED TABLE")
        if offenders:
            failures.append("{}: plans other than {} changed: {}".format(
                table, EXPECTED_PLAN, sorted(offenders)[:8]))
            verdict.append("OTHER PLANS CHANGED")
        if removed and not offenders:
            # removals on the expected plan are still worth surfacing
            verdict.append("{} rows removed on {}".format(len(removed), EXPECTED_PLAN))
        if not verdict:
            verdict.append("OK (+{} rows, {} only)".format(len(added), EXPECTED_PLAN))

        print("{:<18}{:>10}{:>10}{:>9}  {}".format(
            table, len(before), len(after), len(after) - len(before), "; ".join(verdict)))
        if add_plans:
            print("      added by plan:   {}".format(dict(add_plans)))
        if rem_plans:
            print("      removed by plan: {}".format(dict(rem_plans)))

    print()
    # Detail on the intended change
    after_nps, hdr = load(os.path.join(AFTER, "QuikNps.csv"))
    mine = [r for r in after_nps if plan_of(r, hdr) == EXPECTED_PLAN]
    seg = defaultdict(int)
    for r in mine:
        seg[(r[hdr.index("GENDER")], r[hdr.index("UWCLASS")],
             r[hdr.index("BAND")], r[hdr.index("EFFDATE")])] += 1
    print("{} QuikNps rows now emitted: {}".format(EXPECTED_PLAN, len(mine)))
    for k in sorted(seg):
        print("   GENDER={} UWCLASS={} BAND={} EFFDATE={} -> {} rows".format(*k, seg[k]))

    after_keys, hk = load(os.path.join(AFTER, "QuikPlTv.csv"))
    mykeys = [r for r in after_keys if plan_of(r, hk) == EXPECTED_PLAN]
    print()
    print("{} QuikPlTv key rows: {}".format(EXPECTED_PLAN, len(mykeys)))
    for r in sorted(mykeys):
        print("   " + " ".join("{}={}".format(hk[i], r[i]) for i in range(len(hk))
                               if hk[i] in ("GENDER", "UWCLASS", "EFFDATE", "MORT",
                                            "RSVINT", "RSVMETH")))

    print()
    if failures:
        print("REGRESSION FAIL")
        for f in failures:
            print("  - " + f)
        return 1
    print("REGRESSION PASS — only {} changed, only in {}".format(
        EXPECTED_PLAN, sorted(EXPECTED_TABLES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
