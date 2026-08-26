#!/usr/bin/env python3
"""Issue 146 — strip already-emitted allowlist 0561 history from current Output.

Does not re-run PR-7 emit (that appends quikclms/quikclmp).
Does not touch PACTG, quikridr, quikmstr, or quikspec.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from qla_core.issue146_pc_isrr import is_issue146_keep_policy, is_issue146_policy
from qla_core.quikisrr_loader import QUIKBENH_FIELDS, QUIKISRR_FIELDS, write_csv_rows

OUT = REPO / "QLA_Migration" / "Output"
EVIDENCE = REPO / "Issue_Log_Items" / "Issue_146" / "evidence"
GOLD_REMOVE = ("9011077629C", "9010817956C", "9010808831C")
GOLD_KEEP = ("9010761639C", "9010760840C")


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, [dict(r) for r in reader]


def _is_ps_clms(row: dict) -> bool:
    claim = str(row.get("CLAIMNUM") or "")
    cause = str(row.get("CAUSE") or "").strip().upper()
    phase = str(row.get("MPHASE") or "").strip()
    return claim.startswith("PS-") or cause == "SRR" or phase == "0"


def _is_type8(row: dict) -> bool:
    return str(row.get("MBENTYP") or "").strip() in ("8", "8.0")


def _is_phase0(row: dict) -> bool:
    return str(row.get("MPHASE") or "").strip() in ("0", "0.0")


def main() -> int:
    isrr_path = OUT / "QuikIsrr.csv"
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    benh_path = OUT / "quikbenh.csv"
    for p in (isrr_path, clms_path, clmp_path, benh_path):
        if not p.is_file():
            print(f"FAIL missing {p}")
            return 1

    isrr_fields, isrr_rows = _read(isrr_path)
    clms_fields, clms_rows = _read(clms_path)
    clmp_fields, clmp_rows = _read(clmp_path)
    benh_fields, benh_rows = _read(benh_path)

    def allow(row: dict) -> bool:
        return is_issue146_policy(str(row.get("MPOLICY") or ""))

    isrr_keep = [r for r in isrr_rows if not allow(r)]
    clms_keep = [r for r in clms_rows if not (allow(r) and _is_ps_clms(r))]
    clmp_keep = [r for r in clmp_rows if not (allow(r) and _is_phase0(r))]
    benh_keep = [r for r in benh_rows if not (allow(r) and _is_type8(r))]

    write_csv_rows(isrr_path, isrr_fields or QUIKISRR_FIELDS, isrr_keep)
    write_csv_rows(clms_path, clms_fields, clms_keep)
    write_csv_rows(clmp_path, clmp_fields, clmp_keep)
    write_csv_rows(benh_path, benh_fields or QUIKBENH_FIELDS, benh_keep)

    leftover_keep_gold = sum(
        1 for r in isrr_keep if is_issue146_keep_policy(str(r.get("MPOLICY") or ""))
    )
    audit = {
        "issue": "146",
        "applied_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "before": {
            "QuikIsrr": len(isrr_rows),
            "quikclms": len(clms_rows),
            "quikclmp": len(clmp_rows),
            "quikbenh": len(benh_rows),
        },
        "after": {
            "QuikIsrr": len(isrr_keep),
            "quikclms": len(clms_keep),
            "quikclmp": len(clmp_keep),
            "quikbenh": len(benh_keep),
        },
        "removed": {
            "QuikIsrr": len(isrr_rows) - len(isrr_keep),
            "quikclms": len(clms_rows) - len(clms_keep),
            "quikclmp": len(clmp_rows) - len(clmp_keep),
            "quikbenh": len(benh_rows) - len(benh_keep),
        },
        "leftover_keep_gold_isrr": leftover_keep_gold,
        "gold_remove": GOLD_REMOVE,
        "gold_keep": GOLD_KEEP,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_json = EVIDENCE / "issue146_apply_summary.json"
    out_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if leftover_keep_gold < 3:
        print("FAIL keep golds missing after strip")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
