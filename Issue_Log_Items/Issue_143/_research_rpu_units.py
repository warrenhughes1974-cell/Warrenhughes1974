"""Read-only Issue #143 research: RPU units vs ORIGINAL_UNITS vs BF_CURRENT_DB."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Source")
OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(exist_ok=True)


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


def load_rpu_pols(ppolc_path):
    rpu = {}
    put_ct = Counter()
    with ppolc_path.open(newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            put = norm(row.get("PAID_UP_TYPE"))
            put_ct[put] += 1
            if put == "RU":
                rpu[norm(row["POLICY_NUMBER"])] = {
                    "PUT": put,
                    "CONTRACT_CODE": norm(row.get("CONTRACT_CODE")),
                    "CONTRACT_REASON": norm(row.get("CONTRACT_REASON")),
                }
    return rpu, put_ct


def load_ppben(path, rpu_pols):
    rows = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pol = norm(row.get("POLICY_NUMBER"))
            if pol not in rpu_pols:
                continue
            units = fnum(row.get("NUMBER_OF_UNITS"))
            vpu = fnum(row.get("VALUE_PER_UNIT"))
            rows.append(
                {
                    "pol": pol,
                    "seq": norm(row.get("BENEFIT_SEQ")),
                    "btype": norm(row.get("BENEFIT_TYPE")),
                    "status": norm(row.get("STATUS_CODE")),
                    "reason": norm(row.get("STATUS_REASON")),
                    "plan": norm(row.get("PLAN_CODE")),
                    "units": units,
                    "vpu": vpu,
                    "face": (units or 0.0) * (vpu or 0.0),
                    "nar": fnum(row.get("UV_CURRENT_NAR")),
                    "fv2": fnum(row.get("FV_BALANCE2")),
                }
            )
    return rows


def load_typ(path, rpu_pols):
    typ = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pol = norm(row.get("POLICY_NUMBER"))
            if pol not in rpu_pols:
                continue
            seq = str(int(float(norm(row.get("BENEFIT_SEQ") or "0") or 0)))
            typ[(pol, seq)] = {
                "type_code": norm(row.get("TYPE_CODE")),
                "orig_units": fnum(row.get("ORIGINAL_UNITS")),
                "eti_rpu_endow": fnum(row.get("ETI_RPU_ENDOWMENT")),
                "eti_rpu_pat": norm(row.get("ETI_RPU_PATTERN")),
                "nfo": norm(row.get("NON_FORFEITURE")),
                "bf_nfo": norm(row.get("BF_NON_FORFEITURE")),
                "bf_spec": fnum(row.get("BF_SPECIFIED_AMT")),
                "bf_db": fnum(row.get("BF_CURRENT_DB")),
                "bf_opt": norm(row.get("BF_DB_OPTION")),
                "or_pua": fnum(row.get("OR_PUA_FACE")),
            }
    return typ


def seq_key(seq):
    try:
        return str(int(float(seq or "0")))
    except ValueError:
        return seq


def main():
    ppolc = SRC / "PPOLC_PolicyMaster_Extract_20260630.csv"
    ppben_p = SRC / "PPBEN_PolicyBenefit_Extract_20260630.csv"
    typ_p = SRC / "PPBENTYP_BenefitType_Extract_20260630.csv"

    rpu_pols, put_ct = load_rpu_pols(ppolc)
    ppben = load_ppben(ppben_p, rpu_pols)
    typ = load_typ(typ_p, rpu_pols)

    seq1 = [r for r in ppben if seq_key(r["seq"]) == "1"]

    summary = {
        "put_counts": put_ct.most_common(25),
        "rpu_policy_count": len(rpu_pols),
        "ppben_rpu_rows": len(ppben),
        "ppben_status": Counter(r["status"] for r in ppben).most_common(),
        "ppben_reason": Counter(r["reason"] for r in ppben).most_common(),
        "ppben_btype": Counter(r["btype"] for r in ppben).most_common(),
        "typ_rows": len(typ),
        "typ_type_code": Counter(v["type_code"] for v in typ.values()).most_common(),
        "typ_bf_opt": Counter(v["bf_opt"] for v in typ.values()).most_common(),
        "typ_pattern": Counter(v["eti_rpu_pat"] for v in typ.values()).most_common(),
        "orig_units_nonzero": sum(1 for v in typ.values() if (v["orig_units"] or 0) > 0),
        "bf_db_nonzero": sum(1 for v in typ.values() if (v["bf_db"] or 0) > 0),
        "bf_spec_nonzero": sum(1 for v in typ.values() if (v["bf_spec"] or 0) > 0),
        "endow_nonzero": sum(1 for v in typ.values() if (v["eti_rpu_endow"] or 0) > 0),
        "seq1_count": len(seq1),
    }

    reduced = []
    same = []
    orig_zero = []
    missing = []
    face_vs_db = []

    for r in seq1:
        t = typ.get((r["pol"], seq_key(r["seq"])))
        if not t:
            missing.append(r)
            continue
        ou = t["orig_units"] or 0.0
        cu = r["units"] or 0.0
        rec = {"ppben": r, "typ": t}
        if ou == 0:
            orig_zero.append(rec)
        elif abs(cu - ou) > 1e-6:
            reduced.append(rec)
        else:
            same.append(rec)
        if (t["bf_db"] or 0) > 0:
            face_vs_db.append(rec)

    summary["seq1_units_vs_orig"] = {
        "reduced": len(reduced),
        "same": len(same),
        "orig_zero": len(orig_zero),
        "missing_typ": len(missing),
    }

    def pack(rec):
        r, t = rec["ppben"], rec["typ"]
        return {
            "policy": r["pol"],
            "plan": r["plan"],
            "btype": r["btype"],
            "type_code": t["type_code"],
            "status": r["status"],
            "reason": r["reason"],
            "units": r["units"],
            "orig_units": t["orig_units"],
            "vpu": r["vpu"],
            "face": round(r["face"], 2),
            "bf_current_db": t["bf_db"],
            "bf_specified_amt": t["bf_spec"],
            "bf_db_option": t["bf_opt"],
            "eti_rpu_endow": t["eti_rpu_endow"],
            "eti_rpu_pattern": t["eti_rpu_pat"],
            "nfo": t["nfo"],
            "bf_nfo": t["bf_nfo"],
            "units_x_vpu_minus_bf_db": round((r["face"] or 0) - (t["bf_db"] or 0), 2)
            if t["bf_db"]
            else None,
            "implied_units_from_bf_db": round((t["bf_db"] or 0) / (r["vpu"] or 1), 5)
            if (t["bf_db"] and r["vpu"])
            else None,
        }

    tiny = [r for r in seq1 if r["units"] is not None and 0 < r["units"] < 0.001]
    zero = [r for r in seq1 if (r["units"] or 0) == 0]
    normal = [r for r in seq1 if (r["units"] or 0) >= 0.001]
    summary["seq1_unit_buckets"] = {
        "tiny_gt0_lt_0.001": len(tiny),
        "zero": len(zero),
        "normal_ge_0.001": len(normal),
    }

    tiny_zero_pols = {r["pol"] for r in tiny + zero}
    later = [r for r in ppben if r["pol"] in tiny_zero_pols and seq_key(r["seq"]) != "1"]
    summary["later_on_tiny_zero_base"] = {
        "rows": len(later),
        "btype": Counter(r["btype"] for r in later).most_common(),
        "units_gt0": sum(1 for r in later if (r["units"] or 0) > 0),
    }

    # Face vs BF_CURRENT_DB
    close = far = ba_db = bf_db = 0
    far_examples = []
    close_examples = []
    for rec in face_vs_db:
        r, t = rec["ppben"], rec["typ"]
        if t["type_code"] == "BF":
            bf_db += 1
        else:
            ba_db += 1
        delta = abs((r["face"] or 0) - (t["bf_db"] or 0))
        if delta <= 1.0:
            close += 1
            if len(close_examples) < 10:
                close_examples.append(pack(rec))
        else:
            far += 1
            if len(far_examples) < 15:
                far_examples.append(pack(rec))
    summary["face_vs_bf_current_db"] = {
        "rows_with_bf_db_gt0": len(face_vs_db),
        "close_le_1": close,
        "far": far,
        "type_BA_or_other": ba_db,
        "type_BF": bf_db,
    }

    # All BF RPU seq1 whether or not orig units populated
    bf_seq1 = []
    for r in seq1:
        t = typ.get((r["pol"], seq_key(r["seq"])))
        if t and t["type_code"] == "BF":
            bf_seq1.append({"ppben": r, "typ": t})
    summary["seq1_BF_count"] = len(bf_seq1)

    # Implied units from BF_CURRENT_DB vs actual units on BF
    bf_match = bf_mismatch = 0
    bf_examples = []
    for rec in bf_seq1:
        r, t = rec["ppben"], rec["typ"]
        if not t["bf_db"] or not r["vpu"]:
            continue
        implied = (t["bf_db"] or 0) / (r["vpu"] or 1)
        if abs(implied - (r["units"] or 0)) <= 0.01:
            bf_match += 1
        else:
            bf_mismatch += 1
        if len(bf_examples) < 20:
            bf_examples.append(pack(rec))
    summary["bf_implied_units_vs_actual"] = {"match_le_0.01": bf_match, "mismatch": bf_mismatch}

    # BA seq1 face vs units*1000 sanity and orig
    ba_seq1 = []
    for r in seq1:
        t = typ.get((r["pol"], seq_key(r["seq"])))
        if t and t["type_code"] == "BA":
            ba_seq1.append({"ppben": r, "typ": t})
    summary["seq1_BA_count"] = len(ba_seq1)

    # Also check ALL RPU policies TYPE_CODE mix at seq1
    type_by_pol = Counter()
    for r in seq1:
        t = typ.get((r["pol"], seq_key(r["seq"])))
        type_by_pol[(t or {}).get("type_code", "MISSING")] += 1
    summary["seq1_type_code"] = type_by_pol.most_common()

    # Sample later-phase face on tiny-base RPU
    later_examples = []
    by = defaultdict(list)
    for r in later:
        by[r["pol"]].append(r)
    for i, (pol, rows) in enumerate(by.items()):
        if i >= 8:
            break
        t = typ.get((pol, "1"))
        later_examples.append(
            {
                "policy": pol,
                "seq1_units": next((x["units"] for x in seq1 if x["pol"] == pol), None),
                "seq1_type": (t or {}).get("type_code"),
                "later": [
                    {
                        "seq": x["seq"],
                        "btype": x["btype"],
                        "units": x["units"],
                        "face": round(x["face"], 2),
                        "status": x["status"],
                        "plan": x["plan"],
                    }
                    for x in rows
                ],
            }
        )

    report = {
        "summary": summary,
        "examples_units_reduced_vs_orig": [pack(x) for x in reduced[:15]],
        "examples_units_same_as_orig": [pack(x) for x in same[:15]],
        "examples_orig_zero": [pack(x) for x in orig_zero[:15]],
        "examples_bf_seq1": bf_examples,
        "examples_face_close_to_bf_db": close_examples,
        "examples_face_far_from_bf_db": far_examples,
        "examples_tiny_base_later_phases": later_examples,
    }

    out_json = OUT / "issue143_rpu_units_research.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("wrote", out_json)


if __name__ == "__main__":
    main()
