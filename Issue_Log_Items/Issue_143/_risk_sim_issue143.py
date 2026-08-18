"""Read-only Issue #143 risk sim: BF RPU MUNIT = BF_CURRENT_DB / VPU when they differ."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974")
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
EVID.mkdir(exist_ok=True)
EPS = 0.01


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


def qla_key(pol):
    p = norm(pol)
    return p if p.endswith("C") else p + "C"


def main():
    rpu = set()
    with (SRC / "PPOLC_PolicyMaster_Extract_20260630.csv").open(newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            if norm(row.get("PAID_UP_TYPE")) == "RU":
                rpu.add(norm(row["POLICY_NUMBER"]))

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

    ridr = {}
    mstr = {}
    ridr_path = OUT / "quikridr.csv"
    mstr_path = OUT / "quikmstr.csv"
    if ridr_path.exists():
        with ridr_path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = (norm(row.get("MPOLICY")), norm(row.get("MPHASE")))
                ridr[key] = row
    if mstr_path.exists():
        with mstr_path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                mstr[norm(row.get("MPOLICY"))] = row

    change = []
    aligned = []
    ba = []
    missing_out = []
    for (pol, seq), brow in ben.items():
        if seq != "1":
            continue
        trow = typ.get((pol, seq), {})
        units = fnum(brow.get("NUMBER_OF_UNITS")) or 0.0
        vpu = fnum(brow.get("VALUE_PER_UNIT")) or 0.0
        db = fnum(trow.get("BF_CURRENT_DB")) or 0.0
        tcode = norm(trow.get("TYPE_CODE"))
        qk = qla_key(pol)
        out_row = ridr.get((qk, "1")) or ridr.get((qk, "01"))
        munit_now = fnum(out_row.get("MUNIT")) if out_row else None
        rec = {
            "policy": pol,
            "qla": qk,
            "type_code": tcode,
            "source_units": units,
            "vpu": vpu,
            "bf_current_db": db,
            "output_munit": munit_now,
            "output_msaveunit": norm(out_row.get("MSAVEUNIT")) if out_row else None,
            "output_mprem": norm(out_row.get("MPREM")) if out_row else None,
            "output_mplan": norm(out_row.get("MPLAN")) if out_row else None,
            "mstatus": norm(mstr.get(qk, {}).get("MSTATUS")),
            "mphstat": norm(out_row.get("MPHSTAT")) if out_row else None,
        }
        if tcode != "BF" or db <= 0 or not vpu:
            ba.append(rec)
            continue
        expected = db / vpu
        rec["proposed_munit"] = round(expected, 5)
        rec["delta"] = round(units - expected, 5)
        if abs(units - expected) <= EPS:
            aligned.append(rec)
        else:
            rec["would_change"] = munit_now is None or abs((munit_now or 0) - expected) > EPS
            change.append(rec)
            if out_row is None:
                missing_out.append(qk)

    change.sort(key=lambda r: abs(r.get("delta") or 0), reverse=True)
    summary = {
        "rpu_policies": len(rpu),
        "seq1_ba_or_no_dd": len(ba),
        "bf_aligned_no_change": len(aligned),
        "bf_unaligned_candidates": len(change),
        "output_ridr_present": ridr_path.exists(),
        "candidates_missing_output": missing_out,
        "candidates_mstatus": {},
        "proposed_munit_eq_dd_over_vpu": all(
            abs((r["proposed_munit"] * r["vpu"]) - r["bf_current_db"]) < 0.02 for r in change
        ),
        "aligned_output_already_matches": sum(
            1
            for r in aligned
            if r["output_munit"] is not None and abs(r["output_munit"] - r["source_units"]) <= EPS
        ),
        "unaligned_output_still_source_units": sum(
            1
            for r in change
            if r["output_munit"] is not None and abs(r["output_munit"] - r["source_units"]) <= EPS
        ),
        "msaveunit_blank_on_candidates": sum(1 for r in change if not r["output_msaveunit"]),
    }
    from collections import Counter

    summary["candidates_mstatus"] = Counter(r["mstatus"] for r in change).most_common()
    summary["ba_mstatus_sample"] = Counter(r["mstatus"] for r in ba).most_common()

    report = {"summary": summary, "candidates": change, "aligned_sample": aligned[:5]}
    outp = EVID / "issue143_risk_impact_summary.json"
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("wrote", outp)


if __name__ == "__main__":
    main()
