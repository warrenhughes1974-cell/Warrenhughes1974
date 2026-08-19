"""Read-only Issue 141 risk sim: PPBEN BA PLAN_CODE -> PCOVR.PRODUCT_TYPE.

Does not write Output or change converters.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = ROOT / "Issue_Log_Items" / "Issue_141" / "evidence"

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import normalize  # noqa: E402


def _norm(v: str) -> str:
    return normalize(v)


def _cols(fieldnames):
    return {str(c).replace("\ufeff", "").strip().upper(): c for c in fieldnames}


def main() -> None:
    pcovr = next(SRC.glob("PCOVR_Coverage_Extract*.csv"))
    cov_pt = {}
    with pcovr.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        r = csv.DictReader(fh)
        cols = _cols(r.fieldnames)
        for row in r:
            cov = _norm(row.get(cols["COVERAGE_ID"], ""))
            if not cov or set(cov) <= set("-"):
                continue
            cov_pt[cov] = str(row.get(cols["PRODUCT_TYPE"], "") or "").strip()

    ppben = next(SRC.glob("PPBEN_PolicyBenefit_Extract*.csv"))
    ba = {}
    with ppben.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        r = csv.DictReader(fh)
        cols = _cols(r.fieldnames)
        for row in r:
            pol = _norm(row.get(cols["POLICY_NUMBER"], ""))
            if not pol or set(pol) <= set("-"):
                continue
            seq = str(row.get(cols["BENEFIT_SEQ"], "") or "").strip()
            if seq in ("1", "1.0"):
                ba[pol] = _norm(row.get(cols["PLAN_CODE"], ""))

    spec = list(csv.DictReader((OUT / "quikspec.csv").open(newline="", encoding="utf-8-sig", errors="replace")))
    qp = {}
    with (OUT / "quikplan.csv").open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            qp[_norm(row.get("PLAN", ""))] = {
                "PRODUCT": str(row.get("PRODUCT", "") or "").strip(),
                "HLOB": str(row.get("HLOB", "") or "").strip(),
                "MKTG": str(row.get("MKTG", "") or "").strip(),
            }

    ridr_base = {}
    with (OUT / "quikridr.csv").open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("MPHASE", "") or "").strip() == "1":
                ridr_base[_norm(row.get("MPOLICY", ""))] = _norm(row.get("MPLAN", ""))

    would = Counter()
    vs_plan_product = Counter()
    traces = []
    want = {"9010143726C", "9010148272C", "9010713704C"}
    miss = 0
    for row in spec:
        qla = _norm(row.get("MPOLICY", ""))
        lp = qla[:-1] if qla.endswith("C") else qla
        plan = ba.get(lp) or ba.get(qla)
        pt = cov_pt.get(plan)
        if pt is None and plan:
            compact = " ".join(plan.split())
            pt = cov_pt.get(compact)
            if pt is not None:
                plan = compact
        if pt is None:
            miss += 1
            would["MISSING"] += 1
            continue
        would[pt] += 1
        mplan = ridr_base.get(qla, "")
        cur_prod = qp.get(mplan, {}).get("PRODUCT", "")
        if cur_prod != pt:
            vs_plan_product["differs_from_quikplan_PRODUCT"] += 1
        else:
            vs_plan_product["matches_quikplan_PRODUCT"] += 1
        if qla in want:
            traces.append(
                {
                    "policy": qla,
                    "ppben_plan": plan,
                    "mplan": mplan,
                    "proposed_resrvcat": pt,
                    "quikplan_product": cur_prod,
                    "quikplan_hlob": qp.get(mplan, {}).get("HLOB", ""),
                    "vanish": row.get("VANISH"),
                    "resstate": row.get("RESSTATE"),
                }
            )

    summary = {
        "quikspec_rows": len(spec),
        "ppben_ba_rows": len(ba),
        "pcovr_coverages": len(cov_pt),
        "missing_join": miss,
        "proposed_resrvcat": dict(would),
        "vs_current_quikplan_product": dict(vs_plan_product),
        "traces": traces,
        "iswl_plan_tags_must_stay": {
            p: v for p, v in qp.items() if v.get("HLOB") == "ISWLFE" or v.get("PRODUCT") == "ISWLFE"
        },
    }
    EVID.mkdir(parents=True, exist_ok=True)
    outp = EVID / "issue141_risk_impact_summary.json"
    outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(outp), "rows": len(spec), "missing": miss, "codes": dict(would)}, indent=2))


if __name__ == "__main__":
    main()
