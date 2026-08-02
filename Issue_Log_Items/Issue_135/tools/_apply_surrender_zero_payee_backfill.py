"""Apply Issue #135 surrender zero-payee backfill to Output (+ Test_Validation)."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from qla_core.issue135_surrender_zero_payee_backfill import (  # noqa: E402
    apply_surrender_zero_payee_backfill,
    write_surrender_zero_payee_audit,
)

OUT = REPO / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
EVID = REPO / "Issue_Log_Items" / "Issue_135" / "evidence"
ARCH = REPO / "QLA_Migration" / "Archive"
PACTG = REPO / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260630.csv"
PRELSA = REPO / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv"
GOLDEN = "9011158068C"


def main() -> int:
    clms_path = OUT / "quikclms.csv"
    clmp_path = OUT / "quikclmp.csv"
    if not clms_path.is_file() or not clmp_path.is_file():
        print("FAIL: missing Output quikclms/quikclmp")
        return 2

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ARCH.mkdir(parents=True, exist_ok=True)
    arch = ARCH / f"quikclmp_pre_surrender_zero_payee_{ts}.csv"
    shutil.copy2(clmp_path, arch)
    print("archive", arch)

    clms = pd.read_csv(clms_path, dtype=str).fillna("")
    clmp = pd.read_csv(clmp_path, dtype=str).fillna("")
    before = len(clmp)

    clms2, clmp2, stats = apply_surrender_zero_payee_backfill(
        clms,
        clmp,
        pactg_path=PACTG,
        prelsa_path=PRELSA,
        clid_path=OUT / "quikclid.csv",
        clnt_path=OUT / "quikclnt.csv",
    )
    paths = write_surrender_zero_payee_audit(stats, EVID)
    clmp2.to_csv(clmp_path, index=False, encoding="utf-8")
    TV.mkdir(parents=True, exist_ok=True)
    clmp2.to_csv(TV / "quikclmp.csv", index=False, encoding="utf-8")
    # keep clms unchanged but refresh TV copy for package consistency
    shutil.copy2(clms_path, TV / "quikclms.csv")

    g = clmp2[clmp2["MPOLICY"].astype(str).str.strip() == GOLDEN]
    print("stats", {k: stats[k] for k in stats if k not in {"audit_rows", "holds"}})
    print("clmp rows", before, "->", len(clmp2))
    print("golden payees", len(g))
    if len(g):
        print(g[["MPOLICY", "MSEQ", "MAMOUNT", "MPAYNAME", "MHDPMT"]].to_string(index=False))
        pay_sum = round(pd.to_numeric(g["MAMOUNT"], errors="coerce").fillna(0).sum(), 2)
        print("golden pay_sum", pay_sum)
    print("evidence", paths)
    if not stats.get("applied"):
        print("WARN: nothing applied")
        return 1
    if len(g) < 1:
        print("FAIL: golden still has no payees")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
