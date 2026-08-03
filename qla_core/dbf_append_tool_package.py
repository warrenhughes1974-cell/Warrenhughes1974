"""Finalize Desktop DBF Append Tool package after each conversion build.

Generic Append Tool binary injection blanks MEMO (M) fields, so quikmemo and
claims tables with MEMOTEXT must be placed via dedicated generators / staging
copies — never rebuilt by Append Tool EXECUTE on those CSVs.

Claims payee MSEQ must match claim-header MSEQ (usually 0) or QLAdmin shows
blank payees. Packaging always re-aligns Output CSVs, regenerates claims UAT
DBFs, validates the join, then places DBFs into Append Tool output.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import dbf
import pandas as pd

from qla_core.claims_payee_mseq_align import (
    GOLDEN_POLICY,
    ClaimsPayeeMseqAlignError,
    align_claims_csv_dir,
    validate_payee_mseq_join,
)
from qla_core.quikmemo_dbf_generator import write_quikmemo_dbf

DEFAULT_APPEND_INPUT = r"C:\Users\warren\Desktop\DBF_Append_Tool\input"
DEFAULT_APPEND_OUTPUT = r"C:\Users\warren\Desktop\DBF_Append_Tool\output"

# CSVs that must not be fed to Append Tool EXECUTE (memo packing / claims UAT DBF).
APPEND_INPUT_SKIP_CSVS = frozenset({
    "quikmemo.csv",
    "quikclms.csv",
    "quikclmp.csv",
})


class DbfAppendPackageError(RuntimeError):
    """Hard-fail Append Tool packaging (do not treat as warning-only)."""


def _norm(p: str | Path) -> str:
    return os.path.normpath(str(p))


def publish_append_input_csvs(
    output_dir: str | Path,
    append_input: str | Path = DEFAULT_APPEND_INPUT,
) -> dict[str, Any]:
    """Copy quik*.csv (+ rates) to Append Tool input, excluding memo/claims CSVs."""
    src_dir = Path(output_dir)
    dest = Path(append_input)
    dest.mkdir(parents=True, exist_ok=True)

    skip_extra = {
        "rate_csv_manifest.csv",
        "claims_review_hold_manifest.csv",
        "claims_cross_table_validation_report.csv",
        "claims_emit_enhancement_validation.csv",
        "cso_mortality_crosswalk_qa.csv",
        "variation_code_audit.csv",
    }
    copied: list[str] = []
    skipped: list[str] = []

    for src in sorted(src_dir.glob("*.csv")):
        name = src.name
        low = name.lower()
        if not low.startswith("quik"):
            continue
        if low in APPEND_INPUT_SKIP_CSVS or low in skip_extra:
            skipped.append(name)
            stale = dest / name
            if stale.is_file():
                stale.unlink()
            continue
        shutil.copy2(src, dest / name)
        copied.append(name)

    rates = src_dir / "rates"
    if rates.is_dir():
        for src in sorted(rates.glob("*.csv")):
            low = src.name.lower()
            if low in skip_extra:
                continue
            shutil.copy2(src, dest / src.name)
            copied.append(f"rates/{src.name}")

    return {
        "copied": len(copied),
        "skipped": skipped,
        "dest": _norm(dest),
        "files": copied,
    }


def place_quikmemo_dbf(
    output_dir: str | Path,
    append_output: str | Path = DEFAULT_APPEND_OUTPUT,
) -> dict[str, Any]:
    """Write quikmemo.dbf + memo sidecar into Append Tool output via Issue 21M generator."""
    csv_path = Path(output_dir) / "quikmemo.csv"
    if not csv_path.is_file():
        return {"ok": False, "error": f"missing {csv_path}"}
    dbf_dir = Path(append_output)
    dbf_dir.mkdir(parents=True, exist_ok=True)
    dbf_path = dbf_dir / "quikmemo.dbf"
    info = write_quikmemo_dbf(str(csv_path), str(dbf_path))
    info["ok"] = bool(info.get("fpt_exists")) and int(info.get("dbf_rows") or 0) > 0
    if not info.get("fpt_exists"):
        info["error"] = "memo sidecar (.dbt/.fpt) missing after write_quikmemo_dbf"
        info["ok"] = False
    return info


def _mpolicy_is_c11(structure) -> bool:
    specs = structure if isinstance(structure, list) else str(structure).split(";")
    for s in specs:
        su = str(s).upper().replace(" ", "")
        if "MPOLICY" in su and "C(11)" in su:
            return True
    return False


def validate_claims_dbf_join(
    staging: str | Path,
    *,
    expect_clms_rows: int | None = None,
    expect_clmp_rows: int | None = None,
) -> dict[str, Any]:
    """Destination-side checks on regenerated claims DBFs."""
    staging_p = Path(staging)
    clms_p = staging_p / "QUIKCLMS.DBF"
    if not clms_p.is_file():
        clms_p = staging_p / "quikclms.dbf"
    clmp_p = staging_p / "QUIKCLMP.DBF"
    if not clmp_p.is_file():
        clmp_p = staging_p / "quikclmp.dbf"
    fails: list[str] = []
    if not clms_p.is_file() or not clmp_p.is_file():
        return {"ok": False, "fails": ["missing_short_name_claims_dbf"]}
    if (staging_p / "QUIKCLMP.DBT").exists() or (staging_p / "quikclmp.dbt").exists():
        fails.append("unexpected_quikclmp_dbt")

    header_triples: set[tuple[str, str, int]] = set()
    t = dbf.Table(str(clms_p))
    t.open()
    try:
        clms_n = len(t)
        clms_c11 = _mpolicy_is_c11(t.structure())
        hdr_mseq = None
        for rec in t:
            pol = str(rec.mpolicy).strip()
            phase = str(rec.mphase).strip() or "1"
            mseq = int(rec.mseq or 0)
            header_triples.add((pol, phase, mseq))
            if pol == GOLDEN_POLICY and hdr_mseq is None:
                hdr_mseq = mseq
    finally:
        t.close()

    t = dbf.Table(str(clmp_p))
    t.open()
    try:
        clmp_n = len(t)
        clmp_c11 = _mpolicy_is_c11(t.structure())
        pay = []
        mismatch = 0
        for rec in t:
            pol = str(rec.mpolicy).strip()
            phase = str(rec.mphase).strip() or "1"
            mseq = int(rec.mseq or 0)
            if (pol, phase, mseq) not in header_triples:
                mismatch += 1
            if pol == GOLDEN_POLICY:
                pay.append(mseq)
    finally:
        t.close()

    if not clms_c11 or not clmp_c11:
        fails.append("mpolicy_not_c11")
    if expect_clms_rows is not None and clms_n != expect_clms_rows:
        fails.append(f"clms_rows={clms_n} expected={expect_clms_rows}")
    if expect_clmp_rows is not None and clmp_n != expect_clmp_rows:
        fails.append(f"clmp_rows={clmp_n} expected={expect_clmp_rows}")
    if mismatch:
        fails.append(f"dbf_payee_header_join_mismatch={mismatch}")
    if hdr_mseq is not None:
        if len(pay) != 4:
            fails.append(f"golden_dbf_payees={len(pay)}")
        if pay and sorted(set(pay)) != [hdr_mseq]:
            fails.append(f"golden_dbf_mseqs={sorted(set(pay))} header={hdr_mseq}")

    return {
        "ok": len(fails) == 0,
        "fails": fails,
        "clms_rows": clms_n,
        "clmp_rows": clmp_n,
        "mpolicy_c11": bool(clms_c11 and clmp_c11),
        "join_mismatch_n": mismatch,
        "golden_payee_mseqs": sorted(set(pay)) if pay else [],
    }


def regenerate_claims_uat_dbfs(
    output_dir: str | Path,
    staging_dir: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Regenerate claims UAT DBFs from Output CSVs into staging (temp then replace)."""
    out = Path(output_dir)
    staging = Path(staging_dir)
    root = Path(repo_root)
    gen = root / "claims_analysis" / "phase19_uat_emitted_csv_dbf" / "uat_emitted_csv_dbf_generator.py"
    clms_csv = out / "quikclms.csv"
    clmp_csv = out / "quikclmp.csv"
    if not gen.is_file():
        raise DbfAppendPackageError(f"missing generator {gen}")
    if not clms_csv.is_file() or not clmp_csv.is_file():
        raise DbfAppendPackageError("missing Output quikclms/quikclmp for DBF regenerate")

    staging.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="claims_uat_dbf_") as tmp:
        tmp_dir = Path(tmp)
        cmd = [
            sys.executable,
            str(gen),
            "--clms-csv",
            str(clms_csv),
            "--clmp-csv",
            str(clmp_csv),
            "--output-dir",
            str(tmp_dir),
            "--run-mode",
            "UAT",
        ]
        rc = subprocess.call(cmd)
        if rc != 0:
            raise DbfAppendPackageError(f"claims DBF generator rc={rc}")

        pairs = [
            ("QUIKCLMS_PHASE19_UAT.DBF", "QUIKCLMS.DBF"),
            ("QUIKCLMS_PHASE19_UAT.DBT", "QUIKCLMS.DBT"),
            ("QUIKCLMP_PHASE19_UAT.DBF", "QUIKCLMP.DBF"),
        ]
        for src_name, dst_name in pairs:
            src = tmp_dir / src_name
            if not src.is_file():
                raise DbfAppendPackageError(f"generator missing {src_name}")
            shutil.copy2(src, tmp_dir / dst_name)

        for junk in ("QUIKCLMP.DBT", "QUIKCLMP_PHASE19_UAT.DBT"):
            p = tmp_dir / junk
            if p.is_file():
                p.unlink()

        # Atomically replace staging short-name + phase19 outputs.
        replace_names = [
            "QUIKCLMS_PHASE19_UAT.DBF",
            "QUIKCLMS_PHASE19_UAT.DBT",
            "QUIKCLMP_PHASE19_UAT.DBF",
            "QUIKCLMS.DBF",
            "QUIKCLMS.DBT",
            "QUIKCLMP.DBF",
        ]
        for name in replace_names:
            src = tmp_dir / name
            if not src.is_file():
                continue
            dst = staging / name
            tmp_dst = staging / f".{name}.tmp"
            if tmp_dst.exists():
                tmp_dst.unlink()
            shutil.copy2(src, tmp_dst)
            tmp_dst.replace(dst)

        for junk in ("QUIKCLMP.DBT", "quikclmp.dbt", "QUIKCLMP_PHASE19_UAT.DBT"):
            p = staging / junk
            if p.is_file():
                p.unlink()

    clms_n = len(pd.read_csv(clms_csv, dtype=str))
    clmp_n = len(pd.read_csv(clmp_csv, dtype=str))
    gate = validate_claims_dbf_join(
        staging, expect_clms_rows=clms_n, expect_clmp_rows=clmp_n
    )
    if not gate["ok"]:
        raise DbfAppendPackageError(
            "claims DBF join validation failed: " + "; ".join(gate["fails"])
        )
    return {"ok": True, "staging": str(staging), "dbf_gate": gate}


