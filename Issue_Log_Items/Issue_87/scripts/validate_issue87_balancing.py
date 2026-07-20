#!/usr/bin/env python3
"""Issue #87 — validate QuikForge Balancing report (Governance-style layout)."""
from __future__ import annotations

import csv
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qla_core.balancing import REPORT_COLUMNS, run_balancing  # noqa: E402

SRC = os.path.join(REPO_ROOT, "QLA_Migration", "Source")
OUT = os.path.join(REPO_ROOT, "QLA_Migration", "Output")
BAL = os.path.join(REPO_ROOT, "QLA_Migration", "Balancing")
CW = os.path.join(REPO_ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv")
EXC = os.path.join(REPO_ROOT, "QLA_Migration", "Configs", "balancing_exclusions.csv")
METH = os.path.join(BAL, "Balancing_Methodology.md")


def main() -> int:
    errors: list[str] = []

    if not os.path.isfile(METH):
        errors.append(f"Missing methodology: {METH}")
    if not os.path.isdir(SRC):
        errors.append(f"Missing source dir: {SRC}")
    if not os.path.isdir(OUT):
        errors.append(f"Missing output dir: {OUT}")

    summary = run_balancing(
        src_dir=SRC,
        out_dir=OUT,
        balancing_dir=BAL,
        crosswalk_path=CW,
        exclusions_path=EXC,
    )

    html_path = summary.get("what_was_checked_path") or ""
    attention = summary.get("attention_csv_path") or ""
    totals = summary.get("control_totals_path") or ""
    run_folder = summary.get("run_folder") or ""

    if not html_path or not os.path.isfile(html_path):
        errors.append("Missing 1_What_Was_Checked.html")
    else:
        text = open(html_path, encoding="utf-8").read()
        for needle in ("Executive Summary", "Overall Result", "What We Checked", "What To Do Next"):
            if needle not in text:
                errors.append(f"HTML missing section: {needle}")

    if not attention or not os.path.isfile(attention):
        errors.append("Missing 2_Items_Needing_Attention.csv")
    else:
        with open(attention, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            errors.append("Attention CSV is empty")
        elif "Problem / Explanation" not in rows[0]:
            errors.append(f"Unexpected attention columns: {list(rows[0].keys())}")

    if not totals or not os.path.isfile(totals):
        errors.append("Missing internal/balancing_control_totals.csv")
    else:
        with open(totals, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            errors.append("Control totals CSV is empty")
        elif list(rows[0].keys()) != REPORT_COLUMNS:
            errors.append(f"Unexpected totals columns: {list(rows[0].keys())}")
        ids = {r["CONTROL_ID"] for r in rows}
        for required in ("BAL-C01", "BAL-C02", "BAL-I01", "BAL-I02"):
            if required not in ids:
                errors.append(f"Missing control {required}")

    if run_folder and not os.path.basename(run_folder).startswith("BAL-"):
        errors.append(f"Run folder naming unexpected: {run_folder}")

    for name in os.listdir(OUT):
        if name.startswith("Balancing_") or name.startswith("BAL-"):
            errors.append(f"Output hygiene violation: {name} in Output/")

    print("Issue #87 Balancing validation")
    print(f"  Run folder: {run_folder}")
    print(f"  What Was Checked: {html_path}")
    print(f"  Attention CSV: {attention}")
    print(
        f"  PASS={summary.get('pass_count')} "
        f"EXPLAINED={summary.get('explained_count')} "
        f"FAIL={summary.get('fail_count')}"
    )
    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
