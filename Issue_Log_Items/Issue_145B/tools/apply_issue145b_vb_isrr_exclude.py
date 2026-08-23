#!/usr/bin/env python3
"""Issue 145B — strip already-emitted VB 0561 history from current Output.

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

from qla_core.issue145b_vb_isrr import is_vb_policy
from qla_core.quikisrr_loader import QUIKBENH_FIELDS, QUIKISRR_FIELDS, write_csv_rows
from qla_core.quikspec_vanish import load_ppolc_billing_reason

OUT = REPO / "QLA_Migration" / "Output"
SRC = REPO / "QLA_Migration" / "Source"
EVIDENCE = REPO / "Issue_Log_Items" / "Issue_145B" / "evidence"
GOLD_VB = ("9010815236C", "9011050114C", "9011069610C")
GOLD_146 = ("9010761639C", "9010760840C")


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
    reasons = load_ppolc_billing_reason(str(SRC))
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

    def vb(row: dict) -> bool:
        return is_vb_policy(str(row.get("MPOLICY") or ""), reasons)

    isrr_keep = [r for r in isrr_rows if not vb(r)]
    clms_keep = [r for r in clms_rows if not (vb(r) and _is_ps_clms(r))]
    clmp_keep = [r for r in clmp_rows if not (vb(r) and _is_phase0(r))]
    benh_keep = [r for r in benh_rows if not (vb(r) and _is_type8(r))]

    write_csv_rows(isrr_path, isrr_fields or QUIKISRR_FIELDS, isrr_keep)
    write_csv_rows(clms_path, clms_fields, clms_keep)
    write_csv_rows(clmp_path, clmp_fields, clmp_keep)
    write_csv_rows(benh_path, benh_fields or QUIKBENH_FIELDS, benh_keep)

    audit = {
        "issue": "145B",
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
        "gold_vb": GOLD_VB,
        "gold_146": GOLD_146,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_json = EVIDENCE / "issue145b_apply_summary.json"
    out_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
