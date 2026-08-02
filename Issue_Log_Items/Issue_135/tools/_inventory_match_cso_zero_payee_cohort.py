#!/usr/bin/env python3
"""Issue #135 — inventory + classify MATCH_CSO existing-header zero-payee cohort."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_match_cso_zero_payee_backfill import (  # noqa: E402
    discover_safe_allowlist,
    write_zero_payee_backfill_audit,
)

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from issue135_cso_pactg_recon import resolve_pactg  # noqa: E402

CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
PRELSA = ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"
RECON = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence" / "issue135_cso_output_recon.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"


def main() -> int:
    clms = pd.read_csv(CLMS, dtype=str).fillna("")
    clmp = pd.read_csv(CLMP, dtype=str).fillna("")
    pactg = resolve_pactg(None)
    allow, cohort, class_df, _buckets = discover_safe_allowlist(
        clms,
        clmp,
        prelsa_path=PRELSA,
        pactg_path=pactg,
        recon_path=RECON if RECON.is_file() else None,
    )
    stats = {
        "applied": False,
        "policies_backfilled": 0,
        "rows_added": 0,
        "skipped": [],
        "audit_rows": [],
        "allowlist_policies": sorted(allow.keys()),
        "discovery": {
            "cohort_n": int(len(cohort)),
            "class_counts": {
                str(k): int(v)
                for k, v in class_df["class"].value_counts().to_dict().items()
            }
            if len(class_df)
            else {},
            "safe_n": int(len(allow)),
        },
        "_cohort_df": cohort,
        "_class_df": class_df,
    }
    paths = write_zero_payee_backfill_audit(stats, EVID, cohort_df=cohort, class_df=class_df)
    summary = {
        "cohort_n": int(len(cohort)),
        "class_counts": stats["discovery"]["class_counts"],
        "safe_allowlist_n": int(len(allow)),
        "hold_n": int(
            class_df["class"].isin(["HOLD_INCOMPLETE", "HOLD_MISMATCH"]).sum()
        )
        if len(class_df)
        else 0,
        "artifacts": paths,
    }
    out = EVID / "issue135_match_cso_zero_payee_inventory_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
