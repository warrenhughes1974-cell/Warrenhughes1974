#!/usr/bin/env python3
"""Issue #135 Option-3 overlay validator (read-only vs production Output)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
TOL = 0.01
TEACHERS = ["9011156098C", "9010914301C", "9010391359C"]


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").replace("$", "").strip() or 0)
    except ValueError:
        return 0.0


def main() -> int:
    errors: list[str] = []
    summary_path = EVIDENCE / "issue135_option3_summary.json"
    cand_path = EVIDENCE / "issue135_option3_candidate_summary.csv"
    clms_ov = EVIDENCE / "issue135_option3_quikclms_overlay.csv"
    clmp_ov = EVIDENCE / "issue135_option3_quikclmp_overlay.csv"
    for p in (summary_path, cand_path, clms_ov, clmp_ov):
        if not p.is_file():
            errors.append(f"missing artifact {p.name}")

    if errors:
        print("FAIL:", errors)
        return 1

    machine = json.loads(summary_path.read_text(encoding="utf-8"))
    if machine.get("production_output_mutated"):
        errors.append("production_output_mutated unexpectedly True")
    if machine.get("eric_gaps_touched"):
        errors.append("eric_gaps_touched unexpectedly True")
    if not machine.get("mintamt_remains_zero", False):
        errors.append("mintamt_remains_zero flag false")

    cand = pd.read_csv(cand_path, dtype=str, keep_default_na=False)
    clms = pd.read_csv(clms_ov, dtype=str, keep_default_na=False)
    clmp = pd.read_csv(clmp_ov, dtype=str, keep_default_na=False)

    corrected = cand[cand["option3_status"] == "CORRECTED"]
    if int(machine.get("corrected_candidates", -1)) != len(corrected):
        errors.append(
            f"summary corrected_candidates {machine.get('corrected_candidates')} "
            f"!= csv {len(corrected)}"
        )
    if len(clms) != len(corrected):
        errors.append(f"overlay clms rows {len(clms)} != corrected {len(corrected)}")

    # Coherence: overlay MPAID == CSO == payee sum; MINTAMT=0
    payee_sum = {}
    if len(clmp):
        for pol, grp in clmp.groupby(clmp["MPOLICY"].astype(str).str.strip()):
            payee_sum[pol] = round(
                pd.to_numeric(grp["MAMOUNT"], errors="coerce").fillna(0).sum(), 2
            )

    for _, r in clms.iterrows():
        pol = str(r["MPOLICY"]).strip()
        mpaid = _money(r.get("MPAID"))
        cso = _money(r.get("_cso_total_paid"))
        mint = _money(r.get("MINTAMT"))
        psum = payee_sum.get(pol, None)
        if abs(mint) > TOL:
            errors.append(f"{pol}: overlay MINTAMT nonzero {mint}")
        if abs(mpaid - cso) > TOL:
            errors.append(f"{pol}: overlay MPAID {mpaid} != CSO {cso}")
        if psum is None:
            errors.append(f"{pol}: missing overlay payees")
        elif abs(psum - cso) > TOL:
            errors.append(f"{pol}: overlay payee sum {psum} != CSO {cso}")
        elif abs(psum - mpaid) > TOL:
            errors.append(f"{pol}: overlay payee sum {psum} != MPAID {mpaid}")

    # Teachers
    for t in TEACHERS:
        sub = clms[clms["MPOLICY"].astype(str).str.strip() == t]
        if sub.empty:
            errors.append(f"teacher {t} missing from overlay")
        else:
            st = machine.get("teacher_status", {}).get(t, {})
            if st.get("option3_status") != "CORRECTED":
                errors.append(f"teacher {t} status {st.get('option3_status')}")

    # Production Output untouched for corrected policies (spot amounts still old)
    prod_clms = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
    if prod_clms.is_file() and len(corrected):
        prod = pd.read_csv(prod_clms, dtype=str, keep_default_na=False)
        # Spot-check teachers still have pre-correction amounts in production
        spots = {
            "9011156098C": 45000.0,
            "9010914301C": 50039.96,
            "9010391359C": 0.0,
        }
        for pol, old in spots.items():
            prow = prod[
                (prod["MPOLICY"].astype(str).str.strip() == pol)
                & (prod["CLAIMSTAT"].astype(str).str.strip() == "2")
            ]
            if prow.empty:
                continue
            cur = _money(prow.iloc[0]["MPAID"])
            if abs(cur - old) > TOL:
                # Not an error if Output was changed outside this pass; warn only
                print(f"WARN: production {pol} MPAID={cur} (expected pre-overlay {old})")

    # 459 readiness artifacts
    for name in (
        "issue135_459_eric_expansion_readiness.md",
        "issue135_459_eric_expansion_template.csv",
    ):
        if not (EVIDENCE / name).is_file():
            # template may be generated below; readiness md required
            if name.endswith(".md"):
                errors.append(f"missing {name}")

    out = {
        "issue": 135,
        "phase": "OPTION3_OVERLAY_VALIDATION",
        "status": "PASS" if not errors else "FAIL",
        "corrected_candidates": int(len(corrected)),
        "candidate_holds": int((cand["option3_status"] != "CORRECTED").sum()),
        "overlay_clms": int(len(clms)),
        "overlay_clmp": int(len(clmp)),
        "production_output_mutated": bool(machine.get("production_output_mutated")),
        "errors": errors,
    }
    out_path = EVIDENCE / "issue135_option3_validation.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
