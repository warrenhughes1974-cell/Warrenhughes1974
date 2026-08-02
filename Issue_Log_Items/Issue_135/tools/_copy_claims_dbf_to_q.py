#!/usr/bin/env python3
"""Issue #135 — copy verified short-name claims DBFs to Q:\\CSO\\CSO_Test_6_30_2026."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import dbf

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

    # Preflight staging verification
    clms_n = count_dbf(STAGING / "QUIKCLMS.DBF")
    clmp_n = count_dbf(STAGING / "QUIKCLMP.DBF")
    if clms_n != 6044 or clmp_n != 5495:
        print(f"FAIL: staging counts clms={clms_n} clmp={clmp_n}")
        return 4

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

    # Confirm destination (MPOLICY C(11) must preserve trailing C)
    POL = "9011156655C"
    q_clms_n = count_dbf(QDEST / "QUIKCLMS.DBF")
    q_clmp_n = count_dbf(QDEST / "QUIKCLMP.DBF")
    t = dbf.Table(str(QDEST / "QUIKCLMS.DBF"))
    t.open()
    try:
        clms_spec = t.structure()
        mpolicy_spec = [
            p.strip()
            for p in (clms_spec if isinstance(clms_spec, list) else str(clms_spec).split(";"))
            if "MPOLICY" in str(p).upper()
        ]
        hdr = None
        for rec in t:
            if str(rec.mpolicy).strip() == POL:
                hdr = {
                    "MPOLICY": str(rec.mpolicy).strip(),
                    "MPAID": float(rec.mpaid or 0),
                    "MFACE": float(rec.mface or 0),
                    "NETDB": float(rec.netdb or 0),
                    "MINTAMT": float(rec.mintamt or 0),
                }
                break
    finally:
        t.close()

    t = dbf.Table(str(QDEST / "QUIKCLMP.DBF"))
    t.open()
    try:
        clmp_spec = t.structure()
        clmp_mpolicy_spec = [
            p.strip()
            for p in (clmp_spec if isinstance(clmp_spec, list) else str(clmp_spec).split(";"))
            if "MPOLICY" in str(p).upper()
        ]
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
    pay = sorted(pay, key=lambda r: r["MSEQ"])
    psum = round(sum(r["MAMOUNT"] for r in pay), 2)
    mpolicy_c11 = (
        any("C(11)" in s.upper().replace(" ", "") for s in mpolicy_spec)
        and any("C(11)" in s.upper().replace(" ", "") for s in clmp_mpolicy_spec)
    )

    ok = (
        q_clms_n == 6044
        and q_clmp_n == 5495
        and hdr is not None
        and hdr.get("MPOLICY") == POL
        and mpolicy_c11
        and abs(hdr["MPAID"] - 5145.67) <= TOL
        and abs(hdr["MFACE"] - 5000) <= TOL
        and abs(hdr["NETDB"] - 5000) <= TOL
        and abs(hdr["MINTAMT"]) <= TOL
        and len(pay) == 4
        and abs(psum - 5145.67) <= TOL
        and not (QDEST / "QUIKCLMP.DBT").exists()
    )

    summary = {
        "generated_at": ts,
        "destination": str(QDEST),
        "copied": copied,
        "destination_clms_rows": q_clms_n,
        "destination_clmp_rows": q_clmp_n,
        "mpolicy_spec_clms": mpolicy_spec,
        "mpolicy_spec_clmp": clmp_mpolicy_spec,
        "mpolicy_c11": mpolicy_c11,
        "header_9011156655C": hdr,
        "payees_9011156655C": pay,
        "payee_sum": psum,
        "no_quikclmp_dbt": not (QDEST / "QUIKCLMP.DBT").exists(),
        "pass": ok,
    }
    out = EVID / "issue135_q_destination_copy_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Q_COPY", "PASS" if ok else "FAIL")
    print("rows", q_clms_n, q_clmp_n, "payees", len(pay), "sum", psum)
    print("wrote", out)
    return 0 if ok else 5


if __name__ == "__main__":
    raise SystemExit(main())
