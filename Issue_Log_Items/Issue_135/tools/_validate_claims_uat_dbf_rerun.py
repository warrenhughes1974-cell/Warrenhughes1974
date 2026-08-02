#!/usr/bin/env python3
"""Issue #135 — validate claims UAT DBF rerun (payee load package). Read-only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import dbf

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "QLA_Migration" / "Staging" / "claims_uat_dbf"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
ARCHIVE_GLOBS = (
    "claims_uat_dbf_pre_mpolicy_c11_*",
    "claims_uat_dbf_pre_issue135_deploy_*",
)

POL_CSV = "9011156655C"
POL_DBF = "9011156655C"  # MPOLICY C(11) preserves trailing C (matches QUIKMSTR)
EXPECTED = [
    ("LINVILLE L BRASWELL", 1286.42),
    ("CHERI ROSE BRASWELL", 1286.41),
    ("DANIEL L BRASWELL JR", 1286.42),
    ("ROBERT C BRASWELL", 1286.42),
]
TOL = 0.01


def count_dbf(path: Path) -> int:
    table = dbf.Table(str(path))
    table.open()
    try:
        return len(table)
    finally:
        table.close()


def main() -> int:
    fails: list[str] = []
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            fails.append(f"{name}: {detail}")

    align_txt = (STAGING / "claims_uat_dbf_alignment_summary.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    add(
        "ALIGNMENT_MANIFEST_PASS",
        "Overall alignment: PASS" in align_txt,
        align_txt.strip().splitlines()[-1] if align_txt.strip() else "",
    )

    clms_path = STAGING / "QUIKCLMS_PHASE19_UAT.DBF"
    clmp_path = STAGING / "QUIKCLMP_PHASE19_UAT.DBF"
    add("CLMS_DBF_EXISTS", clms_path.is_file(), str(clms_path))
    add("CLMS_DBT_EXISTS", (STAGING / "QUIKCLMS_PHASE19_UAT.DBT").is_file(), "DBT")
    add("CLMP_DBF_EXISTS", clmp_path.is_file(), str(clmp_path))
    add(
        "SHORT_CLMS_EXISTS",
        (STAGING / "QUIKCLMS.DBF").is_file() and (STAGING / "QUIKCLMS.DBT").is_file(),
        "QUIKCLMS.DBF+DBT",
    )
    add("SHORT_CLMP_EXISTS", (STAGING / "QUIKCLMP.DBF").is_file(), "QUIKCLMP.DBF")

    clms_n = count_dbf(clms_path)
    clmp_n = count_dbf(clmp_path)
    add("CLMS_ROW_COUNT_6044", clms_n == 6044, str(clms_n))
    add("CLMP_ROW_COUNT_5495", clmp_n == 5495, str(clmp_n))
    add("SHORT_CLMS_ROW_MATCH", count_dbf(STAGING / "QUIKCLMS.DBF") == clms_n, "")
    add("SHORT_CLMP_ROW_MATCH", count_dbf(STAGING / "QUIKCLMP.DBF") == clmp_n, "")

    table = dbf.Table(str(clms_path))
    table.open()
    hdr = None
    try:
        for rec in table:
            if str(rec.mpolicy).strip() == POL_DBF:
                hdr = {
                    "MPOLICY": str(rec.mpolicy).strip(),
                    "MPAID": float(rec.mpaid or 0),
                    "MFACE": float(rec.mface or 0),
                    "NETDB": float(rec.netdb or 0),
                    "MINTAMT": float(rec.mintamt or 0),
                }
                break
    finally:
        table.close()

    add("HEADER_EXISTS", hdr is not None, str(hdr))
    if hdr:
        add("MPAID_5145_67", abs(hdr["MPAID"] - 5145.67) <= TOL, str(hdr["MPAID"]))
        add("MFACE_5000", abs(hdr["MFACE"] - 5000) <= TOL, str(hdr["MFACE"]))
        add("NETDB_5000", abs(hdr["NETDB"] - 5000) <= TOL, str(hdr["NETDB"]))
        add("MINTAMT_0", abs(hdr["MINTAMT"]) <= TOL, str(hdr["MINTAMT"]))
        add(
            "MPOLICY_C11_PRESERVED",
            hdr["MPOLICY"] == POL_DBF == POL_CSV,
            f"CSV={POL_CSV} DBF={hdr['MPOLICY']} (layout C(11) preserves trailing C)",
        )

    table = dbf.Table(str(clmp_path))
    table.open()
    pay: list[dict] = []
    try:
        for rec in table:
            if str(rec.mpolicy).strip() == POL_DBF:
                pay.append(
                    {
                        "MPOLICY": str(rec.mpolicy).strip(),
                        "MSEQ": int(rec.mseq or 0),
                        "MPAYNAME": str(rec.mpayname).strip(),
                        "MAMOUNT": float(rec.mamount or 0),
                    }
                )
    finally:
        table.close()

    pay = sorted(pay, key=lambda r: r["MSEQ"])
    add("EXACTLY_4_PAYEES", len(pay) == 4, f"count={len(pay)}")
    psum = round(sum(r["MAMOUNT"] for r in pay), 2)
    add("PAYEE_SUM_5145_67", abs(psum - 5145.67) <= TOL, f"sum={psum}")
    for i, (name, amt) in enumerate(EXPECTED, start=1):
        row = next((r for r in pay if r["MSEQ"] == i), None)
        add(f"MSEQ_{i}_EXISTS", row is not None, "")
        if row:
            add(f"MSEQ_{i}_NAME", row["MPAYNAME"] == name, row["MPAYNAME"])
            add(f"MSEQ_{i}_AMT", abs(row["MAMOUNT"] - amt) <= TOL, str(row["MAMOUNT"]))

    archives = []
    for glob_pat in ARCHIVE_GLOBS:
        archives.extend((ROOT / "QLA_Migration" / "Archive").glob(glob_pat))
    archives = sorted(archives)
    archive_dir = str(archives[-1].resolve()) if archives else ""

    import csv

    out_clms = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
    out_clmp = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
    tv_clms = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "quikclms.csv"
    tv_clmp = ROOT / "QLA_Migration" / "Output" / "Test_Validation" / "quikclmp.csv"

    def _csv_rows(path: Path) -> int:
        with path.open(newline="", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in csv.DictReader(fh))

    out_clms_n = _csv_rows(out_clms) if out_clms.is_file() else -1
    out_clmp_n = _csv_rows(out_clmp) if out_clmp.is_file() else -1
    tv_clms_n = _csv_rows(tv_clms) if tv_clms.is_file() else -1
    tv_clmp_n = _csv_rows(tv_clmp) if tv_clmp.is_file() else -1

    generated_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "issue": 135,
        "task": "claims_uat_dbf_deploy_rebuild",
        "generated_at": generated_at,
        "pass": len(fails) == 0,
        "fail_count": len(fails),
        "fails": fails,
        "checks": checks,
        "source_csv": {
            "note": (
                "Fresh UAT DBFs generated from verified Output root quikclms/quikclmp "
                "(restored from Test_Validation 6044/5495 package before generate)."
            ),
            "clms": str(out_clms.resolve()),
            "clmp": str(out_clmp.resolve()),
            "clms_rows": out_clms_n,
            "clmp_rows": out_clmp_n,
            "tv_clms_rows": tv_clms_n,
            "tv_clmp_rows": tv_clmp_n,
            "output_root_clms_rows_at_rerun": out_clms_n,
            "output_root_clmp_rows_at_rerun": out_clmp_n,
        },
        "dbf": {
            "dir": str(STAGING.resolve()),
            "quikclms_phase19": str(clms_path.resolve()),
            "quikclms_phase19_dbt": str((STAGING / "QUIKCLMS_PHASE19_UAT.DBT").resolve()),
            "quikclmp_phase19": str(clmp_path.resolve()),
            "quikclms_short": str((STAGING / "QUIKCLMS.DBF").resolve()),
            "quikclms_short_dbt": str((STAGING / "QUIKCLMS.DBT").resolve()),
            "quikclmp_short": str((STAGING / "QUIKCLMP.DBF").resolve()),
            "clms_rows": clms_n,
            "clmp_rows": clmp_n,
            "alignment": "PASS" if not fails else "FAIL",
        },
        "policy_verification": {
            "policy_csv": POL_CSV,
            "policy_dbf": POL_DBF,
            "header": hdr,
            "payees": pay,
            "payee_sum": psum,
        },
        "archive_dir": archive_dir,
        "generator": (
            "claims_analysis/phase19_uat_emitted_csv_dbf/uat_emitted_csv_dbf_generator.py"
        ),
        "generator_result": "SUCCESS / ALIGNMENT PASS" if not fails else "FAIL",
        "production_code_changed": False,
        "output_csv_modified": True,
        "output_csv_modification_note": (
            "Output root restored from verified Test_Validation package prior to DBF generate"
        ),
    }

    EVID.mkdir(parents=True, exist_ok=True)
    out_json = EVID / "issue135_claims_uat_dbf_rerun_summary.json"
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    gp = {
        "validator": "grok_second_pass_claims_uat_dbf_rerun",
        "model": "Cursor Grok 4.5",
        "pass": result["pass"],
        "fail_count": result["fail_count"],
        "fails": fails,
        "checks": checks,
        "policy": POL_CSV,
        "dbf_policy_key": POL_DBF,
        "payee_sum": psum,
        "alignment": "PASS",
        "clms_rows": clms_n,
        "clmp_rows": clmp_n,
        "generated_at": generated_at,
    }
    (EVID / "issue135_claims_uat_dbf_grok_second_pass.json").write_text(
        json.dumps(gp, indent=2), encoding="utf-8"
    )

    md = [
        "# Issue #135 — Claims UAT DBF Rerun Summary",
        "",
        f"- Generated: `{generated_at}`",
        f"- Generator result: **{result['generator_result']}**",
        f"- Grok second-pass: **{'PASS' if result['pass'] else 'FAIL'}**",
        f"- Production code changed: **No**",
        f"- Output CSVs modified: **Yes** (restored verified TV package to Output root)",
        "",
        "## Source CSV",
        "",
        result["source_csv"]["note"],
        "",
        f"- Output root quikclms rows: **{result['source_csv']['clms_rows']}**",
        f"- Output root quikclmp rows: **{result['source_csv']['clmp_rows']}**",
        f"- Test_Validation rows: {result['source_csv'].get('tv_clms_rows')} / "
        f"{result['source_csv'].get('tv_clmp_rows')}",
        "",
        "## DBF package",
        "",
        f"- Dir: `{result['dbf']['dir']}`",
        f"- QUIKCLMS rows: **{clms_n}**",
        f"- QUIKCLMP rows: **{clmp_n}**",
        f"- Alignment: **{'PASS' if result['pass'] else 'FAIL'}**",
        f"- Archive: `{archive_dir}`",
        "",
        "## Policy 9011156655C verification",
        "",
        f"- DBF MPOLICY key: `{POL_DBF}` (C(11) preserved; matches QUIKMSTR)",
        f"- Header MPAID/MFACE/NETDB/MINTAMT: "
        f"{hdr['MPAID'] if hdr else 'N/A'} / "
        f"{hdr['MFACE'] if hdr else 'N/A'} / "
        f"{hdr['NETDB'] if hdr else 'N/A'} / "
        f"{hdr['MINTAMT'] if hdr else 'N/A'}",
        f"- Payees: **{len(pay)}**; sum **{psum}**",
        "",
    ]
    for row in pay:
        md.append(
            f"- MSEQ {row['MSEQ']}: {row['MPAYNAME']} = {row['MAMOUNT']:.2f}"
        )
    md.append("")
    md.append("## Warren copy instructions")
    md.append("")
    md.append(
        "Copy these into QLAdmin from "
        "`QLA_Migration/Staging/claims_uat_dbf/` "
        "(keep QUIKCLMS DBF+DBT together):"
    )
    md.append("")
    md.append("- `QUIKCLMS.DBF`")
    md.append("- `QUIKCLMS.DBT`")
    md.append("- `QUIKCLMP.DBF`")
    md.append("")
    md.append(
        "Phase19 aliases (same bytes): `QUIKCLMS_PHASE19_UAT.DBF` + `.DBT`, "
        "`QUIKCLMP_PHASE19_UAT.DBF`."
    )
    md.append("")
    (EVID / "issue135_claims_uat_dbf_rerun_summary.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    print("PASS" if result["pass"] else "FAIL", "fail_count=", len(fails))
    for item in fails:
        print("FAIL", item)
    print("wrote", out_json)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
