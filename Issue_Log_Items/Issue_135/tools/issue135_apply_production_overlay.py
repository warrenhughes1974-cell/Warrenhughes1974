#!/usr/bin/env python3
"""Issue #135 — apply controlled Option-3 + 459 expansion to Output (no full rebatch).

Mutates only quikclms.csv / quikclmp.csv under QLA_Migration/Output.
Writes audits under Issue_Log_Items/Issue_135/evidence/ (not Output root).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_cso_claims_expansion import (  # noqa: E402
    apply_issue135_cso_claims_expansion,
    write_issue135_expansion_audits,
)

DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_ARCHIVE = ROOT / "QLA_Migration" / "Archive"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
REPORTS = ROOT / "QLA_Migration" / "Reports"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clms", default=str(DEFAULT_CLMS))
    ap.add_argument("--clmp", default=str(DEFAULT_CLMP))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    clms_path = Path(args.clms)
    clmp_path = Path(args.clmp)
    if not clms_path.is_file() or not clmp_path.is_file():
        print("FAIL: missing quikclms/quikclmp")
        return 2

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    before_clms, before_clmp = len(clms), len(clmp)

    clms_after, clmp_after, stats = apply_issue135_cso_claims_expansion(clms, clmp)
    paths = write_issue135_expansion_audits(stats, EVIDENCE, REPORTS)

    print("Issue #135 production apply")
    print(f"  dry_run={args.dry_run}")
    print(f"  clms {before_clms} -> {len(clms_after)}")
    print(f"  clmp {before_clmp} -> {len(clmp_after)}")
    for k in (
        "option3_headers_updated",
        "derived_headers_emitted",
        "derived_payees_emitted",
        "derived_payee_holds",
        "header_only_308_emitted",
        "holds_9",
        "skipped_duplicates",
    ):
        print(f"  {k}={stats.get(k)}")
    print(f"  artifacts={paths}")

    if args.dry_run:
        print("DRY-RUN: Output not written")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    arch = DEFAULT_ARCHIVE
    arch.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clms_path, arch / f"quikclms_pre_issue135_{ts}.csv")
    shutil.copy2(clmp_path, arch / f"quikclmp_pre_issue135_{ts}.csv")

    tmp_clms = clms_path.with_suffix(".csv.tmp")
    tmp_clmp = clmp_path.with_suffix(".csv.tmp")
    clms_after.to_csv(tmp_clms, index=False, encoding="utf-8")
    clmp_after.to_csv(tmp_clmp, index=False, encoding="utf-8")
    tmp_clms.replace(clms_path)
    tmp_clmp.replace(clmp_path)
    print(f"  wrote {clms_path}")
    print(f"  wrote {clmp_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
