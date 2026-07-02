"""
ISWL Phase 1 — V-CVS-01: PSEGT CV gate for 8/8 ISWL coverages.

Usage:
  python tools/validators/iswl_psegt_cv_gate.py
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.validators.iswl_common import (
    ISWL_COVERAGE_IDS,
    ensure_phase1_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"


def _load_psegt_types(path: Path) -> dict[str, set[str]]:
    types_by_seg: dict[str, set[str]] = defaultdict(set)
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        for row in rd:
            seg = (row.get("SEGMENT_ID") or "").strip()
            typ = (row.get("SEGT_TYPE") or "").strip()
            if seg and typ:
                types_by_seg[seg].add(typ)
    return types_by_seg


def _load_pcovrsgt_slots(path: Path) -> dict[str, list[str]]:
    """COVERAGE_ID -> list of active SEGT_ID (SEGT_FLAG=Y)."""
    slots: dict[str, list[str]] = defaultdict(list)
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        col = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            cov = row[col["COVERAGE_ID"]].strip()
            if cov not in ISWL_COVERAGE_IDS:
                continue
            if row[col["SEGT_FLAG"]].strip().upper() != "Y":
                continue
            seg = row[col["SEGT_ID"]].strip()
            if seg:
                slots[cov].append(seg)
    return dict(slots)


def main() -> int:
    cfg = load_config()
    psegt_path = resolve_path(cfg, "psegt_csv")
    psgt_path = resolve_path(cfg, "pcovrsgt_csv")
    out_dir = ensure_phase1_out()
    report_path = out_dir / "iswl_psegt_cv_gate_report.csv"

    errors: list[str] = []
    if not psegt_path.is_file():
        print(f"FAIL — PSEGT not found: {psegt_path}")
        return 1
    if not psgt_path.is_file():
        print(f"FAIL — PCOVRSGT not found: {psgt_path}")
        return 1

    psegt_types = _load_psegt_types(psegt_path)
    slots = _load_pcovrsgt_slots(psgt_path)

    rows_out = []
    passed = 0
    for cov in sorted(ISWL_COVERAGE_IDS):
        segt_ids = slots.get(cov, [])
        cv_found = False
        cv_segments = []
        for seg in segt_ids:
            if "CV" in psegt_types.get(seg, set()):
                cv_found = True
                cv_segments.append(seg)
        status = "PASS" if cv_found else "FAIL"
        if cv_found:
            passed += 1
        else:
            errors.append(f"{cov}: no PSEGT CV on slots {segt_ids}")
        rows_out.append({
            "COVERAGE_ID": cov,
            "SEGT_IDS": "|".join(segt_ids),
            "CV_SEGMENTS": "|".join(cv_segments),
            "STATUS": status,
        })

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["COVERAGE_ID", "SEGT_IDS", "CV_SEGMENTS", "STATUS"])
        w.writeheader()
        w.writerows(rows_out)

    print("=" * 72)
    print(f"ISWL PSEGT CV GATE v{SCRIPT_VERSION} — V-CVS-01")
    print(f"PSEGT: {psegt_path}")
    print(f"PCOVRSGT: {psgt_path}")
    print(f"Coverages with CV: {passed}/{len(ISWL_COVERAGE_IDS)}")
    print(f"Report: {report_path}")
    print("=" * 72)

    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        return 1
    print("PASS — 8/8 ISWL coverages have PSEGT CV capability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
