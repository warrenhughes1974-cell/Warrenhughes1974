#!/usr/bin/env python3
"""Grok second-pass — Issue #135 MATCH_CSO zero-payee cohort backfill."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue135_match_cso_zero_payee_backfill import (  # noqa: E402
    GOLDEN_ALLOWLIST,
    REASON,
)

EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
RESULT = EVID / "issue135_match_cso_zero_payee_grok_second_pass.json"
TOL = 0.01
GOLDEN = "9011156655C"


def _strip(v) -> str:
    return "" if v is None else str(v).strip()


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    fails: list[str] = []
    notes: list[str] = []

    clms = pd.read_csv(CLMS, dtype=str).fillna("")
    clmp = pd.read_csv(CLMP, dtype=str).fillna("")
    class_df = pd.read_csv(
        EVID / "issue135_match_cso_zero_payee_classification.csv", dtype=str
    ).fillna("")
    holds = pd.read_csv(
        EVID / "issue135_match_cso_zero_payee_holds.csv", dtype=str
    ).fillna("")
    meta = json.loads(
        (EVID / "issue135_match_cso_zero_payee_apply_meta.json").read_text(encoding="utf-8")
    )
    mod = (ROOT / "qla_core" / "issue135_match_cso_zero_payee_backfill.py").read_text(
        encoding="utf-8"
    )

    if "auto_discover" not in mod or "SAFE_BACKFILL" not in mod:
        fails.append("module missing cohort discover/classify path")
    if GOLDEN not in GOLDEN_ALLOWLIST:
        fails.append("golden allowlist missing 9011156655C")

    safe = class_df[class_df["class"].map(_strip) == "SAFE_BACKFILL"]
    if len(safe) < 137:
        fails.append(f"safe_n={len(safe)}<137")
    if len(holds) != 3:
        fails.append(f"hold_n={len(holds)}!=3")
    notes.append(f"cohort_classified={len(class_df)} safe={len(safe)} holds={len(holds)}")

    # Output: safe policies have payees; holds do not
    clmp_cnt = clmp.groupby(clmp["MPOLICY"].map(_strip)).size().to_dict()
    for pol in safe["mpolicy"].map(_strip):
        if int(clmp_cnt.get(pol, 0)) <= 0:
            fails.append(f"safe_still_zero:{pol}")
            break
    for pol in holds["mpolicy"].map(_strip):
        if int(clmp_cnt.get(pol, 0)) > 0:
            fails.append(f"hold_has_payees:{pol}")

    # Golden exact
    g = clmp[clmp["MPOLICY"].map(_strip) == GOLDEN]
    if len(g) != 4:
        fails.append(f"golden_payees={len(g)}")
    else:
        if abs(round(g["MAMOUNT"].map(_money).sum(), 2) - 5145.67) > TOL:
            fails.append("golden_sum_mismatch")
        exp = {str(e["mseq"]): e for e in GOLDEN_ALLOWLIST[GOLDEN]["expected_payees"]}
        for _, r in g.iterrows():
            e = exp.get(_strip(r["MSEQ"]))
            if not e:
                fails.append(f"golden_unexpected_mseq={r['MSEQ']}")
                continue
            if abs(_money(r["MAMOUNT"]) - float(e["amount"])) > TOL:
                fails.append(f"golden_amt_mseq{r['MSEQ']}")
            if _strip(r["MPAYNAME"]).upper() != _strip(e["name"]).upper():
                fails.append(f"golden_name_mseq{r['MSEQ']}")

    # No stubs / MCHECKNO invent
    audit = pd.read_csv(
        EVID / "issue135_match_cso_zero_payee_backfill_audit.csv", dtype=str
    ).fillna("")
    detail = audit[audit["mseq"].map(_strip) != "SUMMARY"]
    if detail["mpayname"].astype(str).str.contains("NEEDS_PAYEE|\\*\\*\\*", regex=True).any():
        fails.append("fabricated_stub_names_in_audit")
    if not all(_strip(x) in ("", "0") for x in detail["mcheckno"].tolist()):
        fails.append("nonblank_mcheckno_in_audit")

    # Meta consistency
    if int(meta.get("policies_backfilled", 0) or 0) != 137:
        fails.append(f"meta_policies={meta.get('policies_backfilled')}")
    if int(meta.get("rows_added", 0) or 0) != 194:
        fails.append(f"meta_rows={meta.get('rows_added')}")
    if meta.get("quikclms_mutated") is not False:
        fails.append("quikclms_mutated")

    # MINTAMT fleet
    mint_nz = int((pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0).abs() > TOL).sum())
    if mint_nz:
        fails.append(f"MINTAMT_nz={mint_nz}")

    # #134 marker
    marker_hits = int(
        clms["MEMOTEXT"].astype(str).str.contains("CSO_CONTROLLED_NO_PACTG_HISTORY", regex=False).sum()
    )
    if marker_hits < 1:
        fails.append("issue134_marker_missing")
    notes.append(f"issue134_marker_hits={marker_hits}")

    # Expansion wiring
    exp_txt = (ROOT / "qla_core" / "issue135_cso_claims_expansion.py").read_text(encoding="utf-8")
    if "auto_discover=True" not in exp_txt:
        fails.append("expansion_not_wired_auto_discover")

    # App version
    for p in (ROOT / "app.py", ROOT / "QLA_Migration" / "app.py"):
        if 'APP_VERSION = "v58.60"' not in p.read_text(encoding="utf-8"):
            fails.append(f"version_not_v58.60:{p.name}")

    result = {
        "reason": REASON + "_COHORT",
        "pass": len(fails) == 0,
        "fails": fails,
        "notes": notes,
        "safe_n": int(len(safe)),
        "hold_n": int(len(holds)),
        "policies_backfilled": int(meta.get("policies_backfilled", 0) or 0),
        "rows_added": int(meta.get("rows_added", 0) or 0),
        "golden_payees": int(len(g)),
        "issue135_status": "NOT closed; prior 9 HOLDs remain; 3 residual zero-payee holds",
        "confidence": "HIGH" if not fails else "LOW",
        "higher_model_needed": False,
    }
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Wrote", RESULT)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
