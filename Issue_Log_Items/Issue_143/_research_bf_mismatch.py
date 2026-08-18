"""Deeper Issue #143 research: BF RPU match vs mismatch cohorts."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

SRC = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source")
OUT = Path(__file__).resolve().parent / "evidence"


def fnum(x):
    if x is None:
        return None
    s = str(x).replace(",", "").strip()
    if s == "" or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm(x):
    return str(x or "").strip()


def seq_key(seq):
    try:
        return str(int(float(seq or "0")))
    except ValueError:
        return seq


def main():
    rpu = set()
    ppolc_extra = {}
    with (SRC / "PPOLC_PolicyMaster_Extract_20260630.csv").open(newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            if norm(row.get("PAID_UP_TYPE")) != "RU":
                continue
            pol = norm(row["POLICY_NUMBER"])
            rpu.add(pol)
            ppolc_extra[pol] = {
                "contract_code": norm(row.get("CONTRACT_CODE")),
                "contract_reason": norm(row.get("CONTRACT_REASON")),
                "paid_to": norm(row.get("PAID_TO_DATE")),
                "issue": norm(row.get("ISSUE_DATE")),
            }

    typ = {}
    with (SRC / "PPBENTYP_BenefitType_Extract_20260630.csv").open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pol = norm(row.get("POLICY_NUMBER"))
            if pol not in rpu:
                continue
            typ[(pol, seq_key(row.get("BENEFIT_SEQ")))] = row

    ben = {}
    with (SRC / "PPBEN_PolicyBenefit_Extract_20260630.csv").open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pol = norm(row.get("POLICY_NUMBER"))
            if pol not in rpu:
                continue
            ben[(pol, seq_key(row.get("BENEFIT_SEQ")))] = row

    match = []
    mismatch = []
    for (pol, seq), brow in ben.items():
        if seq != "1":
            continue
        trow = typ.get((pol, seq), {})
        if norm(trow.get("TYPE_CODE")) != "BF":
            continue
        units = fnum(brow.get("NUMBER_OF_UNITS")) or 0.0
        vpu = fnum(brow.get("VALUE_PER_UNIT")) or 0.0
        face = units * vpu
        db = fnum(trow.get("BF_CURRENT_DB")) or 0.0
        spec = fnum(trow.get("BF_SPECIFIED_AMT")) or 0.0
        fv = fnum(brow.get("FV_BALANCE2")) or 0.0
        rec = {
            "policy": pol,
            "plan": norm(brow.get("PLAN_CODE")),
            "status": norm(brow.get("STATUS_CODE")),
            "reason": norm(brow.get("STATUS_REASON")),
            "units": units,
            "vpu": vpu,
            "face": round(face, 2),
            "bf_current_db": db,
            "bf_specified_amt": spec,
            "fv_balance2": fv,
            "units_integer": abs(units - round(units)) < 1e-6,
            "spec_eq_db": abs(spec - db) <= 0.02,
            "face_eq_spec": abs(face - spec) <= 1.0,
            "bf_nfo": norm(trow.get("BF_NON_FORFEITURE")),
            "bf_opt": norm(trow.get("BF_DB_OPTION")),
            "var_covr": norm(trow.get("BF_VAR_COVR_FLAG")),
            "issue_age": norm(brow.get("ISSUE_AGE")),
            "issue_date": norm(brow.get("ISSUE_DATE")),
            "status_date": norm(brow.get("STATUS_DATE")),
            "product_type": norm(brow.get("PRODUCT_TYPE")),
            **ppolc_extra.get(pol, {}),
            "implied_units": round(db / vpu, 5) if vpu else None,
        }
        if abs(face - db) <= 1.0:
            match.append(rec)
        else:
            mismatch.append(rec)

    def cohort_stats(rows, name):
        return {
            "name": name,
            "n": len(rows),
            "plans": Counter(r["plan"] or "(blank)" for r in rows).most_common(),
            "status": Counter(r["status"] for r in rows).most_common(),
            "reason": Counter(r["reason"] for r in rows).most_common(),
            "integer_units": sum(1 for r in rows if r["units_integer"]),
            "spec_eq_db": sum(1 for r in rows if r["spec_eq_db"]),
            "face_eq_spec": sum(1 for r in rows if r["face_eq_spec"]),
            "bf_nfo": Counter(r["bf_nfo"] for r in rows).most_common(),
            "var_covr": Counter(r["var_covr"] for r in rows).most_common(),
            "product_type": Counter(r["product_type"] for r in rows).most_common(),
            "fv_gt0": sum(1 for r in rows if (r["fv_balance2"] or 0) > 0),
            "unit_values": sorted({r["units"] for r in rows if r["units_integer"]}),
        }

    report = {
        "match_stats": cohort_stats(match, "units_x_vpu_eq_bf_current_db"),
        "mismatch_stats": cohort_stats(mismatch, "units_x_vpu_ne_bf_current_db"),
        "mismatch_rows": sorted(mismatch, key=lambda r: r["policy"]),
        "match_integer_unit_examples": [r for r in match if r["units_integer"]][:20],
        "match_fractional_sample": [r for r in match if not r["units_integer"]][:8],
    }
    out = OUT / "issue143_bf_rpu_mismatch.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"match": report["match_stats"], "mismatch": report["mismatch_stats"]}, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
