"""Issue #169 Planning — blast radius of a PAAGERAT TYPE_CODE='NP' loader.

`qla_core/paagerat_pr_loader.py` streams PAAGERAT rows for one TYPE_CODE and has
thin wrappers for 'PR' and 'NF' only. There is no 'NP' wrapper, so any plan whose
net-premium schedule exists only in the attained-age extract emits zero QuikNps
rows. This sizes how many coverages/plans that affects and, critically, how many
already have QuikNps rows from PDAGE (where new rows could collide).

Read-only.
"""
from __future__ import annotations

import collections
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PAAGERAT = os.path.join(ROOT, "QLA_Migration", "Source",
                        "PAAGERAT_AttainedAge_Rates_Extract_20260831.csv")
PDAGE = os.path.join(ROOT, "QLA_Migration", "Source",
                     "PDAGE_AgeDuration_Rates_Extract_20260831.csv")
QUIKNPS = os.path.join(ROOT, "QLA_Migration", "Output", "rates", "QuikNps.csv")
CROSSWALK = os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv")


def np_coverages(path, cov_col=0, type_col=1):
    counts = collections.Counter()
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        fh.readline()
        for line in fh:
            parts = line.split(",")
            if len(parts) > type_col and parts[type_col].strip() == "NP":
                counts[parts[cov_col].strip()] += 1
    return counts


def main() -> int:
    pa_np = np_coverages(PAAGERAT)
    pd_np = np_coverages(PDAGE)

    emitted = collections.Counter()
    with open(QUIKNPS, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            emitted[row["PLAN"]] += 1

    cov2plan = {}
    with open(CROSSWALK, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cov_key = reader.fieldnames[0]
        for row in reader:
            cov = (row.get(cov_key) or "").strip()
            plan = ""
            for cand in ("ql_plan_code", "plan", "output_plan", "PLAN"):
                if row.get(cand):
                    plan = row[cand].strip()
                    break
            if cov:
                cov2plan[cov] = plan

    print("PAAGERAT (attained-age) coverages carrying TYPE_CODE='NP':",
          len(pa_np), "coverages /", sum(pa_np.values()), "rows")
    print("PDAGE (age-duration) coverages carrying TYPE_CODE='NP':",
          len(pd_np), "coverages /", sum(pd_np.values()), "rows")
    print()

    header = "{:<18}{:>9}{:>10}{:>10}{:>15}".format(
        "COVERAGE", "PA NP", "PDAGE NP", "PLAN", "QuikNps today")
    print(header)
    print("-" * len(header))

    at_risk = []
    for cov, n in pa_np.most_common():
        plan = cov2plan.get(cov, "?")
        have = emitted.get(plan, 0)
        pdn = pd_np.get(cov, 0)
        print("{:<18}{:>9}{:>10}{:>10}{:>15}".format(cov, n, pdn, plan or "?", have))
        if have == 0:
            at_risk.append((cov, n, plan))

    print()
    print("Coverages with attained-age NP data whose plan has NO QuikNps rows today:")
    for cov, n, plan in at_risk:
        print("   {:<18} {:>6} NP rows -> PLAN {}".format(cov, n, plan or "?"))
    print()
    print("Overlap risk (coverage has NP in BOTH extracts):",
          sorted(set(pa_np) & set(pd_np)) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
