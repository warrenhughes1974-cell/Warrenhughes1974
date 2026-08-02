#!/usr/bin/env python3
"""Grok second-pass for Issue #135 deploy package (CSV + DBF) — Cursor Grok 4.5."""

from __future__ import annotations

import json
import re
from pathlib import Path

import dbf
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
STAGING = ROOT / "QLA_Migration" / "Staging" / "claims_uat_dbf"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
MARKER = "CSO_CONTROLLED_NO_PACTG_HISTORY"
HOLDS9 = {
    "9010395879C",
    "9010741943C",
    "9010771580C",
    "9010771662C",
    "9011153243C",
    "9011154868C",
    "9011158069C",
    "9011175485C",
    "9011193674C",
}
TOL = 0.01


def _ver(path: Path) -> str:
    m = re.search(
        r'APP_VERSION\s*=\s*"([^"]+)"',
        path.read_text(encoding="utf-8", errors="replace"),
    )
    return m.group(1) if m else ""


def main() -> int:
    fails: list[str] = []
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            fails.append(f"{name}: {detail}")

    v_root = _ver(ROOT / "app.py")
    v_mig = _ver(ROOT / "QLA_Migration" / "app.py")
    add("APP_VERSION_LOCK", v_root == "v58.60" and v_mig == "v58.60", f"root={v_root} mig={v_mig}")

    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str).fillna("")
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str).fillna("")
    tv_clms = pd.read_csv(OUT / "Test_Validation" / "quikclms.csv", dtype=str).fillna("")
    tv_clmp = pd.read_csv(OUT / "Test_Validation" / "quikclmp.csv", dtype=str).fillna("")

    add("CLMS_ROWS_6044", len(clms) == 6044, str(len(clms)))
    add("CLMP_ROWS_5495", len(clmp) == 5495, str(len(clmp)))
    add("TV_SYNC_CLMS", len(tv_clms) == len(clms), f"tv={len(tv_clms)} out={len(clms)}")
    add("TV_SYNC_CLMP", len(tv_clmp) == len(clmp), f"tv={len(tv_clmp)} out={len(clmp)}")

    mint_nz = int((pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0).abs() > TOL).sum())
    add("MINTAMT_ALL_ZERO", mint_nz == 0, f"nonzero={mint_nz}")

    marker_n = int(clms["MEMOTEXT"].astype(str).str.contains(MARKER, regex=False).sum())
    add("MARKER_308", marker_n == 308, str(marker_n))
    clmp_pols = set(clmp["MPOLICY"].astype(str).str.strip())
    marker_payee = int(
        clms[clms["MEMOTEXT"].astype(str).str.contains(MARKER, regex=False)]["MPOLICY"]
        .astype(str)
        .str.strip()
        .isin(clmp_pols)
        .sum()
    )
    add("MARKER_NO_PAYEES", marker_payee == 0, f"with_payees={marker_payee}")

    holds_present = sorted(HOLDS9 & set(clms["MPOLICY"].astype(str).str.strip()))
    add("HOLD9_ABSENT", len(holds_present) == 0, str(holds_present))

    g = clmp[clmp["MPOLICY"].astype(str).str.strip().str.upper().str.startswith("9011156655")]
    add("GOLDEN_4_PAYEES", len(g) == 4, str(len(g)))
    psum = round(float(pd.to_numeric(g["MAMOUNT"], errors="coerce").fillna(0).sum()), 2)
    add("GOLDEN_PAYEE_SUM", abs(psum - 5145.67) <= TOL, str(psum))

    # DBF inspection
    clms_dbf = STAGING / "QUIKCLMS.DBF"
    clmp_dbf = STAGING / "QUIKCLMP.DBF"
    add("SHORT_CLMS_EXISTS", clms_dbf.is_file() and (STAGING / "QUIKCLMS.DBT").is_file(), "")
    add("SHORT_CLMP_EXISTS", clmp_dbf.is_file(), "")
    add("NO_CLMP_DBT", not (STAGING / "QUIKCLMP.DBT").exists(), "")

    POL = "9011156655C"
    t = dbf.Table(str(clms_dbf))
    t.open()
    try:
        clms_n = len(t)
        clms_spec = t.structure()
        clms_mpol = [
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
    add("DBF_CLMS_ROWS", clms_n == 6044, str(clms_n))
    add(
        "DBF_MPOLICY_C11",
        any("C(11)" in s.upper().replace(" ", "") for s in clms_mpol),
        str(clms_mpol),
    )
    add("DBF_HEADER_EXISTS", hdr is not None, str(hdr))
    if hdr:
        add("DBF_MPOLICY_KEY", hdr["MPOLICY"] == POL, hdr["MPOLICY"])
        add("DBF_MPAID", abs(hdr["MPAID"] - 5145.67) <= TOL, str(hdr["MPAID"]))
        add("DBF_MFACE", abs(hdr["MFACE"] - 5000) <= TOL, str(hdr["MFACE"]))
        add("DBF_NETDB", abs(hdr["NETDB"] - 5000) <= TOL, str(hdr["NETDB"]))
        add("DBF_MINTAMT", abs(hdr["MINTAMT"]) <= TOL, str(hdr["MINTAMT"]))

    t = dbf.Table(str(clmp_dbf))
    t.open()
    try:
        clmp_n = len(t)
        clmp_spec = t.structure()
        clmp_mpol = [
            p.strip()
            for p in (clmp_spec if isinstance(clmp_spec, list) else str(clmp_spec).split(";"))
            if "MPOLICY" in str(p).upper()
        ]
        pay = []
        for rec in t:
            if str(rec.mpolicy).strip() == POL:
                pay.append((int(rec.mseq or 0), str(rec.mpayname).strip(), float(rec.mamount or 0)))
    finally:
        t.close()
    pay = sorted(pay)
    add("DBF_CLMP_ROWS", clmp_n == 5495, str(clmp_n))
    add(
        "DBF_CLMP_MPOLICY_C11",
        any("C(11)" in s.upper().replace(" ", "") for s in clmp_mpol),
        str(clmp_mpol),
    )
    add("DBF_GOLDEN_4", len(pay) == 4, str(len(pay)))
    dsum = round(sum(a for _, _, a in pay), 2)
    add("DBF_GOLDEN_SUM", abs(dsum - 5145.67) <= TOL, str(dsum))

    result = {
        "validator": "grok_second_pass_issue135_deploy_package",
        "model": "Cursor Grok 4.5",
        "pass": len(fails) == 0,
        "fail_count": len(fails),
        "fails": fails,
        "checks": checks,
        "clms_rows": int(len(clms)),
        "clmp_rows": int(len(clmp)),
        "dbf_clms_rows": clms_n,
        "dbf_clmp_rows": clmp_n,
        "golden_payees": [
            {"MSEQ": s, "MPAYNAME": n, "MAMOUNT": a} for s, n, a in pay
        ],
        "remaining_holds_documented": {
            "hold_incomplete_source_9": sorted(HOLDS9),
            "zero_payee_hold_incomplete_3": [
                "9010792038C",
                "9011062307C",
                "9015000341C",
            ],
            "issue_closed": False,
        },
        "generated_at": pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%SZ"),
    }
    out = EVID / "issue135_deploy_grok_second_pass.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("PASS" if result["pass"] else "FAIL", "fail_count=", len(fails))
    for f in fails:
        print("FAIL", f)
    print("wrote", out)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
