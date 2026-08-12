#!/usr/bin/env python3
"""Issue 139 — mixed ISWL/UNKNOWN fee suppression vs non-ISWL passthrough.

Read-only / data-driven. Does not modify Output.
Baseline fleet counts (~2249 ISWL / ~2191 non-ISWL) are sanity checks only.
Clean acceptance requires UNKNOWN phase-1 MPLAN count = 0 absent waiver.
"""

from __future__ import annotations

import csv
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from qla_core.modal_premium_factors import (
    POLICY_FEE_FIELDS,
    issue139_fee_class,
    policy_fees_suppressed,
)

OUTPUT = os.path.join(REPO, "QLA_Migration", "Output")
REPORTS = os.path.join(REPO, "QLA_Migration", "Reports")


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="latin1", errors="replace") as f:
        return list(csv.DictReader(f))


def _num(val) -> float:
    try:
        return float(str(val or "").strip().replace(",", "") or 0)
    except ValueError:
        return 0.0


def _any_fee(row: dict) -> bool:
    return any(_num(row.get(f)) > 0 for f in POLICY_FEE_FIELDS)


def main() -> int:
    ridr_path = os.path.join(OUTPUT, "quikridr.csv")
    if not os.path.isfile(ridr_path):
        print(f"SKIP: {ridr_path} not found — run batch first")
        return 0

    if not policy_fees_suppressed():
        print(
            "PASS: QLA_SUPPRESS_POLICY_FEES=0 — Issue 139 suppression disabled; "
            "#58/#89 cover full-fleet fee load"
        )
        return 0

    ridr = _read_csv(ridr_path)
    base = [r for r in ridr if (r.get("MPHASE") or "").strip() in ("1", "01")]

    cohorts = {"ISWL": [], "NON_ISWL": [], "UNKNOWN": []}
    for r in base:
        cohorts[issue139_fee_class(r.get("MPLAN"))].append(r)

    iswl_n = len(cohorts["ISWL"])
    non_n = len(cohorts["NON_ISWL"])
    unk_n = len(cohorts["UNKNOWN"])
    unk_list = sorted(
        {(r.get("MPOLICY") or "").strip() for r in cohorts["UNKNOWN"] if (r.get("MPOLICY") or "").strip()}
    )

    iswl_fee = sum(1 for r in cohorts["ISWL"] if _any_fee(r))
    unk_fee = sum(1 for r in cohorts["UNKNOWN"] if _any_fee(r))
    non_fee = sum(1 for r in cohorts["NON_ISWL"] if _num(r.get("MANNLFEE")) > 0)

    print(
        f"phase1 total={len(base)} ISWL={iswl_n} NON_ISWL={non_n} UNKNOWN={unk_n}"
    )
    print(
        f"ISWL fee>0={iswl_fee} UNKNOWN fee>0={unk_fee} NON_ISWL MANNLFEE>0={non_fee}"
    )
    if unk_list:
        print(f"UNKNOWN policies: {', '.join(unk_list[:50])}")
        if len(unk_list) > 50:
            print(f"  ... +{len(unk_list) - 50} more")

    failures: list[str] = []
    if iswl_fee:
        failures.append(f"ISWL rows with nonzero fees = {iswl_fee} (must be 0)")
    if unk_fee:
        failures.append(f"UNKNOWN rows with nonzero fees = {unk_fee} (must be 0)")
    if unk_n:
        failures.append(
            f"UNKNOWN phase-1 MPLAN count = {unk_n} "
            "(clean acceptance requires 0 absent documented waiver)"
        )
    if non_n and non_fee == 0:
        failures.append(
            "confirmed NON_ISWL MANNLFEE>0 = 0 — non-ISWL fees not restored "
            "(stale fleet-wide suppression Output or wipe)"
        )

    # Rider phases must not be used for classification — spot-check: if a policy
    # has ISWL base and non-ISWL rider, base class remains ISWL (already enforced
    # by phase-1-only cohort build). Count rider rows ignored:
    rider_n = sum(1 for r in ridr if (r.get("MPHASE") or "").strip() not in ("1", "01", ""))
    print(f"rider_phase_rows_ignored_for_classification={rider_n}")

    audit = os.path.join(REPORTS, "policy_fee_suppression_audit.csv")
    if os.path.isfile(audit):
        rows = _read_csv(audit)
        bad_cls = [
            r for r in rows
            if (r.get("CLASSIFICATION") or "").strip() not in ("", "ISWL", "UNKNOWN")
        ]
        if bad_cls:
            failures.append(
                f"audit has {len(bad_cls)} rows with non-suppress class "
                "(non-ISWL must not be subtracted)"
            )
        print(f"audit_rows={len(rows)}")

    if failures:
        print("FAIL")
        for f in failures:
            print(" ", f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
