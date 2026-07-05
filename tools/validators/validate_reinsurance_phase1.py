#!/usr/bin/env python3
"""Phase 1 reinsurance conversion validators."""

from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from qla_core.lifepro_source_resolver import resolve_reinsurance_sources
from qla_core.quikplan_converter import load_crosswalk_map
from qla_core.reinsurance_converter import convert_reinsurance_phase1, load_derivation_rules
from qla_core.schema_constants import QUIKREIN_SCHEMA, QUIKRMST_SCHEMA


def _check_app_version_log_alignment() -> tuple[bool, str]:
    import re

    details: list[str] = []
    ok = True
    for rel in ("app.py", os.path.join("QLA_Migration", "app.py")):
        path = os.path.join(_REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        header = re.search(r"# Version:\s+(v[\d.]+)", text)
        header_ver = header.group(1) if header else ""
        log = re.search(r"Initializing Migration Engine (v[\d.]+)", text)
        log_ver = log.group(1) if log else ""
        if not header_ver or header_ver != log_ver:
            ok = False
            details.append(f"{rel}: header={header_ver or '?'} log={log_ver or '?'}")
    return ok, "; ".join(details) if details else "aligned"


def _default_paths() -> dict[str, str]:
    src = os.path.join(_REPO_ROOT, "QLA_Migration", "Source")
    ptrty, _, prein, _, preintrt, _ = resolve_reinsurance_sources(src)
    return {
        "ptrty": os.environ.get("QLA_PTRTY_PATH", ptrty),
        "prein": os.environ.get("QLA_PREIN_PATH", prein),
        "preintrt": os.environ.get("QLA_PREINTRT_PATH", preintrt),
        "crosswalk": os.path.join(_REPO_ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv"),
        "quikmstr": os.path.join(_REPO_ROOT, "QLA_Migration", "Output", "quikmstr.csv"),
        "quikridr": os.path.join(_REPO_ROOT, "QLA_Migration", "Output", "quikridr.csv"),
        "phase_dir": os.path.join(_REPO_ROOT, "plan_analysis", "phase_r9_quikrein_rmst"),
    }


def run_validation(*, write_json: str | None = None) -> dict:
    paths = _default_paths()
    rules = load_derivation_rules()
    cw = paths["crosswalk"] if os.path.isfile(paths["crosswalk"]) else None
    cw_map = load_crosswalk_map(cw) if cw else {}
    qm = paths["quikmstr"] if os.path.isfile(paths["quikmstr"]) else None
    qr = paths["quikridr"] if os.path.isfile(paths["quikridr"]) else None

    rein_df, rmst_df, trace_df, rein_exc, rmst_exc, stats = convert_reinsurance_phase1(
        paths["ptrty"],
        paths["prein"],
        paths["preintrt"],
        cw_map=cw_map,
        rules=rules,
        output_dir=paths["phase_dir"],
        quikmstr_path=qm,
        quikridr_path=qr,
    )

    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    add("quikrein_schema", list(rein_df.columns) == QUIKREIN_SCHEMA, str(list(rein_df.columns)))
    add("quikrmst_schema", list(rmst_df.columns) == QUIKRMST_SCHEMA, str(list(rmst_df.columns)))
    add("quikrein_row_count", len(rein_df) == stats.get("ptrty_rows", 0), f"emit={len(rein_df)} ptrty={stats.get('ptrty_rows')}")
    canonical = stats.get("preintrt_rows_canonical", stats.get("preintrt_rows", 0))
    add(
        "quikrmst_row_count",
        len(rmst_df) + stats.get("quikrmst_exceptions", 0) == canonical,
        f"emit={len(rmst_df)} exc={stats.get('quikrmst_exceptions')} canonical={canonical}",
    )
    add("ceded_reconciliation", bool(stats.get("ceded_reconciliation_ok")), f"src={stats.get('ceded_source_total')} emit={stats.get('ceded_emit_total')}")
    add("mreinco_populated", rein_df["MREINCO"].astype(str).str.strip().ne("").all() if len(rein_df) else True, "")
    add("mcomp_default_c", (rein_df["MCOMP"].astype(str).str.strip() == "C").all() if len(rein_df) else True, "")
    if len(rmst_df):
        rein_treaties = set(rein_df["MTREATY"].astype(str).str.strip().str.upper())
        rmst_treaties = set(rmst_df["MTREATY"].astype(str).str.strip().str.upper())
        add("rmst_treaties_in_quikrein", rmst_treaties <= rein_treaties, f"missing={sorted(rmst_treaties - rein_treaties)}")
        dup = rmst_df.duplicated(subset=["MPOLICY", "MPHASE", "MTREATY"]).sum()
        add("no_duplicate_rmst_keys", dup == 0, f"dup={dup}")
    if len(trace_df) and "CROSSWALK_CONFIDENCE" in trace_df.columns:
        add(
            "placeholder_crosswalk_flagged",
            (trace_df["CROSSWALK_CONFIDENCE"].astype(str).str.strip() == "Manual Placeholder").all(),
            "",
        )
    if len(rmst_df):
        mpct_blank = rmst_df["MPCTCEDED"].fillna("").astype(str).str.strip().eq("").all()
        add("mpctceded_blank_phase1", mpct_blank, "MPCTCEDED must remain blank/default in Phase 1")
    if len(rein_df):
        rein_treaties = set(rein_df["MTREATY"].astype(str).str.strip().str.upper())
        munich_in_rein = "MUNICH50" in rein_treaties
        munich_rmst = 0
        if len(rmst_df):
            munich_rmst = int(
                (rmst_df["MTREATY"].astype(str).str.strip().str.upper() == "MUNICH50").sum()
            )
        add(
            "munich50_quikrein_only",
            munich_in_rein and munich_rmst == 0,
            f"rein_has_munich50={munich_in_rein} rmst_munich50_rows={munich_rmst}",
        )
    ver_ok, ver_detail = _check_app_version_log_alignment()
    add("app_version_log_aligned", ver_ok, ver_detail)

    failed = [c for c in checks if c["status"] == "FAIL"]
    result = {
        "module": "reinsurance_phase1",
        "quikrein_rows": len(rein_df),
        "quikrmst_rows": len(rmst_df),
        "stats": {k: v for k, v in stats.items() if k != "report_paths"},
        "checks": checks,
        "overall": "PASS" if not failed else "FAIL",
        "failed_count": len(failed),
    }
    if write_json:
        os.makedirs(os.path.dirname(write_json) or ".", exist_ok=True)
        with open(write_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 reinsurance validators")
    parser.add_argument("--json", default="", help="Write JSON results path")
    args = parser.parse_args()
    out_path = args.json or os.path.join(
        _REPO_ROOT, "plan_analysis", "phase_r9_quikrein_rmst", "reinsurance_validation.json"
    )
    result = run_validation(write_json=out_path)
    print(json.dumps(result, indent=2))
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
