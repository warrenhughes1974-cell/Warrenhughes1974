"""
Issue #124 — QuikIswl month-0 seed validation.

Superseded 2026-09-24 (Warren): Issue #155 full PFNDRDET history replaces month-0 rows.
This validator now asserts the #155 history shape (no month-0 at issue) and exits 0.

Usage:
  python tools/validators/validate_issue124_quikiswl.py
  python tools/validators/validate_issue124_quikiswl.py --publish-test-validation
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.quikiswl_loader import (  # noqa: E402
    OUTPUT_FILENAME,
    QUIKISWL_FIELDS,
    _load_issue_dates,
    _s,
)

SCRIPT_VERSION = "2.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_124" / "evidence"
OVERRIDE_NOTE = (
    "Issue #124 month-0 expectation superseded by Issue #155 (Warren 2026-09-24): "
    "QuikIswl carries full LifePRO PFNDRDET history; no MMONTH=0 row at issue date."
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #124 / #155 QuikIswl shape")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    out = args.output_dir
    iswl_path = out / OUTPUT_FILENAME
    if not iswl_path.exists():
        alt = out / "quikiswl.csv"
        if alt.exists():
            iswl_path = alt

    print(f"validate_issue124_quikiswl.py v{SCRIPT_VERSION}")
    print(OVERRIDE_NOTE)
    print(f"output: {out}")

    fails: list[str] = []
    if not iswl_path.is_file():
        print(f"FAIL: missing {OUTPUT_FILENAME}")
        return 1

    with iswl_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        actual = list(reader)

    if fields != QUIKISWL_FIELDS:
        fails.append(f"schema mismatch: got {fields[:5]}... expected QUIKISWL_FIELDS")

    issue_dates = _load_issue_dates(out / "quikmstr.csv")
    month0_issue = [
        r
        for r in actual
        if _s(r.get("MMONTH")) == "0"
        and _s(r.get("MACCTBAL")) == "0.00"
        and _norm_date(r.get("MLASTANNV")) == issue_dates.get(_s(r.get("MPOLICY")), "")
    ]
    if month0_issue:
        fails.append(
            f"{len(month0_issue)} legacy month-0 rows at issue date (Issue #155 removes these)"
        )

    if len(actual) < 500:
        fails.append(f"QuikIswl row count {len(actual)} — expected full PFNDRDET history")

    keys = Counter(
        (_s(r.get("MPOLICY")), _norm_date(r.get("MLASTANNV"))) for r in actual
    )
    dups = sum(1 for _, c in keys.items() if c > 1)
    if dups:
        fails.append(f"{dups} duplicate MPOLICY+MLASTANNV keys")

    print(f"QuikIswl rows: {len(actual)} (legacy month-0 at issue: {len(month0_issue)})")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = {
        "validator": "validate_issue124_quikiswl.py",
        "version": SCRIPT_VERSION,
        "override": OVERRIDE_NOTE,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": len(actual),
        "month0_at_issue": len(month0_issue),
        "fails": fails,
        "pass": not fails,
    }
    (EVIDENCE / "issue124_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    if fails:
        print("FAIL:")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("PASS (#155 history shape; #124 month-0 waived)")
    if args.publish_test_validation:
        tv = out / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        dest = tv / OUTPUT_FILENAME
        shutil.copy2(iswl_path, dest)
        print(f"Published {dest}")
    return 0


def _norm_date(v: object) -> str:
    d = "".join(ch for ch in _s(v) if ch.isdigit())
    return d[:8] if len(d) >= 8 else ""


if __name__ == "__main__":
    raise SystemExit(main())
