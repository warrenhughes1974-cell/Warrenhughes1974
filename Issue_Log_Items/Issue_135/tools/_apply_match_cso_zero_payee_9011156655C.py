#!/usr/bin/env python3
"""Issue #135 — surgical apply MATCH_CSO zero-payee backfill for 9011156655C only.

Mutates QLA_Migration/Output/quikclmp.csv only (append). quikclms unchanged.
Archives pre-change quikclmp; publishes updated quikclmp to Output/Test_Validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_match_cso_zero_payee_backfill import (  # noqa: E402
    apply_match_cso_zero_payee_backfill,
    write_zero_payee_backfill_audit,
)

TOOLS_135 = ROOT / "Issue_Log_Items" / "Issue_135" / "tools"
sys.path.insert(0, str(TOOLS_135))
from issue135_cso_pactg_recon import resolve_pactg  # noqa: E402

DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_PRELSA = ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"
DEFAULT_ARCHIVE = ROOT / "QLA_Migration" / "Archive"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
TV = ROOT / "QLA_Migration" / "Output" / "Test_Validation"
POL = "9011156655C"


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    clms_path = DEFAULT_CLMS
    clmp_path = DEFAULT_CLMP
    if not clms_path.is_file() or not clmp_path.is_file():
        print("FAIL: missing quikclms/quikclmp")
        return 2
    if not DEFAULT_PRELSA.is_file():
        print("FAIL: missing PRELSA/RNA")
        return 2

    pactg = resolve_pactg(None)
    if not Path(pactg).is_file():
        print(f"FAIL: missing PACTG ({pactg})")
        return 2

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    before_clmp = len(clmp)
    before_pol = int((clmp["MPOLICY"].astype(str).str.strip() == POL).sum())
    before_sha = _file_sha(clmp_path)

    clms_after, clmp_after, stats = apply_match_cso_zero_payee_backfill(
        clms,
        clmp,
        prelsa_path=DEFAULT_PRELSA,
        pactg_path=pactg,
    )
    paths = write_zero_payee_backfill_audit(stats, EVIDENCE)

    # Prove quikclms byte-stable money for this policy
    before_hdr = clms[clms["MPOLICY"].astype(str).str.strip() == POL].copy()
    after_hdr = clms_after[clms_after["MPOLICY"].astype(str).str.strip() == POL].copy()
    money_cols = ["MPAID", "MFACE", "NETDB", "MINTAMT", "PREMIUM", "DIVIDENDS", "LOAN", "CLAIMSTAT"]
    money_ok = before_hdr[money_cols].reset_index(drop=True).equals(
        after_hdr[money_cols].reset_index(drop=True)
    )

    print("Issue #135 MATCH_CSO zero-payee backfill (9011156655C)")
    print(f"  dry_run={args.dry_run}")
    print(f"  clmp {before_clmp} -> {len(clmp_after)} (pol_rows {before_pol} -> "
          f"{int((clmp_after['MPOLICY'].astype(str).str.strip()==POL).sum())})")
    print(f"  applied={stats.get('applied')} rows_added={stats.get('rows_added')} "
          f"policies={stats.get('policies_backfilled')}")
    print(f"  skipped={stats.get('skipped')}")
    print(f"  header_money_unchanged={money_ok}")
    print(f"  artifacts={paths}")

    if not stats.get("applied"):
        print("FAIL: backfill not applied")
        return 1
    if not money_ok:
        print("FAIL: quikclms money fields changed")
        return 1

    if args.dry_run:
        print("DRY-RUN: Output not written")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    DEFAULT_ARCHIVE.mkdir(parents=True, exist_ok=True)
    arch = DEFAULT_ARCHIVE / f"quikclmp_pre_issue135_9011156655C_{ts}.csv"
    shutil.copy2(clmp_path, arch)
    evid_arch = EVIDENCE / f"quikclmp_pre_issue135_9011156655C_{ts}.csv"
    shutil.copy2(clmp_path, evid_arch)

    tmp = clmp_path.with_suffix(".csv.tmp")
    clmp_after.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(clmp_path)

    TV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clmp_path, TV / "quikclmp.csv")

    meta = {
        "policy": POL,
        "reason": "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE",
        "before_clmp_rows": before_clmp,
        "after_clmp_rows": int(len(clmp_after)),
        "before_policy_payee_rows": before_pol,
        "after_policy_payee_rows": int(
            (clmp_after["MPOLICY"].astype(str).str.strip() == POL).sum()
        ),
        "rows_added": int(stats.get("rows_added", 0) or 0),
        "pre_archive": str(arch),
        "evidence_archive": str(evid_arch),
        "pre_sha256": before_sha,
        "post_sha256": _file_sha(clmp_path),
        "test_validation": str(TV / "quikclmp.csv"),
        "quikclms_mutated": False,
        "header_money_unchanged": money_ok,
    }
    (EVIDENCE / "issue135_9011156655C_apply_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"  archived {arch}")
    print(f"  wrote {clmp_path}")
    print(f"  published {TV / 'quikclmp.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
