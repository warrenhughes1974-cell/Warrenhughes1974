#!/usr/bin/env python3
"""
Issue #34 PR-7 — emit ISWL partial surrender history package.

Appends QuikClms/QuikClmp partial-surrender rows; creates QuikBenh and QuikIsrr.

Usage:
  python Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py
  python Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.quikisrr_loader import (
    QUIKBENH_FIELDS,
    QUIKCLMS_FIELDS,
    QUIKCLMP_FIELDS,
    QUIKISRR_FIELDS,
    EmitResult,
    build_emit,
    fmt_amount,
    read_csv_rows,
    write_csv_rows,
)

OUT_DIR = PROJECT_ROOT / "QLA_Migration" / "Output"
ARTIFACT_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_34" / "output" / "PR7_QUIKISRR"
# Pre-#145B floor (all ISWL 0561s). After #145B the leftover book is extract-dependent.
# Do not fail emit on this stale count. Fail if any VB event is still a candidate.
EXPECTED_PRE_145B = {"rows": 3657, "policies": 637, "amount": 1232602.53}


def _row_hash(rows: list[dict], fields: list[str]) -> str:
    h = hashlib.sha256()
    for row in rows:
        h.update("|".join(row.get(f, "") for f in fields).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _write_artifact_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        write_csv_rows(path, fields or [], [])
        return
    flds = fields or list(rows[0].keys())
    write_csv_rows(path, flds, rows)


def _event_csv_rows(events) -> list[dict]:
    return [
        {
            "policy_number": e.policy_number,
            "mpolicy": e.mpolicy,
            "mplan": e.mplan,
            "mplan_source": e.mplan_source,
            "effective_date": e.effective_date,
            "date_added": e.date_added,
            "trans_amount": fmt_amount(e.trans_amount),
            "mseq": e.mseq,
            "record_sequence": e.record_sequence,
        }
        for e in events
    ]


def emit_package(dry_run: bool = False) -> dict:
    clms_path = OUT_DIR / "quikclms.csv"
    clmp_path = OUT_DIR / "quikclmp.csv"
    benh_path = OUT_DIR / "quikbenh.csv"
    isrr_path = OUT_DIR / "QuikIsrr.csv"

    clms_fields, clms_existing = read_csv_rows(clms_path)
    clmp_fields, clmp_existing = read_csv_rows(clmp_path)
    clms_before_hash = _row_hash(clms_existing, clms_fields)
    clmp_before_hash = _row_hash(clmp_existing, clmp_fields)

    result: EmitResult = build_emit(PROJECT_ROOT)

    candidate_policies = {e.policy_number for e in result.candidates}
    candidate_amount = sum(e.trans_amount for e in result.candidates)
    vb_policies = {e.policy_number for e in result.vb_excluded}
    issue146_policies = {e.policy_number for e in result.issue146_excluded}

    summary = {
        "emit_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dry_run": dry_run,
        "candidate_population": {
            "rows": len(result.candidates),
            "policies": len(candidate_policies),
            "gross_amount": round(candidate_amount, 2),
            "expected_rows_pre_145b": EXPECTED_PRE_145B["rows"],
            "expected_policies_pre_145b": EXPECTED_PRE_145B["policies"],
            "expected_amount_pre_145b": EXPECTED_PRE_145B["amount"],
            "vb_excluded_rows": len(result.vb_excluded),
            "vb_excluded_policies": len(vb_policies),
            "vb_leak_policies": sorted(candidate_policies & vb_policies),
            "issue146_excluded_rows": len(result.issue146_excluded),
            "issue146_excluded_policies": len(issue146_policies),
            "issue146_leak_policies": sorted(candidate_policies & issue146_policies),
        },
        "emitted": {
            "rows": len(result.emitted_events),
            "policies": len({e.mpolicy for e in result.emitted_events}),
            "gross_amount": round(sum(e.trans_amount for e in result.emitted_events), 2),
        },
        "exceptions": {
            "payee_exception_rows": len(result.payee_exceptions),
            "hold_rows": len(result.hold_rows),
            "reversal_excluded_rows": len(result.reversal_excluded),
        },
        "existing_preserved": {
            "quikclms_before_rows": len(clms_existing),
            "quikclmp_before_rows": len(clmp_existing),
            "quikclms_before_hash": clms_before_hash,
            "quikclmp_before_hash": clmp_before_hash,
        },
        "outputs": {},
    }

    if not dry_run:
        clms_out = clms_existing + result.clms_rows
        clmp_out = clmp_existing + result.clmp_rows
        write_csv_rows(clms_path, clms_fields, clms_out)
        write_csv_rows(clmp_path, clmp_fields, clmp_out)
        # Preserve Issue #54 loan history (MBENTYP 10/11/12) — only replace type-8 (ISRR) rows.
        _, benh_existing = read_csv_rows(benh_path)
        benh_keep = [
            r for r in benh_existing
            if str(r.get("MBENTYP", "")).strip() not in ("8", "8.0")
        ]
        benh_out = benh_keep + result.benh_rows
        write_csv_rows(benh_path, QUIKBENH_FIELDS, benh_out)
        write_csv_rows(isrr_path, QUIKISRR_FIELDS, result.isrr_rows)

        _, clms_after_existing = read_csv_rows(clms_path)
        _, clmp_after_existing = read_csv_rows(clmp_path)
        clms_after_hash = _row_hash(clms_after_existing[: len(clms_existing)], clms_fields)
        clmp_after_hash = _row_hash(clmp_after_existing[: len(clmp_existing)], clmp_fields)
        summary["existing_preserved"]["quikclms_after_prefix_hash"] = clms_after_hash
        summary["existing_preserved"]["quikclmp_after_prefix_hash"] = clmp_after_hash
        summary["existing_preserved"]["quikclms_prefix_unchanged"] = clms_before_hash == clms_after_hash
        summary["existing_preserved"]["quikclmp_prefix_unchanged"] = clmp_before_hash == clmp_after_hash
        summary["outputs"] = {
            "quikclms.csv": {"rows": len(clms_out), "appended": len(result.clms_rows)},
            "quikclmp.csv": {"rows": len(clmp_out), "appended": len(result.clmp_rows)},
            "quikbenh.csv": {
                "rows": len(benh_out),
                "preserved_non_type8": len(benh_keep),
                "type8_isrr": len(result.benh_rows),
                "mode": "merge_preserve_loan_history",
            },
            "QuikIsrr.csv": {"rows": len(result.isrr_rows), "miswl": "omitted"},
        }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_candidate_population.csv", _event_csv_rows(result.candidates))
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_emitted_events.csv", _event_csv_rows(result.emitted_events))
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_reversal_excluded.csv", result.reversal_excluded)
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_policy_9010780411_hold.csv", result.hold_rows)
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_payee_exceptions.csv", result.payee_exceptions)
    _write_artifact_csv(ARTIFACT_DIR / "quikisrr_sequence_audit.csv", result.sequence_audit)
    if result.product_id_fallbacks:
        _write_artifact_csv(ARTIFACT_DIR / "quikisrr_product_id_fallbacks.csv", result.product_id_fallbacks)

    with open(ARTIFACT_DIR / "quikisrr_validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #34 PR-7 QuikIsrr package emit")
    parser.add_argument("--dry-run", action="store_true", help="Build artifacts only; do not write Output/")
    args = parser.parse_args()

    summary = emit_package(dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))

    pop = summary["candidate_population"]
    if pop.get("vb_excluded_rows", 0) < 1:
        print("FAIL: Issue 145B VB exclude produced 0 drops — PPOLC VB join missed")
        return 2
    if pop.get("vb_leak_policies"):
        print("FAIL: VB policies still in leftover candidates")
        return 2
    if pop.get("issue146_leak_policies"):
        print("FAIL: Issue 146 allowlist policies still in leftover candidates")
        return 2
    if pop["rows"] < 1:
        print("FAIL: leftover non-VB QuikIsrr candidates is 0")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
