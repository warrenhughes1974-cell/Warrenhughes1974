"""
Headless Phase 1 reinsurance runner: PROD_PTRTY/PREIN/PREINTRT -> QuikRein/QuikRmst QA reports.

Usage (from repo root):
  python plan_analysis/phase_r9_quikrein_rmst/reinsurance_runner.py

Environment:
  QLA_PTRTY_PATH / QLA_PREIN_PATH / QLA_PREINTRT_PATH — override LifePRO extracts
  QLA_CROSSWALK_PATH — Master_Crosswalk for MPOLICY mapping
  QLA_QUIKMSTR_PATH / QLA_QUIKRIDR_PATH — converted policy/rider CSVs
  QLA_ENABLE_REINSURANCE_EMIT=1 — required for app batch; runner always executes
  QLA_REINSURANCE_WRITE_OUTPUT=1 — write quikrein.csv + quikrmst.csv to Output/
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qla_core.lifepro_source_resolver import resolve_reinsurance_sources
from qla_core.quikplan_converter import load_crosswalk_map
from qla_core.reinsurance_converter import convert_reinsurance_phase1, load_derivation_rules


def _env_path(name: str, fallback: str = "") -> str:
    val = os.environ.get(name, "").strip()
    return val if val and os.path.isfile(val) else fallback


def _default_src_dir() -> str:
    return os.path.join(_REPO_ROOT, "QLA_Migration", "Source")


def main() -> int:
    phase_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = _default_src_dir()
    ptrty = _env_path("QLA_PTRTY_PATH")
    prein = _env_path("QLA_PREIN_PATH")
    preintrt = _env_path("QLA_PREINTRT_PATH")
    if not (ptrty and prein and preintrt):
        p, pl, pi, pil, pr, prl = resolve_reinsurance_sources(src_dir)
        ptrty = ptrty or p
        prein = prein or pi
        preintrt = preintrt or pr
    cw_path = _env_path(
        "QLA_CROSSWALK_PATH",
        os.path.join(_REPO_ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv"),
    )
    cw_map = load_crosswalk_map(cw_path) if os.path.isfile(cw_path) else {}
    out_dir = os.path.join(_REPO_ROOT, "QLA_Migration", "Output")
    qm = _env_path("QLA_QUIKMSTR_PATH", os.path.join(out_dir, "quikmstr.csv"))
    qr = _env_path("QLA_QUIKRIDR_PATH", os.path.join(out_dir, "quikridr.csv"))
    rules = load_derivation_rules()

    for label, path in (
        ("PROD_PTRTY", ptrty),
        ("PREIN", prein),
        ("PREINTRT", preintrt),
    ):
        if not path or not os.path.isfile(path):
            print(f"ERROR: {label} extract not found: {path or '(missing)'}")
            return 1

    print(f"PROD_PTRTY: {ptrty}")
    print(f"PREIN: {prein}")
    print(f"PREINTRT: {preintrt}")
    print(f"Reports: {phase_dir}")
    if cw_map:
        print(f"Crosswalk: {cw_path}")
    if os.path.isfile(qm):
        print(f"quikmstr: {qm}")
    if os.path.isfile(qr):
        print(f"quikridr: {qr}")

    rein_df, rmst_df, trace_df, rein_exc, rmst_exc, stats = convert_reinsurance_phase1(
        ptrty,
        prein,
        preintrt,
        cw_map=cw_map,
        rules=rules,
        output_dir=phase_dir,
        quikmstr_path=qm if os.path.isfile(qm) else None,
        quikridr_path=qr if os.path.isfile(qr) else None,
    )

    print("\n--- Phase 1 Reinsurance summary ---")
    for k in (
        "ptrty_rows",
        "prein_rows",
        "preintrt_rows",
        "preintrt_rows_canonical",
        "preintrt_superseded",
        "quikrein_emitted",
        "quikrmst_emitted",
        "quikrein_exceptions",
        "quikrmst_exceptions",
        "defaulted_fields",
        "ceded_reconciliation_ok",
        "ceded_source_total",
        "ceded_emit_total",
    ):
        if k in stats:
            print(f"  {k}: {stats[k]}")

    if os.environ.get("QLA_REINSURANCE_WRITE_OUTPUT", "").strip() == "1":
        os.makedirs(out_dir, exist_ok=True)
        rein_path = os.path.join(out_dir, "quikrein.csv")
        rmst_path = os.path.join(out_dir, "quikrmst.csv")
        rein_df.to_csv(rein_path, index=False)
        rmst_df.to_csv(rmst_path, index=False)
        print(f"\nGATED OUTPUT: {rein_path} ({len(rein_df)} rows)")
        print(f"GATED OUTPUT: {rmst_path} ({len(rmst_df)} rows)")

    if stats.get("report_paths"):
        print("\nReports written:")
        for name, path in sorted(stats["report_paths"].items()):
            print(f"  {name}: {path}")

    ok = (
        stats.get("ceded_reconciliation_ok")
        and stats.get("quikrein_emitted", 0) >= 1
        and stats.get("quikrmst_emitted", 0) == stats.get("preintrt_rows_canonical", stats.get("quikrmst_emitted", 0))
        and stats.get("quikrmst_exceptions", 0) == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
