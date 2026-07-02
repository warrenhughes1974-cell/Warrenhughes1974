"""
Headless QuikLoan runner (Issue #32 v1.2): PLOAN → QuikLoan QA reports.

Usage (from repo root):
  python plan_analysis/phase_l1_quikloan/quikloan_runner.py

Optional environment:
  QLA_PLOAN_PATH          — override PLOAN.csv path
  QLA_CROSSWALK_PATH      — Master_Crosswalk for MPOLICY mapping
  QLA_QUIKPLAN_PATH       — QuikPlan CSV for MLOANINTX lookup
  QLA_QUIKMSTR_PATH       — quikmstr CSV for orphan audit
  QLA_QUIKLOAN_WRITE_OUTPUT=1 — write gated candidate CSV to QLA_Migration/Output/quikloan.csv
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qla_core.quikloan_converter import (
    convert_quikloan_from_ploan,
    default_derivation_rules_path,
    load_derivation_rules,
)


def _default_ploan_path() -> str:
    env = os.environ.get("QLA_PLOAN_PATH", "").strip()
    if env and os.path.isfile(env):
        return env
    candidates = [
        os.path.join(_REPO_ROOT, "QLA_Migration", "Source", "PLOAN.csv"),
        os.path.join(_REPO_ROOT, "QLA_Migration", "Source", "PLOAN_LoanInformation_Extract_20260530.csv"),
        os.path.join(_REPO_ROOT, "QLA_Migration", "Source", "PLOAN_LoanInformation_Extract_20260427.csv"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return candidates[0]


def _default_crosswalk_path() -> str:
    env = os.environ.get("QLA_CROSSWALK_PATH", "").strip()
    if env:
        return env
    for p in (
        os.path.join(_REPO_ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv"),
        os.path.join(_REPO_ROOT, "Master_Crosswalk.csv"),
    ):
        if os.path.isfile(p):
            return p
    return ""


def _default_quikplan_path() -> str:
    env = os.environ.get("QLA_QUIKPLAN_PATH", "").strip()
    if env and os.path.isfile(env):
        return env
    for p in (
        os.path.join(_REPO_ROOT, "QLA_Migration", "Output", "quikplan.csv"),
        os.path.join(_REPO_ROOT, "plan_governance", "staged", "uat", "quikplan_staged.csv"),
    ):
        if os.path.isfile(p):
            return p
    return ""


def _default_quikmstr_path() -> str:
    env = os.environ.get("QLA_QUIKMSTR_PATH", "").strip()
    if env and os.path.isfile(env):
        return env
    p = os.path.join(_REPO_ROOT, "QLA_Migration", "Output", "quikmstr.csv")
    return p if os.path.isfile(p) else ""


def main() -> int:
    phase_dir = os.path.dirname(os.path.abspath(__file__))
    ploan_path = _default_ploan_path()
    cw_path = _default_crosswalk_path()
    qp_path = _default_quikplan_path()
    qm_path = _default_quikmstr_path()

    rules_path = default_derivation_rules_path()
    rules = load_derivation_rules(rules_path)

    if not os.path.isfile(ploan_path):
        print(f"ERROR: PLOAN extract not found: {ploan_path}")
        return 1

    print(f"PLOAN source: {ploan_path}")
    print(f"Rules: {rules_path}")
    print(f"Output dir: {phase_dir}")
    if cw_path:
        print(f"Crosswalk: {cw_path}")
    else:
        print("Crosswalk: (none) — SOURCE_POLICY preserved in trace")

    if qp_path:
        print(f"QuikPlan: {qp_path}")
    if qm_path:
        print(f"quikmstr: {qm_path}")

    passed_df, trace_df, exceptions_df, stats = convert_quikloan_from_ploan(
        ploan_path,
        rules=rules,
        output_dir=phase_dir,
        crosswalk_path=cw_path or None,
        quikplan_path=qp_path or None,
        quikmstr_path=qm_path or None,
    )

    print("\n--- Issue #32 QuikLoan summary ---")
    for k in (
        "raw_rows",
        "valid_rows",
        "excluded_rows",
        "latest_policies",
        "emit_passed",
        "emit_exceptions",
        "zero_balance_held",
        "mloanintx_fallback_count",
        "quikmstr_orphan_rows",
        "duplicate_mpolicy_in_emit",
    ):
        if k in stats:
            print(f"  {k}: {stats[k]}")

    if os.environ.get("QLA_QUIKLOAN_WRITE_OUTPUT", "").strip() == "1":
        out_dir = os.path.join(_REPO_ROOT, "QLA_Migration", "Output")
        os.makedirs(out_dir, exist_ok=True)
        out_name = rules.get("output_filename", "quikloan.csv")
        out_path = os.path.join(out_dir, out_name)
        passed_df.to_csv(out_path, index=False)
        print(f"\nGATED OUTPUT (QLA_QUIKLOAN_WRITE_OUTPUT=1): {out_path} ({len(passed_df)} rows)")
    else:
        print("\nProduction Output/quikloan.csv NOT written (set QLA_QUIKLOAN_WRITE_OUTPUT=1 to enable).")

    if stats.get("report_paths"):
        print("\nReports written:")
        for name, path in sorted(stats["report_paths"].items()):
            print(f"  {name}: {path}")

    if rules.get("pactg_reconciliation_enabled"):
        try:
            import importlib.util

            recon_path = os.path.join(phase_dir, "quikloan_reconciliation.py")
            spec = importlib.util.spec_from_file_location("quikloan_reconciliation", recon_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                out = mod.run_reconciliation(
                    ploan_latest_path=os.path.join(phase_dir, "ploan_latest_row_selection.csv"),
                    output_dir=phase_dir,
                    repo_root=_REPO_ROOT,
                )
                print(f"PACTG reconciliation: {out}")
        except Exception as exc:
            print(f"Note: PACTG reconciliation skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
