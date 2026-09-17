"""Issue #169 Planning — why is MTABNET zero for 196085 / 7619PU / 5667AT?

Both 196085 and 7619PU have complete nonzero QuikTvs AND QuikNps grids at
UWCLASS=00, matching every loaded policy's class, yet return MRESERVE=0 with
MTABNET=0. This prints the policy's own age/duration and whether the emitted
grids actually cover that cell — the same test used at #168 review section 1.4.

Read-only.
"""
from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402

PLANS = ("196085", "7619PU", "5667AT")
RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")

# QuikNps/QuikTvs are paged 10 durations per row: CNTL is the page number.
DURS_PER_PAGE = 10


def load_grid(table, prefix):
    """(plan, age, gender, uwclass) -> {duration: value}"""
    grid = {}
    with open(os.path.join(RATES, table + ".csv"), encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["PLAN"] not in PLANS:
                continue
            try:
                age = int(row["AGE"])
                page = int(row["CNTL"])
            except (TypeError, ValueError):
                continue
            key = (row["PLAN"], age, row.get("GENDER", ""), row.get("UWCLASS", ""))
            cells = grid.setdefault(key, {})
            for i in range(DURS_PER_PAGE):
                raw = row.get(prefix + str(i), "")
                try:
                    val = float(raw or 0)
                except ValueError:
                    val = 0.0
                cells[page * DURS_PER_PAGE + i] = val
    return grid


def main() -> int:
    nps = load_grid("QuikNps", "NP")
    tvs = load_grid("QuikTvs", "TV")

    valf = QV.load()
    rows = [r for r in valf.valued if QV.plan_code(r) in PLANS]

    interesting = ["MPOLICY", "MPHASE", "MPLAN", "MAGE", "MDUR", "MSEX", "MUWCLASS",
                   "MUNITS", "MTABNET", "MMEAN", "MRESERVE", "MVPU", "MPAIDTO"]
    present = [f for f in interesting if any(f in r for r in rows)]
    print("QuikValf fields used:", present)
    print()

    shown = 0
    for r in sorted(rows, key=lambda x: (QV.plan_code(x), QV.policy_of(x))):
        plan = QV.plan_code(r)
        if plan == "5667AT" and shown >= 3:
            continue
        if plan == "5667AT":
            shown += 1
        age = int(QV.money(r, "MAGE")) if "MAGE" in r else None
        dur = int(QV.money(r, "MDUR")) if "MDUR" in r else None
        sex = QV.text(r, "MSEX")
        uw = QV.text(r, "MUWCLASS")
        print("-" * 92)
        print("{} plan={} phase={} age={} dur={} sex={} uwclass={!r}".format(
            QV.policy_of(r), plan, QV.phase_of(r), age, dur, sex, uw))
        print("   MUNITS={:.2f}  MTABNET={:.2f}  MMEAN={:.4f}  MRESERVE={:.2f}".format(
            QV.money(r, "MUNITS"), QV.money(r, "MTABNET"),
            QV.money(r, "MMEAN"), QV.money(r, "MRESERVE")))
        for label, grid, in (("QuikNps", nps), ("QuikTvs", tvs)):
            keys = [k for k in grid if k[0] == plan and k[1] == age]
            if not keys:
                ages = sorted({k[1] for k in grid if k[0] == plan})
                span = "{}..{}".format(ages[0], ages[-1]) if ages else "none"
                print("   {}: NO ROW at age {} (plan ages present: {})".format(label, age, span))
                continue
            for k in sorted(keys):
                cells = grid[k]
                at = cells.get(dur)
                at_prev = cells.get((dur or 0) - 1)
                maxdur = max((d for d, v in cells.items() if v), default=None)
                print("   {}: gender={!r} uwclass={!r}  [dur {}]={}  [dur {}]={}  last nonzero dur={}".format(
                    label, k[2], k[3], dur, at, (dur or 0) - 1, at_prev, maxdur))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
