"""Issue #142 — seed 9SUBLF on current Output and emit Active SL quikridr rows.

Uses the same transforms as the engine hook (PLAN=9SUBLF, VPU=0). Idempotent:
replaces any existing 9SUBLF rider rows for the Active SL population.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.issue142_sl_rider import (  # noqa: E402
    ISSUE142_PLAN,
    build_emit_audit_rows,
    seed_9sublf_plan,
    sl_active_mask,
    write_emit_audit,
)
from qla_core.lifepro_source_resolver import find_newest_matching  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402
from qla_core.rate_dbf_schema import map_rider_uwclass  # noqa: E402
from qla_core.sl_benefit_governance import SL_BENEFIT_TYPE  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC_DIR = ROOT / "QLA_Migration" / "Source"


def _f(v: object) -> float:
    try:
        return float(str(v or "").replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0


def _fmt_units(raw: object) -> str:
    return f"{_f(raw):.5f}"


def _fmt_prem(raw: object) -> str:
    v = _f(raw)
    if v == 0.0:
        return "0"
    return f"{v:.5f}"


def _resolve_ppben() -> Path:
    found = find_newest_matching(str(SRC_DIR), [r"^PPBEN[_ ]PolicyBenefit[_ ]Extract.*\.csv$"])
    if found:
        return Path(found)
    legacy = SRC_DIR / "PPBEN.csv"
    if legacy.is_file():
        return legacy
    raise FileNotFoundError("PPBEN extract not found under QLA_Migration/Source")


def main() -> int:
    ppben_path = _resolve_ppben()
    plan_path = OUT / "quikplan.csv"
    ridr_path = OUT / "quikridr.csv"
    if not plan_path.is_file() or not ridr_path.is_file():
        print("FAIL: quikplan.csv or quikridr.csv missing from Output")
        return 2

    plan = pd.read_csv(plan_path, dtype=str, encoding="latin1").fillna("")
    before_plans = len(plan)
    plan = seed_9sublf_plan(plan)
    plan.to_csv(plan_path, index=False, encoding="latin1")
    print(f"quikplan: {before_plans} -> {len(plan)} (9SUBLF present)")

    src = pd.read_csv(ppben_path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    src.columns = [str(c).strip().upper() for c in src.columns]
    bt = src["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
    sl_mask = bt == SL_BENEFIT_TYPE
    active = sl_active_mask(src, sl_mask)
    sl_active = src.loc[active].copy()
    print(f"Active SL source rows: {len(sl_active)} from {ppben_path.name}")

    ridr = pd.read_csv(ridr_path, dtype=str, encoding="latin1").fillna("")
    ridr["_P"] = ridr["MPOLICY"].astype(str).str.strip()
    keep = ~(ridr["MPLAN"].astype(str).str.strip().str.upper() == ISSUE142_PLAN)
    ridr = ridr.loc[keep].copy()

    new_rows: list[dict] = []
    schema = [c for c in ridr.columns if c != "_P"]
    for _, sl in sl_active.iterrows():
        lp = str(sl.get("POLICY_NUMBER", "")).strip()
        qla = format_qladmin_mpolicy(lp)
        tmpl_hits = ridr[ridr["_P"] == qla.strip()]
        if tmpl_hits.empty:
            print(f"WARN: no existing quikridr row for {qla}; skip")
            continue
        tmpl = tmpl_hits.sort_values("MPHASE").iloc[0].to_dict()
        row = {c: tmpl.get(c, "") for c in schema}
        units = _fmt_units(sl.get("NUMBER_OF_UNITS", ""))
        prem = _fmt_prem(sl.get("ANN_PREM_PER_UNIT", ""))
        seq = str(sl.get("BENEFIT_SEQ", "")).strip().replace(".0", "")
        uw = map_rider_uwclass(str(sl.get("UNDERWRITING_CLASS", "")).strip(), plan=ISSUE142_PLAN)
        row["MPOLICY"] = qla
        row["MPHASE"] = seq
        row["MPHSTAT"] = "22"
        row["MPLAN"] = ISSUE142_PLAN
        row["MPAR"] = "0"
        row["MUNIT"] = units
        row["MVPU"] = "0.00"
        row["MPREM"] = prem
        row["MSAVEUNIT"] = units
        row["MSAVEVPU"] = "0.00"
        row["MSAVEPREM"] = prem
        row["MSAVESTAT"] = "22"
        row["MUWCLASS"] = uw
        row["MANNLFEE"] = ""
        row["MSEMIFEE"] = ""
        row["MQTRLFEE"] = ""
        row["MMTHDFEE"] = ""
        row["MMTHBFEE"] = ""
        new_rows.append(row)

    add_df = pd.DataFrame(new_rows, columns=schema)
    out = pd.concat([ridr.drop(columns=["_P"]), add_df], ignore_index=True)
    out.to_csv(ridr_path, index=False, encoding="latin1")
    print(f"quikridr: wrote {len(add_df)} 9SUBLF rows (total {len(out)})")

    audit = build_emit_audit_rows(sl_active)
    audit_path = write_emit_audit(audit)
    print(f"emit audit: {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