def place_claims_uat_dbfs(
    repo_root: str | Path,
    append_output: str | Path = DEFAULT_APPEND_OUTPUT,
) -> dict[str, Any]:
    """Copy Phase19/UAT claims DBF+DBT into Append Tool output (memo-safe)."""
    staging = Path(repo_root) / "QLA_Migration" / "Staging" / "claims_uat_dbf"
    dest = Path(append_output)
    dest.mkdir(parents=True, exist_ok=True)

    # Remove stale claims artifacts before placement.
    for stale_name in (
        "QUIKCLMS.DBF",
        "quikclms.dbf",
        "QUIKCLMS.DBT",
        "quikclms.dbt",
        "QUIKCLMP.DBF",
        "quikclmp.dbf",
        "QUIKCLMP.DBT",
        "quikclmp.dbt",
    ):
        p = dest / stale_name
        if p.is_file():
            p.unlink()

    specs = [
        ("QUIKCLMS.DBF", "QUIKCLMS_PHASE19_UAT.DBF", ("QUIKCLMS.DBF", "quikclms.dbf")),
        ("QUIKCLMS.DBT", "QUIKCLMS_PHASE19_UAT.DBT", ("QUIKCLMS.DBT", "quikclms.dbt")),
        ("QUIKCLMP.DBF", "QUIKCLMP_PHASE19_UAT.DBF", ("QUIKCLMP.DBF", "quikclmp.dbf")),
    ]

    copied: list[dict[str, Any]] = []
    missing: list[str] = []
    for preferred, fallback, out_names in specs:
        src = staging / preferred
        if not src.is_file():
            src = staging / fallback
        if not src.is_file():
            missing.append(preferred)
            continue
        for out_name in out_names:
            dst = dest / out_name
            shutil.copy2(src, dst)
            copied.append({"src": str(src), "dst": str(dst), "size": dst.stat().st_size})

    for junk in ("QUIKCLMP.DBT", "quikclmp.dbt"):
        p = dest / junk
        if p.is_file():
            p.unlink()

    ok = len(missing) == 0 and len(copied) >= 3
    result = {
        "ok": ok,
        "staging": str(staging),
        "copied": copied,
        "missing": missing,
    }
    if not ok:
        raise DbfAppendPackageError(f"claims place incomplete missing={missing}")
    return result


