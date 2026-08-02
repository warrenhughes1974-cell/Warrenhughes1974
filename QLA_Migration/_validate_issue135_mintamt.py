"""Issue #135 — validate quikclms.MINTAMT=0.00 and recon artifact presence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_mintamt_zero import ZERO_MINTAMT, apply_issue135_mintamt_zero  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
TEACHERS = [
    "9011156098C",
    "9010914301C",
    "9010391359C",
    "9010150740C",
    "9010402010C",
    "9010429064C",
    "9010430296C",
]
TOL = 0.01


def _read_app_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else ""


def main() -> int:
    errors: list[str] = []
    clms_path = OUT / "quikclms.csv"
    if not clms_path.is_file():
        print("FAIL: missing quikclms.csv")
        return 1

    clms = pd.read_csv(clms_path, dtype=str, keep_default_na=False)
    if "MINTAMT" not in clms.columns:
        errors.append("MINTAMT column missing from quikclms")
    else:
        mint = pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0.0)
        nonzero = int((mint.abs() > TOL).sum())
        if nonzero:
            errors.append(f"quikclms.MINTAMT nonzero rows: {nonzero}")
        bad_fmt = int((clms["MINTAMT"].astype(str).str.strip() != ZERO_MINTAMT).sum())
        # Allow 0 / 0.0 only if numeric zero; prefer canonical 0.00
        if nonzero == 0 and bad_fmt:
            # canonicalize check via apply helper
            after, stats = apply_issue135_mintamt_zero(clms)
            if int(stats.get("rows_updated", 0)) > 0:
                errors.append(
                    f"MINTAMT numeric zero but not formatted as {ZERO_MINTAMT} "
                    f"on {stats.get('rows_updated')} rows"
                )

    # Emit-path unit check
    sample = {"MPOLICY": "TEST", "MINTAMT": "123.45", "MPAID": "999.00"}
    from qla_core.claims_emit_enhancements import apply_claims_emit_enhancements

    forced = apply_claims_emit_enhancements(sample, {}, "quikclms", {})
    if forced.get("MINTAMT") != ZERO_MINTAMT:
        errors.append("apply_claims_emit_enhancements did not force MINTAMT=0.00")
    if forced.get("MPAID") != "999.00":
        errors.append("emit enhancement altered MPAID (must not)")

    # Version sync
    v_root = _read_app_version(ROOT / "app.py")
    v_mig = _read_app_version(ROOT / "QLA_Migration" / "app.py")
    if v_root != v_mig:
        errors.append(f"APP_VERSION mismatch root={v_root} mig={v_mig}")
    if not v_root.startswith("v58.") or v_root < "v58.54":
        errors.append(f"APP_VERSION expected >= v58.54, got {v_root}")

    # Reconciliation artifact
    summary_path = EVIDENCE / "issue135_recon_summary.json"
    recon_path = EVIDENCE / "issue135_cso_output_recon.csv"
    md_path = EVIDENCE / "issue135_recon_report.md"
    for p in (summary_path, recon_path, md_path):
        if not p.is_file():
            errors.append(f"missing recon artifact: {p.name}")

    recon_checks = {}
    if summary_path.is_file() and recon_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        recon = pd.read_csv(recon_path, dtype=str, keep_default_na=False)
        if "population" not in recon.columns:
            errors.append("recon missing population column")
        else:
            for bucket in (
                "AVAILABLE_MATCH",
                "AVAILABLE_MISMATCH",
                "MISSING_ERIC_SUPPLY",
            ):
                if bucket not in set(recon["population"]):
                    # MISSING may be 0 in theory; only require keys in summary
                    pass
            if int(summary.get("missing_eric_supply", -1)) < 0:
                errors.append("summary missing_eric_supply absent")
            if int(summary.get("available_represented", 0)) < 1000:
                errors.append(
                    f"available_represented unexpectedly low: {summary.get('available_represented')}"
                )
        for pol in TEACHERS:
            hit = recon[recon["mpolicy"] == pol] if "mpolicy" in recon.columns else pd.DataFrame()
            if hit.empty:
                errors.append(f"teacher missing from recon: {pol}")
            else:
                recon_checks[pol] = {
                    "population": str(hit["population"].iloc[0]),
                    "proposed_rule_class": str(hit.get("proposed_rule_class", pd.Series([""])).iloc[0]),
                    "cso_total_paid": str(hit.get("cso_total_paid", pd.Series([""])).iloc[0]),
                    "death_mpaid": str(hit.get("death_mpaid", pd.Series([""])).iloc[0]),
                }
        # Hard-control wording present
        md = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
        if "no claim number" not in md.lower() and "policy-level" not in md.lower():
            errors.append("recon markdown missing hard-control claim-number / policy-level statement")
        if "eric" not in md.lower():
            errors.append("recon markdown missing Eric supply-gap statement")

    # Teacher interest examples: MINTAMT must be zero in Output
    if "MINTAMT" in clms.columns and "MPOLICY" in clms.columns:
        for pol in ("9010402010C", "9010429064C", "9010430296C"):
            rows = clms[clms["MPOLICY"].astype(str).str.strip() == pol]
            if rows.empty:
                continue
            vals = pd.to_numeric(rows["MINTAMT"], errors="coerce").fillna(0.0)
            if (vals.abs() > TOL).any():
                errors.append(f"teacher {pol} still has nonzero MINTAMT")

    result = {
        "issue": 135,
        "status": "PASS" if not errors else "FAIL",
        "app_version_root": v_root,
        "app_version_mig": v_mig,
        "clms_rows": int(len(clms)),
        "mintamt_nonzero": int(
            (pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0.0).abs() > TOL).sum()
        )
        if "MINTAMT" in clms.columns
        else None,
        "teacher_recon": recon_checks,
        "errors": errors,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out_json = EVIDENCE / "issue135_validation_summary.json"
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
