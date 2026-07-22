"""Issue #89 Risk — read-only simulation of MANNLFEE / modal fee restore.

Does NOT modify production Output or app.py.
Simulates: PPOLC POLICY_FEE -> base MANNLFEE; M*FEE = MANNLFEE x quikmstr factors/100.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
MAP = ROOT / "QLA_Migration" / "Mapping"
EVID = ROOT / "Issue_Log_Items" / "Issue_89" / "evidence"

TRACE = ["010310404C", "010367131C", "010391876C", "010713704C", "010779727C"]


def norm(v: str) -> str:
    return str(v or "").strip().upper()


def fnum(v: str) -> float:
    try:
        return float(str(v or "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def load_crosswalk() -> dict[str, str]:
    path = MAP / "Master_Crosswalk.csv"
    out: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            keys = list(row.keys())
            if len(keys) < 2:
                continue
            lp, qla = norm(row[keys[0]]), norm(row[keys[1]])
            if lp and qla:
                out[lp] = qla
    return out


def main() -> None:
    EVID.mkdir(parents=True, exist_ok=True)
    cw = load_crosswalk()

    # PPOLC fees
    ppolc_path = SRC / "PPOLC_PolicyMaster_Extract_20260630.csv"
    fee_by_qla: dict[str, float] = {}
    ppolc_fee_gt0 = 0
    with open(ppolc_path, newline="", encoding="latin1", errors="replace") as f:
        for row in csv.DictReader(f):
            lp = norm(row.get("POLICY_NUMBER"))
            fee = fnum(row.get("POLICY_FEE"))
            if fee <= 0:
                continue
            ppolc_fee_gt0 += 1
            qla = cw.get(lp)
            if qla:
                fee_by_qla[qla] = fee

    # quikmstr factors
    mstr_path = OUT / "quikmstr.csv"
    factors: dict[str, dict[str, float]] = {}
    with open(mstr_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            pol = norm(row.get("MPOLICY"))
            factors[pol] = {
                "MSEMI": fnum(row.get("MSEMI")),
                "MQTRL": fnum(row.get("MQTRL")),
                "MMTHD": fnum(row.get("MMTHD")),
                "MMTHB": fnum(row.get("MMTHB")),
            }

    # current ridr
    ridr_path = OUT / "quikridr.csv"
    rows_in = 0
    base_rows = 0
    current_mannlfee_gt0 = 0
    would_set_mannlfee = 0
    would_set_modal = 0
    missing_factor = 0
    fee_no_ridr = 0
    by_plan = Counter()
    sim_rows = []
    mprem_check = []

    with open(ridr_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            rows_in += 1
            pol = norm(row.get("MPOLICY"))
            phase = norm(row.get("MPHASE"))
            plan = norm(row.get("MPLAN"))
            cur_fee = fnum(row.get("MANNLFEE"))
            cur_mprem = row.get("MPREM", "")
            if phase not in ("1", "01"):
                continue
            base_rows += 1
            if cur_fee > 0:
                current_mannlfee_gt0 += 1
            prop = fee_by_qla.get(pol, 0.0)
            if prop > 0:
                would_set_mannlfee += 1
                by_plan[plan] += 1
                fac = factors.get(pol, {})
                if any(fac.get(k, 0) > 0 for k in ("MSEMI", "MQTRL", "MMTHD", "MMTHB")):
                    would_set_modal += 1
                    prop_s = round(prop * fac.get("MSEMI", 0) / 100, 4)
                    prop_q = round(prop * fac.get("MQTRL", 0) / 100, 4)
                    prop_d = round(prop * fac.get("MMTHD", 0) / 100, 4)
                    prop_b = round(prop * fac.get("MMTHB", 0) / 100, 4)
                else:
                    missing_factor += 1
                    prop_s = prop_q = prop_d = prop_b = 0.0
                if pol in TRACE or len(sim_rows) < 20:
                    sim_rows.append(
                        {
                            "MPOLICY": pol,
                            "MPLAN": plan,
                            "CUR_MANNLFEE": row.get("MANNLFEE", ""),
                            "PROP_MANNLFEE": f"{prop:.2f}",
                            "CUR_MSEMIFEE": row.get("MSEMIFEE", ""),
                            "PROP_MSEMIFEE": f"{prop_s:.4f}" if prop_s else "",
                            "PROP_MQTRLFEE": f"{prop_q:.4f}" if prop_q else "",
                            "PROP_MMTHDFEE": f"{prop_d:.4f}" if prop_d else "",
                            "PROP_MMTHBFEE": f"{prop_b:.4f}" if prop_b else "",
                            "MPREM": cur_mprem,
                            "MUNIT": row.get("MUNIT", ""),
                        }
                    )
            if pol in TRACE:
                mprem_check.append(
                    {
                        "MPOLICY": pol,
                        "MPHASE": phase,
                        "MPREM": cur_mprem,
                        "MANNLFEE_cur": row.get("MANNLFEE", ""),
                        "PROP_MANNLFEE": f"{prop:.2f}" if prop else "",
                    }
                )

    # fees in PPOLC with crosswalk but no base ridr
    base_pols = set()
    with open(ridr_path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if norm(row.get("MPHASE")) in ("1", "01"):
                base_pols.add(norm(row.get("MPOLICY")))
    for pol, fee in fee_by_qla.items():
        if pol not in base_pols:
            fee_no_ridr += 1

    # top fees (largest annual)
    top = sorted(
        ((p, fee_by_qla[p]) for p in fee_by_qla if p in base_pols),
        key=lambda x: -x[1],
    )[:15]

    summary = {
        "ridr_rows": rows_in,
        "base_phase_rows": base_rows,
        "ppolc_fee_gt0": ppolc_fee_gt0,
        "fee_mapped_to_qla": len(fee_by_qla),
        "current_base_mannlfee_gt0": current_mannlfee_gt0,
        "would_set_mannlfee": would_set_mannlfee,
        "would_set_modal": would_set_modal,
        "missing_factors_among_fee": missing_factor,
        "fee_no_base_ridr": fee_no_ridr,
        "top_plans": by_plan.most_common(15),
        "top_fees": top,
        "trace": mprem_check,
    }

    sim_path = EVID / "issue89_risk_simulation.csv"
    with open(sim_path, "w", newline="", encoding="utf-8") as f:
        if sim_rows:
            w = csv.DictWriter(f, fieldnames=list(sim_rows[0].keys()))
            w.writeheader()
            w.writerows(sim_rows)

    sum_path = EVID / "issue89_risk_summary.json"
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"Wrote {sim_path}")
    print(f"Wrote {sum_path}")


if __name__ == "__main__":
    main()