def purge_append_claims_artifacts(append_output: str | Path) -> list[str]:
    """Remove claims DBF/DBT from Append Tool output so stale payee packages cannot load."""
    dest = Path(append_output)
    removed: list[str] = []
    if not dest.is_dir():
        return removed
    for name in (
        "QUIKCLMS.DBF",
        "quikclms.dbf",
        "QUIKCLMS.DBT",
        "quikclms.dbt",
        "QUIKCLMP.DBF",
        "quikclmp.dbf",
        "QUIKCLMP.DBT",
        "quikclmp.dbt",
    ):
        p = dest / name
        if p.is_file():
            p.unlink()
            removed.append(name)
    return removed


def finalize_dbf_append_tool_package(
    output_dir: str | Path,
    repo_root: str | Path,
    append_input: str | Path = DEFAULT_APPEND_INPUT,
    append_output: str | Path = DEFAULT_APPEND_OUTPUT,
    *,
    publish_csvs: bool = True,
    require_golden: bool = False,
    require_claims: bool | None = None,
) -> dict[str, Any]:
    """Publish safe CSVs + align/regenerate/place memo/claims DBFs."""
    result: dict[str, Any] = {
        "output_dir": _norm(output_dir),
        "append_input": _norm(append_input),
        "append_output": _norm(append_output),
    }
    out = Path(output_dir)
    root = Path(repo_root)
    staging = root / "QLA_Migration" / "Staging" / "claims_uat_dbf"
    tv = out / "Test_Validation"

    if publish_csvs:
        result["csv_publish"] = publish_append_input_csvs(output_dir, append_input)

    # Defense-in-depth: align payee MSEQ before any claims DBF regenerate/place.
    clms_csv = out / "quikclms.csv"
    clmp_csv = out / "quikclmp.csv"
    mstr_csv = out / "quikmstr.csv"
    has_clms = clms_csv.is_file()
    has_clmp = clmp_csv.is_file()
    has_mstr = mstr_csv.is_file()
    # Policy master implies claims package is required for UAT handoff.
    claims_required = bool(require_claims) if require_claims is not None else has_mstr

    if has_clms and has_clmp:
        try:
            result["mseq_align"] = align_claims_csv_dir(
                out,
                test_validation_dir=tv,
                require_golden=require_golden,
            )
            result["claims_regen"] = regenerate_claims_uat_dbfs(out, staging, root)
            result["claims"] = place_claims_uat_dbfs(root, append_output)
            # Final Append-output gate (same join checks on placed short names).
            placed_gate = validate_claims_dbf_join(
                append_output,
                expect_clms_rows=result["claims_regen"]["dbf_gate"]["clms_rows"],
                expect_clmp_rows=result["claims_regen"]["dbf_gate"]["clmp_rows"],
            )
            result["append_claims_gate"] = placed_gate
            if not placed_gate["ok"]:
                raise DbfAppendPackageError(
                    "append output claims gate failed: " + "; ".join(placed_gate["fails"])
                )
        except (ClaimsPayeeMseqAlignError, DbfAppendPackageError):
            raise
        except Exception as exc:
            raise DbfAppendPackageError(f"claims package failed: {exc}") from exc
    else:
        purged = purge_append_claims_artifacts(append_output)
        result["claims_purged"] = purged
        if has_clms ^ has_clmp:
            raise DbfAppendPackageError(
                "claims package incomplete: need both quikclms.csv and quikclmp.csv "
                f"(clms={has_clms}, clmp={has_clmp}); purged_stale={purged}"
            )
        if claims_required:
            raise DbfAppendPackageError(
                "claims package required (quikmstr present or require_claims=True) but "
                f"Output quikclms/quikclmp missing; purged_stale={purged}"
            )
        result["claims"] = {
            "ok": True,
            "skipped": True,
            "reason": "claims_not_required_no_csv",
            "purged_stale": purged,
        }

    memo_csv = out / "quikmemo.csv"
    if memo_csv.is_file() or has_mstr:
        result["quikmemo"] = place_quikmemo_dbf(output_dir, append_output)
        if not result["quikmemo"].get("ok"):
            raise DbfAppendPackageError(
                f"quikmemo package failed: {result['quikmemo'].get('error') or result['quikmemo']}"
            )
    else:
        result["quikmemo"] = {
            "ok": True,
            "skipped": True,
            "reason": "memo_not_required_no_csv",
        }

    claims_ok = bool((result.get("claims") or {}).get("ok"))
    memo_ok = bool((result.get("quikmemo") or {}).get("ok"))
    result["ok"] = claims_ok and memo_ok
    if not result["ok"]:
        raise DbfAppendPackageError("Append Tool package incomplete")
    return result
