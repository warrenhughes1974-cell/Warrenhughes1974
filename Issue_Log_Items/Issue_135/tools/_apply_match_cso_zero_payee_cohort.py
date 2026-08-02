#!/usr/bin/env python3
"""Issue #135 — apply SAFE_BACKFILL payees for MATCH_CSO zero-payee cohort.

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
    discover_safe_allowlist,
    write_zero_payee_backfill_audit,
)

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from issue135_cso_pactg_recon import resolve_pactg  # noqa: E402

DEFAULT_CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
DEFAULT_CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
DEFAULT_PRELSA = ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"
DEFAULT_RECON = (
    ROOT / "Issue_Log_Items" / "Issue_135" / "evidence" / "issue135_cso_output_recon.csv"
)
DEFAULT_ARCHIVE = ROOT / "QLA_Migration" / "Archive"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
TV = ROOT / "QLA_Migration" / "Output" / "Test_Validation"
GOLDEN = "9011156655C"


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

    if not DEFAULT_CLMS.is_file() or not DEFAULT_CLMP.is_file():
        print("FAIL: missing quikclms/quikclmp")
        return 2
    if not DEFAULT_PRELSA.is_file():
        print("FAIL: missing PRELSA/RNA")
        return 2

    pactg = resolve_pactg(None)
    if not Path(pactg).is_file():
        print(f"FAIL: missing PACTG ({pactg})")
        return 2

    clms = pd.read_csv(DEFAULT_CLMS, dtype=str).fillna("")
    clmp = pd.read_csv(DEFAULT_CLMP, dtype=str).fillna("")
    before_clmp = len(clmp)
    before_sha = _file_sha(DEFAULT_CLMP)
    before_zero = int(
        (
            clms[clms["CLAIMSTAT"].astype(str).str.strip() == "2"]["MPOLICY"]
            .astype(str)
            .str.strip()
            .map(
                lambda p: int(
                    (clmp["MPOLICY"].astype(str).str.strip() == p).sum()
                )
            )
            == 0
        ).sum()
    ) if len(clms) else 0

    allow, cohort, class_df, _buckets = discover_safe_allowlist(
        clms,
        clmp,
        prelsa_path=DEFAULT_PRELSA,
        pactg_path=pactg,
        recon_path=DEFAULT_RECON if DEFAULT_RECON.is_file() else None,
    )
    # Snapshot MPAID for allowlisted policies before apply
    money_before = {}
    for pol in allow:
        hdr = clms[clms["MPOLICY"].astype(str).str.strip() == pol]
        if len(hdr):
            money_before[pol] = hdr.iloc[0][
                [c for c in ("MPAID", "MFACE", "NETDB", "MINTAMT", "PREMIUM", "CLAIMSTAT", "DTOFDEATH")
                 if c in hdr.columns]
            ].to_dict()

    clms_after, clmp_after, stats = apply_match_cso_zero_payee_backfill(
        clms,
        clmp,
        prelsa_path=DEFAULT_PRELSA,
        pactg_path=pactg,
        allowlist=allow,
    )
    stats["_cohort_df"] = cohort
    stats["_class_df"] = class_df
    stats["discovery"] = {
        "cohort_n": int(len(cohort)),
        "class_counts": {
            str(k): int(v)
            for k, v in class_df["class"].value_counts().to_dict().items()
        }
        if len(class_df)
        else {},
        "safe_n": int(len(allow)),
    }
    paths = write_zero_payee_backfill_audit(
        stats, EVIDENCE, cohort_df=cohort, class_df=class_df
    )

    # Prove quikclms money unchanged for touched policies
    money_ok = True
    money_bad = []
    for pol, before in money_before.items():
        hdr = clms_after[clms_after["MPOLICY"].astype(str).str.strip() == pol]
        if not len(hdr):
            money_ok = False
            money_bad.append(f"{pol}:missing")
            continue
        after = hdr.iloc[0]
        for k, v in before.items():
            if str(after.get(k, "")).strip() != str(v).strip():
                money_ok = False
                money_bad.append(f"{pol}:{k}")
                break

    golden_payees = int(
        (clmp_after["MPOLICY"].astype(str).str.strip() == GOLDEN).sum()
    )

    print("Issue #135 MATCH_CSO zero-payee cohort backfill")
    print(f"  dry_run={args.dry_run}")
    print(f"  cohort_n={len(cohort)} class_counts={stats['discovery']['class_counts']}")
    print(f"  safe_allowlist={len(allow)}")
    print(
        f"  clmp {before_clmp} -> {len(clmp_after)} "
        f"(+{int(stats.get('rows_added', 0) or 0)} rows; "
        f"policies={stats.get('policies_backfilled')})"
    )
    print(f"  skipped_n={len(stats.get('skipped') or [])}")
    print(f"  header_money_unchanged={money_ok} bad={money_bad[:5]}")
    print(f"  golden_{GOLDEN}_payees={golden_payees}")
    print(f"  artifacts={paths}")

    if not stats.get("applied") and len(allow) > 0:
        # Allow no-op only when every SAFE policy already has payees
        still_zero = [
            p
            for p in allow
            if int((clmp["MPOLICY"].astype(str).str.strip() == p).sum()) == 0
        ]
        if still_zero:
            print(f"FAIL: backfill not applied for {len(still_zero)} SAFE policies")
            return 1
    if not money_ok:
        print("FAIL: quikclms money fields changed")
        return 1
    if golden_payees != 4:
        print(f"FAIL: golden {GOLDEN} payee count {golden_payees}!=4")
        return 1

    if args.dry_run:
        print("DRY-RUN: Output not written")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    DEFAULT_ARCHIVE.mkdir(parents=True, exist_ok=True)
    arch = DEFAULT_ARCHIVE / f"quikclmp_pre_issue135_zero_payee_cohort_{ts}.csv"
    shutil.copy2(DEFAULT_CLMP, arch)
    evid_arch = EVIDENCE / f"quikclmp_pre_issue135_zero_payee_cohort_{ts}.csv"
    shutil.copy2(DEFAULT_CLMP, evid_arch)

    tmp = DEFAULT_CLMP.with_suffix(".csv.tmp")
    clmp_after.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(DEFAULT_CLMP)

    TV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEFAULT_CLMP, TV / "quikclmp.csv")

    meta = {
        "reason": "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE_COHORT",
        "before_clmp_rows": before_clmp,
        "after_clmp_rows": int(len(clmp_after)),
        "rows_added": int(stats.get("rows_added", 0) or 0),
        "policies_backfilled": int(stats.get("policies_backfilled", 0) or 0),
        "cohort_n": int(len(cohort)),
        "class_counts": stats["discovery"]["class_counts"],
        "safe_allowlist_n": int(len(allow)),
        "hold_n": int(
            class_df["class"].isin(["HOLD_INCOMPLETE", "HOLD_MISMATCH"]).sum()
        )
        if len(class_df)
        else 0,
        "pre_archive": str(arch),
        "evidence_archive": str(evid_arch),
        "pre_sha256": before_sha,
        "post_sha256": _file_sha(DEFAULT_CLMP),
        "test_validation": str(TV / "quikclmp.csv"),
        "quikclms_mutated": False,
        "header_money_unchanged": money_ok,
        "golden_9011156655C_payees": golden_payees,
        "approx_zero_payee_death_headers_before": before_zero,
    }
    (EVIDENCE / "issue135_match_cso_zero_payee_apply_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"  archived {arch}")
    print(f"  wrote {DEFAULT_CLMP}")
    print(f"  published {TV / 'quikclmp.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
