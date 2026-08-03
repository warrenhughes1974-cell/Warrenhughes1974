#!/usr/bin/env python3
"""Issue #135 — copy verified short-name claims DBFs to Q:\\CSO\\CSO_Test_6_30_2026."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import dbf

from qla_core.claims_payee_mseq_align import GOLDEN_POLICY
from qla_core.dbf_append_tool_package import validate_claims_dbf_join

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "QLA_Migration" / "Staging" / "claims_uat_dbf"
QDEST = Path(r"Q:\CSO\CSO_Test_6_30_2026")
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
FILES = ("QUIKCLMS.DBF", "QUIKCLMS.DBT", "QUIKCLMP.DBF")
TOL = 0.01


def count_dbf(path: Path) -> int:
    table = dbf.Table(str(path))
    table.open()
    try:
        return len(table)
    finally:
        table.close()


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not QDEST.is_dir():
        print("FAIL: Q destination missing", QDEST)
        return 2

    for name in FILES:
        src = STAGING / name
        if not src.is_file():
            print("FAIL: missing staging", src)
            return 3

    staging_gate = validate_claims_dbf_join(STAGING)
    if not staging_gate.get("ok"):
        print("FAIL: staging join gate", staging_gate.get("fails"))
        return 4

    clms_n = int(staging_gate["clms_rows"])
    clmp_n = int(staging_gate["clmp_rows"])

    copied = []
    for name in FILES:
        src = STAGING / name
        dst = QDEST / name
        shutil.copy2(src, dst)
        copied.append(
            {
                "name": name,
                "src": str(src),
                "dst": str(dst),
                "size": dst.stat().st_size,
            }
        )
        print("copied", name, "bytes", dst.stat().st_size)

    for junk in ("QUIKCLMP.DBT", "quikclmp.dbt"):
        p = QDEST / junk
        if p.is_file():
            p.unlink()

    q_gate = validate_claims_dbf_join(
        QDEST, expect_clms_rows=clms_n, expect_clmp_rows=clmp_n
    )

    # Golden money spot-check when present
    POL = GOLDEN_POLICY
    t = dbf.Table(str(QDEST / "QUIKCLMS.DBF"))
    t.open()
    try:
        hdr = None
        for rec in t:
            if str(rec.mpolicy).strip() == POL:
                hdr = {
                    "MPOLICY": str(rec.mpolicy).strip(),
                    "MPAID": float(rec.mpaid or 0),
                    "MFACE": float(rec.mface or 0),
                    "NETDB": float(rec.netdb or 0),
                    "MINTAMT": float(rec.mintamt or 0),
                    "MSEQ": int(rec.mseq or 0),
                }
                break
    finally:
        t.close()

    t = dbf.Table(str(QDEST / "QUIKCLMP.DBF"))
    t.open()
    try:
        pay = []
        for rec in t:
            if str(rec.mpolicy).strip() == POL:
                pay.append(
                    {
                        "MPOLICY": str(rec.mpolicy).strip(),
                        "MSEQ": int(rec.mseq or 0),
                        "MPAYNAME": str(rec.mpayname).strip(),
                        "MAMOUNT": float(rec.mamount or 0),
                    }
                )
    finally:
        t.close()

    pay = sorted(pay, key=lambda r: (r["MSEQ"], r["MPAYNAME"]))
    psum = round(sum(r["MAMOUNT"] for r in pay), 2)
    golden_ok = True
    if hdr is not None:
        golden_ok = (
            hdr.get("MPOLICY") == POL
            and abs(hdr["MPAID"] - 5145.67) <= TOL
            and abs(hdr["MFACE"] - 5000) <= TOL
            and abs(hdr["NETDB"] - 5000) <= TOL
            and abs(hdr["MINTAMT"]) <= TOL
            and hdr["MSEQ"] == 0
            and len(pay) == 4
            and abs(psum - 5145.67) <= TOL
            and sorted({r["MSEQ"] for r in pay}) == [0]
        )

    ok = bool(q_gate.get("ok")) and golden_ok and not (QDEST / "QUIKCLMP.DBT").exists()

    summary = {
        "generated_at": ts,
        "destination": str(QDEST),
        "copied": copied,
        "staging_gate": staging_gate,
        "destination_gate": q_gate,
        "destination_clms_rows": count_dbf(QDEST / "QUIKCLMS.DBF"),
        "destination_clmp_rows": count_dbf(QDEST / "QUIKCLMP.DBF"),
        "header_9011156655C": hdr,
        "payees_9011156655C": pay,
        "payee_sum": psum,
        "no_quikclmp_dbt": not (QDEST / "QUIKCLMP.DBT").exists(),
        "pass": ok,
    }
    out = EVID / "issue135_q_destination_copy_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Q_COPY", "PASS" if ok else "FAIL")
    print("rows", clms_n, clmp_n, "payees", len(pay), "sum", psum, "mseqs", sorted({r['MSEQ'] for r in pay}))
    print("wrote", out)
    return 0 if ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
