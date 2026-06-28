"""
Issue #27 SL quikridr suppression validation (v57.39).

Usage:
  python tools/validators/validate_issue27_sl_quikridr.py
  python tools/validators/validate_issue27_sl_quikridr.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "1.0"
ENGINE_VERSION = "v57.39"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_MCW = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
DEFAULT_AUDIT = PROJECT_ROOT / "Issue_Log_Items" / "Issue_27" / "Issue_27_SL_Suppression_Audit.csv"
DEFAULT_SL_POP = PROJECT_ROOT / "Issue_Log_Items" / "Issue_27" / "Issue_27_SL_Impact_Population.csv"
TRACE_POLICY = "010448806C"


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def _ridr_amt(r) -> float:
    try:
        return round(float(r["MUNIT"] or 0) * float(r["MVPU"] or 0), 2)
    except ValueError:
        return 0.0


def validate(
    output_dir: Path,
    mcw_path: Path,
    audit_path: Path,
    sl_pop_path: Path,
) -> tuple[int, dict]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict = {}

    ridr_path = output_dir / "quikridr.csv"
    mstr_path = output_dir / "quikmstr.csv"
    if not ridr_path.is_file():
        errors.append(f"Missing quikridr.csv: {ridr_path}")
        return 1, {"errors": errors, "warnings": warnings, "metrics": metrics}

    ridr = _read_csv(ridr_path)
    ridr["_POL"] = ridr["MPOLICY"].str.strip()

    # SL policies from planning population
    if sl_pop_path.is_file():
        pop = _read_csv(sl_pop_path)
        sl_qla = sorted({str(x).strip() for x in pop["_QLA"] if str(x).strip()})
    elif audit_path.is_file():
        audit = _read_csv(audit_path)
        sl_qla = sorted({str(x).strip() for x in audit["QLA_POLICY_NUMBER"] if str(x).strip()})
    else:
        sl_qla = []
        warnings.append("No SL population or audit file — skipping fleet SL checks")

    metrics["sl_policies_expected"] = len(sl_qla)
    metrics["quikridr_total_rows"] = len(ridr)

    # Audit row count
    if audit_path.is_file():
        audit = _read_csv(audit_path)
        metrics["audit_rows"] = len(audit)
        if len(audit) != 68:
            warnings.append(f"Audit rows={len(audit)} (expected 68 from planning)")
    else:
        errors.append(f"Missing suppression audit: {audit_path}")

    # No SL phases — match audit (MPOLICY, MPHASE) pairs should not exist
    if audit_path.is_file():
        audit = _read_csv(audit_path)
        sl_phases = {
            (str(r["QLA_POLICY_NUMBER"]).strip(), str(r["BENEFIT_SEQ"]).strip())
            for _, r in audit.iterrows()
        }
        ridr["_PH"] = ridr["MPHASE"].str.strip()
        sl_in_output = ridr[
            ridr.apply(lambda r: (r["_POL"], r["_PH"]) in sl_phases, axis=1)
        ]
        metrics["sl_phases_in_quikridr"] = len(sl_in_output)
        if len(sl_in_output) > 0:
            errors.append(f"Found {len(sl_in_output)} quikridr rows matching suppressed SL phases")

    # Duplicate face on SL policies
    dup_count = 0
    for pol in sl_qla:
        sub = ridr[ridr["_POL"] == pol]
        seen: dict[tuple[float, str], str] = {}
        for _, r in sub.iterrows():
            a = _ridr_amt(r)
            if a <= 0:
                continue
            key = (a, str(r["MPLAN"]).strip())
            ph = str(r["MPHASE"]).strip()
            if key in seen:
                dup_count += 1
                errors.append(f"Duplicate face {pol}: phase {seen[key]} and {ph} both {key[0]} MPLAN={key[1]}")
            else:
                seen[key] = ph
    metrics["duplicate_face_pairs_sl_policies"] = dup_count

    # Trace policy 010448806C
    trace = ridr[ridr["_POL"] == TRACE_POLICY]
    metrics["trace_policy"] = TRACE_POLICY
    metrics["trace_quikridr_rows"] = len(trace)
    if len(trace) != 2:
        errors.append(f"{TRACE_POLICY}: expected 2 quikridr rows, got {len(trace)}")
    else:
        faces = [_ridr_amt(r) for _, r in trace.iterrows()]
        if faces.count(5778.0) > 1:
            errors.append(f"{TRACE_POLICY}: duplicate 5778.00 face still present")

    # MMODEPREM unchanged for SL premium population
    if mstr_path.is_file() and sl_pop_path.is_file():
        mstr = _read_csv(mstr_path)
        mstr["_POL"] = mstr["MPOLICY"].str.strip()
        prem_path = PROJECT_ROOT / "Issue_Log_Items" / "Issue_27" / "Issue_27_SL_Premium_Population.csv"
        if prem_path.is_file():
            prem = _read_csv(prem_path)
            prem_mismatch = 0
            for _, r in prem.iterrows():
                qla = str(r["QLA"]).strip()
                pp = float(r["PPOLC_MODE_PREM"])
                ms = mstr[mstr["_POL"] == qla]
                if ms.empty:
                    continue
                mm = float(str(ms.iloc[0]["MMODEPREM"]).strip() or 0)
                if abs(pp - mm) > 0.10:
                    prem_mismatch += 1
            metrics["premium_bearing_sl_mmodeprem_match"] = len(prem) - prem_mismatch
            metrics["premium_bearing_sl_mmodeprem_mismatch"] = prem_mismatch
            if prem_mismatch:
                errors.append(f"MMODEPREM mismatch on {prem_mismatch} premium-bearing SL policies")

    return (1 if errors else 0), {
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #27 SL quikridr validation")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mcw", type=Path, default=DEFAULT_MCW)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--sl-pop", type=Path, default=DEFAULT_SL_POP)
    args = parser.parse_args()

    print("=" * 72)
    print(f"ISSUE #27 SL QUIKRIDR VALIDATION (script v{SCRIPT_VERSION}, engine {ENGINE_VERSION})")
    print(f"Output: {args.output_dir}")
    print("=" * 72)

    rc, result = validate(args.output_dir, args.mcw, args.audit, args.sl_pop)
    print(json.dumps(result["metrics"], indent=2))
    for w in result["warnings"]:
        print(f"WARNING: {w}")
    for e in result["errors"]:
        print(f"ERROR: {e}")
    print("=" * 72)
    print("PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
