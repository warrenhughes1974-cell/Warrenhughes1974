"""Issue #142 regression — engine partition simulation + Output integrity checks."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.issue142_sl_rider import (  # noqa: E402
    ISSUE142_PLAN,
    prepare_active_sl_for_emit,
    sl_active_mask,
)
from qla_core.sl_benefit_governance import SL_BENEFIT_TYPE  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source" / "PPBEN_PolicyBenefit_Extract_20260630.csv"

results: dict[str, object] = {}
fails: list[str] = []

# --- 1. Engine partition simulation (mirrors app.py v59.04 block) ---
source = pd.read_csv(SRC, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
source.columns = [str(c).strip().upper() for c in source.columns]
_qr_bt = source["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
_sl_mask = _qr_bt == SL_BENEFIT_TYPE
_sl_active = sl_active_mask(source, _sl_mask)
_sl_suppress = _sl_mask & ~_sl_active

results["sim_sl_total"] = int(_sl_mask.sum())
results["sim_sl_active"] = int(_sl_active.sum())
results["sim_sl_suppressed"] = int(_sl_suppress.sum())
if int(_sl_active.sum()) != 22:
    fails.append(f"engine sim: active SL = {int(_sl_active.sum())} (expected 22)")
if int(_sl_suppress.sum()) != 46:
    fails.append(f"engine sim: suppressed SL = {int(_sl_suppress.sum())} (expected 46)")

transformed = prepare_active_sl_for_emit(source, _sl_active)
kept = transformed[~(_qr_bt.isin(["UV", "FV"]) | _sl_suppress)]
sl_kept = kept[kept.index.isin(source.index[_sl_active])]
results["sim_kept_sl_rows"] = int(len(sl_kept))
if not (sl_kept["PLAN_CODE"].str.strip() == ISSUE142_PLAN).all():
    fails.append("engine sim: not all active SL rows routed to 9SUBLF")
if not (sl_kept["VALUE_PER_UNIT"].str.strip() == "0").all():
    fails.append("engine sim: not all active SL rows have VALUE_PER_UNIT=0")
non_sl_changed = (
    transformed.loc[~_sl_active, ["PLAN_CODE", "VALUE_PER_UNIT"]]
    .ne(source.loc[~_sl_active, ["PLAN_CODE", "VALUE_PER_UNIT"]])
    .any()
    .any()
)
if bool(non_sl_changed):
    fails.append("engine sim: transform touched non-active-SL rows")
results["sim_non_sl_rows_touched"] = bool(non_sl_changed)

# --- 2. Output quikridr integrity ---
ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str, encoding="latin1").fillna("")
is_sublf = ridr["MPLAN"].astype(str).str.strip().str.upper() == ISSUE142_PLAN
results["out_quikridr_rows"] = int(len(ridr))
results["out_9sublf_rows"] = int(is_sublf.sum())
if int(is_sublf.sum()) != 22:
    fails.append(f"Output quikridr 9SUBLF rows = {int(is_sublf.sum())} (expected 22)")

sublf = ridr[is_sublf]
if not (pd.to_numeric(sublf["MVPU"], errors="coerce").fillna(-1) == 0).all():
    fails.append("Output: 9SUBLF row with MVPU != 0")
amt = (
    pd.to_numeric(sublf["MUNIT"], errors="coerce").fillna(0)
    * pd.to_numeric(sublf["MVPU"], errors="coerce").fillna(0)
).sum()
results["out_9sublf_amount_insured_total"] = float(amt)
if amt != 0:
    fails.append(f"Output: 9SUBLF amount insured total = {amt} (expected 0)")

# duplicate phase guard
dupes = ridr.duplicated(subset=["MPOLICY", "MPHASE"], keep=False)
dupe_rows = ridr[dupes]
results["out_dup_policy_phase_rows"] = int(len(dupe_rows))
if len(dupe_rows):
    fails.append(
        f"Output: duplicate (MPOLICY, MPHASE) rows = {len(dupe_rows)} "
        f"e.g. {dupe_rows.iloc[0]['MPOLICY']}/{dupe_rows.iloc[0]['MPHASE']}"
    )

# --- 3. Non-SL rows unchanged vs last packaged baseline (DBF Append Tool input) ---
baseline = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\input\quikridr.csv")
if baseline.is_file():
    base = pd.read_csv(baseline, dtype=str, encoding="latin1").fillna("")
    cur_non = ridr[~is_sublf].reset_index(drop=True)
    base_non = base[
        base["MPLAN"].astype(str).str.strip().str.upper() != ISSUE142_PLAN
    ].reset_index(drop=True)
    results["baseline_rows"] = int(len(base_non))
    results["current_non_sublf_rows"] = int(len(cur_non))
    if len(cur_non) != len(base_non):
        fails.append(
            f"non-9SUBLF quikridr count {len(cur_non)} != baseline {len(base_non)}"
        )
    else:
        cols = [c for c in base_non.columns if c in cur_non.columns]
        h_cur = hashlib.md5(
            cur_non[cols].to_csv(index=False).encode("utf-8", "replace")
        ).hexdigest()
        h_base = hashlib.md5(
            base_non[cols].to_csv(index=False).encode("utf-8", "replace")
        ).hexdigest()
        results["non_sublf_hash_match"] = h_cur == h_base
        if h_cur != h_base:
            neq = (cur_non[cols] != base_non[cols]).any(axis=1)
            diff_pols = cur_non.loc[neq, "MPOLICY"].head(5).tolist()
            fails.append(f"non-9SUBLF rows differ from baseline; e.g. {diff_pols}")
else:
    results["baseline_rows"] = "baseline not found"

# --- 4. quikplan delta = exactly one 9SUBLF row ---
plan = pd.read_csv(OUT / "quikplan.csv", dtype=str, encoding="latin1").fillna("")
plans_sublf = plan[plan["PLAN"].astype(str).str.strip().str.upper() == ISSUE142_PLAN]
results["out_quikplan_rows"] = int(len(plan))
results["out_quikplan_9sublf"] = int(len(plans_sublf))
if len(plans_sublf) != 1:
    fails.append(f"quikplan 9SUBLF rows = {len(plans_sublf)} (expected 1)")
pbase = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\input\quikplan.csv")
if pbase.is_file():
    bplan = pd.read_csv(pbase, dtype=str, encoding="latin1").fillna("")
    bplan_non = bplan[
        bplan["PLAN"].astype(str).str.strip().str.upper() != ISSUE142_PLAN
    ].reset_index(drop=True)
    cplan_non = plan[
        plan["PLAN"].astype(str).str.strip().str.upper() != ISSUE142_PLAN
    ].reset_index(drop=True)
    cols = [c for c in bplan_non.columns if c in cplan_non.columns]
    same = len(bplan_non) == len(cplan_non) and bool(
        (bplan_non[cols].values == cplan_non[cols].values).all()
    )
    results["quikplan_non_sublf_match_baseline"] = same
    if not same:
        fails.append("quikplan non-9SUBLF rows differ from baseline")

results["verdict"] = "PASS" if not fails else "FAIL"
results["fails"] = fails

out_path = Path(__file__).resolve().parent / "issue142_regression_summary.json"
out_path.write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
sys.exit(0 if not fails else 1)
