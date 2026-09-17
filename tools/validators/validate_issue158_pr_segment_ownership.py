"""Issue #158 — PR premium grids must sit on the plan that owns the segment at PCOVRSGT SEQ 1.

Fail-closed release smoke. Exits 1 when a premium rate segment is attributed to a plan
that does not carry it in the SEQ 1 (PR) slot, when a segment carried at SEQ 1 by more
than one coverage fails to reach every one of those plans, or when two different LifePRO
segments write the same QuikGps cell.

Checks run against the emitted loader stream, and against full QLA_Migration/Output/
rates/QuikGps.csv when it is present.

Usage:
    python tools/validators/validate_issue158_pr_segment_ownership.py
    python tools/validators/validate_issue158_pr_segment_ownership.py --json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core import paagerat_pr_loader as PA  # noqa: E402
from qla_core import rate_segment_resolution as SR  # noqa: E402
from qla_core.plan_source_paths import (  # noqa: E402
    pcovr_csv,
    pcovrsgt_csv,
    policy_form_crosswalk,
)
from qla_core.rate_factor_loader import LoaderConfig, load_plan_crosswalk  # noqa: E402

QUIKGPS = os.path.join(ROOT, "QLA_Migration", "Output", "rates", "QuikGps.csv")

# Segments proven mis-attributed at Issue #158 Planning (2026-08-29). Each must land on
# every listed plan and on no other. Anchors the 12 LifePRO screenshots in
# docs/Rate_Validation plus the L10 / GL LP85 families found during simulation.
GOLD_OWNERSHIP = {
    "0822 960PO": ["960ADB", "9POADB"],
    "10827 CSI5": ["17CSI5", "1CSIMN"],
    "1576 658": ["976658"],
    "1576 659": ["976659"],
    "1578 FTR": ["778FTR"],
    "1596": ["901ADB", "996ADB"],
    "619 DT SP": ["719SDT"],
    "620 END85": ["221END"],
    "666 WL": ["1666AI", "1666WL"],
    "686S 30MRG": ["7686S3"],
    "8286 GI": ["986JPO"],
    "961 ME65": ["2961ME"],
    "980 END65": ["280END"],
    "GL LP85": ["170588", "170858", "17085M"],
    "L10 LP95": ["1L1095"],
    "L10 LP95SR": ["1L10SR"],
    "L10 PRE97": ["1L10OD"],
    "L15": ["1L15GD"],
    "L17": ["10L171", "117JPO"],
    "L17 2+": ["10L172", "17MJPO"],
}

# Plans that must NOT carry these segments' premium rates any more (the pre-fix owners).
FORBIDDEN = {
    "1658CS": ["1576 658"],
    "1669SR": ["1576 659"],
    "1L10SO": ["L10 LP95", "L10 LP95SR", "L10 PRE97"],
    "1L16GD": ["L15"],
    "1L17SP": ["L17"],
    "222END": ["620 END85"],
    "261PUA": ["961 ME65"],
    "280PUA": ["980 END65"],
    "578STR": ["1578 FTR"],
    "7619PU": ["619 DT SP"],
    "7687J3": ["686S 30MRG"],
    "9JPO10": ["8286 GI"],
}

# Plans that carry no PCOVRSGT SEQ 1 segment at all, so PAAGERAT must not give them a
# premium grid. 1658CS / 1669SR are excluded: PR is suppressed there because PAAGERAT BP
# is the billable-premium authority for the ISWL MPLANs (Issue #31 Phase 2).
NO_PR_SEGMENT_PLANS = ["1L17SP", "222END", "261PUA", "280PUA", "578STR", "7619PU"]


def _paagerat_path():
    src = os.path.join(ROOT, "QLA_Migration", "Source")
    cands = sorted(
        f for f in os.listdir(src)
        if f.startswith("PAAGERAT_AttainedAge_Rates_Extract_") and f.endswith(".csv")
    )
    return os.path.join(src, cands[-1]) if cands else None


def stream_attribution():
    """segment -> set(plan) and cell -> set(segment) from the live PR loader."""
    pa = _paagerat_path()
    if not pa:
        return None, None, "PAAGERAT extract not found in QLA_Migration/Source"
    cov2plan, _ = load_plan_crosswalk(policy_form_crosswalk())
    resolver = SR.SegmentResolver.from_files(pcovrsgt_csv(), pcovr_csv(), cov2plan)
    seg_plans = defaultdict(set)
    cells = defaultdict(set)
    for t in PA.transform_paagerat_pr(pa, resolver, LoaderConfig()):
        if t.get("status") != "IN_SCOPE":
            continue
        seg_plans[t["coverage_id"]].add(t["plan"])
        cells[(t["plan"], t["gender"], t["uwclass"], t["band"],
               t["cntl"], t["col"])].add(t["coverage_id"])
    return seg_plans, cells, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    failures = []
    warnings = []

    seg_plans, cells, err = stream_attribution()
    if err:
        print(f"FAIL Issue #158 — {err}")
        return 1

    # 1. Every gold segment lands on exactly its SEQ 1 owners.
    for seg, expected in sorted(GOLD_OWNERSHIP.items()):
        got = sorted(seg_plans.get(seg, []))
        if got != sorted(expected):
            failures.append({
                "check": "OWNERSHIP",
                "segment": seg,
                "expected": sorted(expected),
                "got": got,
            })

    # 2. No plan carries a segment it lost.
    for plan, segs in sorted(FORBIDDEN.items()):
        for seg in segs:
            if plan in seg_plans.get(seg, set()):
                failures.append({
                    "check": "FORBIDDEN",
                    "plan": plan,
                    "segment": seg,
                    "detail": f"{plan} still carries premium rates from {seg}",
                })

    # 3. No QuikGps cell is written by two different LifePRO segments.
    collisions = {k: sorted(v) for k, v in cells.items() if len(v) > 1}
    if collisions:
        by_plan = defaultdict(set)
        for k, v in collisions.items():
            by_plan[k[0]] |= set(v)
        failures.append({
            "check": "COLLISION",
            "cells": len(collisions),
            "plans": {p: sorted(s) for p, s in sorted(by_plan.items())},
        })

    # 4. Emitted Output must show the gained plans (skipped when Output absent).
    if os.path.isfile(QUIKGPS):
        emitted = set()
        with open(QUIKGPS, newline="", encoding="utf-8-sig", errors="replace") as f:
            for r in csv.DictReader(f):
                p = (r.get("PLAN") or "").strip()
                if p:
                    emitted.add(p)
        expected_plans = {p for plans in GOLD_OWNERSHIP.values() for p in plans}
        missing = sorted(expected_plans - emitted)
        if missing:
            failures.append({
                "check": "OUTPUT_MISSING_PLANS",
                "detail": "plans own a PR segment but have no QuikGps rows",
                "plans": missing,
            })
        # Plans with no SEQ 1 premium segment. They may still be fed by Rate_Table,
        # inheritance or PDAGE miss-fill, so presence is reported, not failed.
        for plan in sorted(NO_PR_SEGMENT_PLANS):
            if plan in emitted:
                warnings.append({
                    "check": "OUTPUT_NO_PR_SEGMENT_PLAN_PRESENT",
                    "plan": plan,
                    "detail": "no SEQ 1 segment; confirm rows come from another rate source",
                })
    else:
        warnings.append({"check": "OUTPUT_ABSENT",
                         "detail": "rates/QuikGps.csv not found — loader-only check"})

    result = {
        "issue": "158",
        "status": "FAIL" if failures else "PASS",
        "segments_checked": len(GOLD_OWNERSHIP),
        "plans_guarded": len(FORBIDDEN),
        "multi_segment_cells": len(collisions),
        "failures": failures,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Issue #158 PR segment ownership — {result['status']}")
        print(f"  segments checked : {result['segments_checked']}")
        print(f"  plans guarded    : {result['plans_guarded']}")
        print(f"  colliding cells  : {result['multi_segment_cells']}")
        for w in warnings:
            print(f"  WARN {w['check']}: {w.get('detail', '')} {w.get('plan', '')}")
        for f in failures:
            print(f"  FAIL {f['check']}: "
                  f"{f.get('segment') or f.get('plan') or ''} "
                  f"{f.get('detail') or f.get('expected', '')} "
                  f"{f.get('got', '') or f.get('plans', '')}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
