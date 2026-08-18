"""Independent Issue #143 Validation — source-derived, not Development candidate list.

Locked rule applied here from LifePRO extracts (20260630), then compared to
pre-#143 quikridr backup and current Output. No production code is imported
for candidate classification.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
CUT = "20260630"
EPS = 0.01
AMT_EPS = 0.02
GOLD = "9010757606C"
BASELINE = EVID / "quikridr_pre_issue143_20260818T130527Z.csv"
ISSUE55_TRACES = {
    ("9018495BC", "1"): 0.0,
    ("9018495BC", "2"): 0.53,
    ("9018499CC", "1"): 0.0,
    ("9018499CC", "2"): 1.05,
    ("9018510C", "1"): 0.0,
    ("9018510C", "2"): 0.647,
}


def fnum(v):
    s = str(v or "").replace(",", "").strip()
    if not s or s in ("-",):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm(v):
    return str(v or "").strip().upper()


def seq1(v):
    s = str(v or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    return (s.lstrip("0") or "0") == "1"


def src_path(stem):
    p = SRC / f"{stem}_Extract_{CUT}.csv"
    if not p.is_file():
        raise FileNotFoundError(p)
    return p


def read_rows(path, encoding="latin1"):
    with path.open(newline="", encoding=encoding, errors="replace") as fh:
        rows = []
        for row in csv.DictReader(fh):
            rows.append({str(k).strip().upper() if k else k: ("" if v is None else v) for k, v in row.items()})
        return rows


def qla_key(source_pol):
    p = norm(source_pol)
    if not p:
        return ""
    if p.endswith("C") and len(p) == 11:
        return p
    return p + "C" if not p.endswith("C") else p


def load_ridr(path):
    by = {}
    rows = []
    if not path.is_file():
        return by, rows
    for row in read_rows(path):
        key = (norm(row.get("MPOLICY")), norm(row.get("MPHASE")))
        by[key] = row
        rows.append(row)
    return by, rows


def classify(units, vpu, dd, type_code, is_rpu):
    if not is_rpu:
        return "other", None
    tc = norm(type_code)
    if tc == "BF" and (dd or 0) > 0 and (vpu or 0) > 0 and units is not None:
        expected = dd / vpu
        if abs(units - expected) > EPS:
            return "candidate", expected
        return "aligned_bf", expected
    return "ba", None


def main():
    errors = []
    observations = []

    rpu = {}
    for row in read_rows(src_path("PPOLC_PolicyMaster")):
        if norm(row.get("PAID_UP_TYPE")) == "RU":
            pol = norm(row.get("POLICY_NUMBER"))
            if pol:
                rpu[pol] = row

    typ = {}
    for row in read_rows(src_path("PPBENTYP_BenefitType")):
        pol = norm(row.get("POLICY_NUMBER"))
        if pol in rpu and seq1(row.get("BENEFIT_SEQ")):
            typ[pol] = row

    groups = {"candidate": [], "aligned_bf": [], "ba": []}
    for row in read_rows(src_path("PPBEN_PolicyBenefit")):
        pol = norm(row.get("POLICY_NUMBER"))
        if pol not in rpu or not seq1(row.get("BENEFIT_SEQ")):
            continue
        trow = typ.get(pol, {})
        units = fnum(row.get("NUMBER_OF_UNITS"))
        vpu = fnum(row.get("VALUE_PER_UNIT"))
        dd = fnum(trow.get("BF_CURRENT_DB"))
        kind, expected = classify(units, vpu, dd, trow.get("TYPE_CODE"), True)
        rec = {
            "policy": pol,
            "qla": qla_key(pol),
            "paid_up_type": norm(rpu[pol].get("PAID_UP_TYPE")),
            "type_code": norm(trow.get("TYPE_CODE")),
            "number_of_units": units,
            "bf_current_db": dd,
            "value_per_unit": vpu,
            "expected_munit": expected,
            "kind": kind,
        }
        if kind in groups:
            groups[kind].append(rec)

    post_by, post_rows = load_ridr(OUT / "quikridr.csv")
    pre_by, pre_rows = load_ridr(BASELINE)

    def ridr_get(store, qla):
        return store.get((qla, "1")) or store.get((qla, "01"))

    # Attach output / plan / diffs
    for kind, recs in groups.items():
        for rec in recs:
            post = ridr_get(post_by, rec["qla"])
            pre = ridr_get(pre_by, rec["qla"])
            rec["in_output"] = post is not None
            rec["in_baseline"] = pre is not None
            rec["plan"] = norm((post or pre or {}).get("MPLAN"))
            rec["actual_munit"] = fnum((post or {}).get("MUNIT"))
            rec["baseline_munit"] = fnum((pre or {}).get("MUNIT"))
            rec["actual_mvpu"] = fnum((post or {}).get("MVPU"))
            rec["actual_mprem"] = (post or {}).get("MPREM")
            rec["baseline_mprem"] = (pre or {}).get("MPREM")
            rec["actual_msaveunit"] = (post or {}).get("MSAVEUNIT")
            rec["baseline_msaveunit"] = (pre or {}).get("MSAVEUNIT")
            rec["actual_mpolicy"] = (post or {}).get("MPOLICY")
            if rec["expected_munit"] is not None and rec["actual_munit"] is not None:
                rec["munit_diff"] = rec["actual_munit"] - rec["expected_munit"]
            else:
                rec["munit_diff"] = None
            if rec["actual_munit"] is not None and rec["actual_mvpu"] is not None:
                rec["amount_ins"] = round(rec["actual_munit"] * rec["actual_mvpu"], 2)
            else:
                rec["amount_ins"] = None

    cand = groups["candidate"]
    aligned = groups["aligned_bf"]
    ba = groups["ba"]

    if len(rpu) != 304:
        observations.append(f"RPU source count {len(rpu)} (Risk used 304)")
    if len(cand) != 23:
        errors.append(f"independent candidates {len(cand)} != 23")
    if len(aligned) != 82:
        errors.append(f"independent aligned BF {len(aligned)} != 82")
    if len(ba) != 199:
        errors.append(f"independent BA {len(ba)} != 199")

    # 23-row remap
    cand_pass = 0
    unauthorized = []
    missing_corr = []
    db_fails = []
    for rec in cand:
        ok = (
            rec["in_output"]
            and rec["expected_munit"] is not None
            and rec["actual_munit"] is not None
            and abs(rec["actual_munit"] - rec["expected_munit"]) <= EPS
        )
        rec["remap_result"] = "PASS" if ok else "FAIL"
        if ok:
            cand_pass += 1
        else:
            missing_corr.append(rec["qla"])
        if rec["in_baseline"] and rec["baseline_munit"] is not None and rec["number_of_units"] is not None:
            if abs(rec["baseline_munit"] - rec["number_of_units"]) > EPS:
                observations.append(f"baseline already differed from source units: {rec['qla']}")
        if rec["amount_ins"] is not None and rec["bf_current_db"] is not None:
            if abs(rec["amount_ins"] - rec["bf_current_db"]) > AMT_EPS:
                db_fails.append((rec["qla"], rec["amount_ins"], rec["bf_current_db"]))
                rec["db_result"] = "FAIL"
            else:
                rec["db_result"] = "PASS"
        else:
            rec["db_result"] = "FAIL"

    # unauthorized: post MUNIT != baseline MUNIT on non-candidates
    for rec in aligned + ba:
        if rec["in_output"] and rec["in_baseline"]:
            if rec["actual_munit"] != rec["baseline_munit"]:
                unauthorized.append(rec["qla"])
        if rec["kind"] == "aligned_bf" and rec["in_output"] and rec["number_of_units"] is not None:
            rec["control_ok"] = (
                rec["actual_munit"] is not None
                and abs(rec["actual_munit"] - rec["number_of_units"]) <= EPS
            )
        if rec["kind"] == "ba" and rec["in_output"] and rec["number_of_units"] is not None:
            rec["control_ok"] = (
                rec["actual_munit"] is not None
                and abs(rec["actual_munit"] - rec["number_of_units"]) <= EPS
            )

    aligned_ok = sum(1 for r in aligned if r.get("control_ok"))
    ba_present = [r for r in ba if r["in_output"]]
    ba_absent = [r for r in ba if not r["in_output"]]
    ba_ok = sum(1 for r in ba_present if r.get("control_ok"))
    ba_absent_also_missing_baseline = sum(1 for r in ba_absent if not r["in_baseline"])

    # Field-level diff baseline vs post
    field_hits = Counter()
    changed_keys = []
    if len(pre_rows) != len(post_rows):
        errors.append(f"row count pre {len(pre_rows)} vs post {len(post_rows)}")
    for pre, post in zip(pre_rows, post_rows):
        diffs = [k for k in pre if pre.get(k) != post.get(k)]
        if diffs:
            changed_keys.append((norm(pre.get("MPOLICY")), norm(pre.get("MPHASE")), diffs))
            for k in diffs:
                field_hits[k] += 1
    if len(changed_keys) != 23:
        errors.append(f"field diff changed rows {len(changed_keys)} != 23")
    if set(field_hits) != {"MUNIT"}:
        errors.append(f"field hits {dict(field_hits)} — expected MUNIT only")
    changed_pols = {p for p, ph, _ in changed_keys if ph in ("1", "01")}
    cand_pols = {r["qla"] for r in cand}
    extra = changed_pols - cand_pols
    missing = cand_pols - changed_pols
    if extra:
        errors.append(f"unauthorized changed policies {sorted(extra)}")
        unauthorized.extend(sorted(extra))
    if missing:
        errors.append(f"candidates not in field-diff {sorted(missing)}")

    # Gold
    gold = next((r for r in cand if r["qla"] == GOLD), None)
    gold_post = ridr_get(post_by, GOLD) or {}
    gold_pre = ridr_get(pre_by, GOLD) or {}
    gold_ok = (
        gold is not None
        and gold["number_of_units"] == 25.0
        and gold["expected_munit"] is not None
        and abs(gold["expected_munit"] - 19.10196) < 1e-8
        and gold["actual_munit"] is not None
        and abs(gold["actual_munit"] - 19.10196) < 1e-6
        and abs((gold["actual_mvpu"] or 0) - 1000.0) <= 0.01
        and gold["amount_ins"] == 19101.96
        and str(gold_pre.get("MPREM", "")) == str(gold_post.get("MPREM", ""))
        and str(gold_pre.get("MVPU", "")) == str(gold_post.get("MVPU", ""))
        and str(gold_pre.get("MSAVEUNIT", "")).strip() == ""
        and str(gold_post.get("MSAVEUNIT", "")).strip() == ""
        and norm(gold_post.get("MPOLICY")) == GOLD
    )
    if not gold_ok:
        errors.append("gold trace failed")

    # #55 traces
    issue55 = []
    for (pol, ph), exp in ISSUE55_TRACES.items():
        row = post_by.get((pol, ph))
        actual = fnum((row or {}).get("MUNIT"))
        ok = row is not None and actual is not None and abs(actual - exp) <= 0.001
        issue55.append({"mpolicy": pol, "mphase": ph, "expected": exp, "actual": actual, "pass": ok})
        if not ok:
            errors.append(f"#55 trace {pol}/{ph} MUNIT={actual} expected {exp}")
    floor_hits = 0
    for row in post_rows:
        u = fnum(row.get("MUNIT"))
        if u is not None and 0 < u < 0.001:
            floor_hits += 1
    if floor_hits:
        errors.append(f"#55 floor broken: {floor_hits} rows with 0<MUNIT<0.001")

    # #108A: status-45 candidates must keep blank MSAVEUNIT
    mstr = {}
    mstr_path = OUT / "quikmstr.csv"
    if mstr_path.is_file():
        for row in read_rows(mstr_path):
            mstr[norm(row.get("MPOLICY"))] = norm(row.get("MSTATUS"))
    msave_ok = 0
    msave_fail = []
    for rec in cand:
        st = mstr.get(rec["qla"], "")
        rec["mstatus"] = st
        if st == "45":
            if str(rec.get("actual_msaveunit") or "").strip() == "":
                msave_ok += 1
            else:
                msave_fail.append(rec["qla"])
                errors.append(f"#108A {rec['qla']} MSAVEUNIT={rec.get('actual_msaveunit')!r}")

    # #124 expected MDB
    iswl = {}
    iswl_path = OUT / "QuikIswl.csv"
    if iswl_path.is_file():
        for row in read_rows(iswl_path, encoding="utf-8-sig"):
            iswl[norm(row.get("MPOLICY"))] = fnum(row.get("MDB"))
    i124 = []
    for rec in cand:
        expected_mdb = round((rec["expected_munit"] or 0) * 1000.0, 2)
        i124.append(
            {
                "mpolicy": rec["qla"],
                "plan": rec["plan"],
                "corrected_munit": rec["expected_munit"],
                "current_quikiswl_mdb": iswl.get(rec["qla"]),
                "expected_mdb_next_seed": expected_mdb,
            }
        )
    gold_mdb = next((x for x in i124 if x["mpolicy"] == GOLD), None)
    if not gold_mdb or abs(gold_mdb["expected_mdb_next_seed"] - 19101.96) > 0.02:
        errors.append("#124 gold expected MDB not 19101.96")

    # Version
    app_text = (ROOT / "app.py").read_text(encoding="utf-8", errors="replace")
    qla_app = (ROOT / "QLA_Migration" / "app.py").read_text(encoding="utf-8", errors="replace")
    version_ok = 'APP_VERSION = "v58.96"' in app_text and 'APP_VERSION = "v58.96"' in qla_app
    if not version_ok:
        errors.append("APP_VERSION is not v58.96 in both app.py files")

    # BA absence detail
    ba_absent_detail = []
    for rec in ba_absent:
        ba_absent_detail.append(
            {
                "source_policy": rec["policy"],
                "constructed_qla": rec["qla"],
                "in_baseline": rec["in_baseline"],
                "in_output": rec["in_output"],
                "preexisting_absence": (not rec["in_baseline"]) and (not rec["in_output"]),
            }
        )

    if ba_absent and not all(x["preexisting_absence"] for x in ba_absent_detail):
        errors.append("one or more absent BA rows were present in the pre-#143 baseline")
    elif ba_absent:
        observations.append(
            f"{len(ba_absent)} BA RPU source policies are absent from both pre-#143 "
            f"baseline and current Output (pre-existing / unrelated to #143)"
        )

    # Control traces from Risk
    for pol, exp in (("9010732975C", 14.08377), ("9010165095C", 1.69072)):
        row = ridr_get(post_by, pol)
        pre = ridr_get(pre_by, pol)
        actual = fnum((row or {}).get("MUNIT"))
        if row is None or actual is None or abs(actual - exp) > EPS:
            errors.append(f"control {pol} MUNIT={actual} expected {exp}")
        elif pre and fnum(pre.get("MUNIT")) != actual:
            errors.append(f"control {pol} MUNIT changed vs baseline")

    extra_traces = []
    for pol, exp in (("9010766847C", 5.16341), ("9010826422C", 9.65590)):
        rec = next((r for r in cand if r["qla"] == pol), None)
        extra_traces.append(
            {
                "mpolicy": pol,
                "expected": exp,
                "actual": rec["actual_munit"] if rec else None,
                "pass": rec is not None and rec["actual_munit"] is not None and abs(rec["actual_munit"] - exp) <= EPS,
            }
        )
        if not extra_traces[-1]["pass"]:
            errors.append(f"risk trace {pol} failed")

    verdict = "PASS" if not errors else "FAIL"
    summary = {
        "verdict": verdict,
        "source_cut": CUT,
        "rpu_policies": len(rpu),
        "independent_candidates": len(cand),
        "candidates_corrected": cand_pass,
        "missing_corrections": missing_corr,
        "unauthorized_corrections": unauthorized,
        "death_benefit_fails": db_fails,
        "aligned_bf": len(aligned),
        "aligned_bf_unchanged": aligned_ok,
        "ba_source": len(ba),
        "ba_present_unchanged": ba_ok,
        "ba_absent": len(ba_absent),
        "ba_absent_preexisting": ba_absent_also_missing_baseline,
        "gold_ok": gold_ok,
        "field_diff_changed_rows": len(changed_keys),
        "field_hits": dict(field_hits),
        "pre_rows": len(pre_rows),
        "post_rows": len(post_rows),
        "issue55_traces_pass": all(x["pass"] for x in issue55),
        "issue55_floor_violations": floor_hits,
        "issue108a_status45_blank_msave": msave_ok,
        "issue108a_fails": msave_fail,
        "version_ok": version_ok,
        "errors": errors,
        "observations": observations,
        "gold": {
            "policy": GOLD,
            "source_units": gold["number_of_units"] if gold else None,
            "bf_current_db": gold["bf_current_db"] if gold else None,
            "vpu": gold["value_per_unit"] if gold else None,
            "expected_munit": gold["expected_munit"] if gold else None,
            "baseline_munit": gold["baseline_munit"] if gold else None,
            "actual_munit": gold["actual_munit"] if gold else None,
            "amount_ins": gold["amount_ins"] if gold else None,
            "baseline_mprem": gold_pre.get("MPREM") if gold_pre else None,
            "actual_mprem": gold_post.get("MPREM") if gold_post else None,
            "baseline_mvpu": gold_pre.get("MVPU") if gold_pre else None,
            "actual_mvpu": gold_post.get("MVPU") if gold_post else None,
            "msaveunit": gold_post.get("MSAVEUNIT") if gold_post else None,
            "mpolicy": gold_post.get("MPOLICY") if gold_post else None,
            "plan": gold["plan"] if gold else None,
        },
        "risk_extra_traces": extra_traces,
        "issue55": issue55,
        "issue124": i124,
        "ba_absent_detail": ba_absent_detail,
    }

    EVID.mkdir(exist_ok=True)
    cand_csv = EVID / "issue143_independent_candidates.csv"
    with cand_csv.open("w", newline="", encoding="utf-8") as fh:
        fields = [
            "policy",
            "qla",
            "plan",
            "type_code",
            "paid_up_type",
            "number_of_units",
            "bf_current_db",
            "value_per_unit",
            "expected_munit",
            "actual_munit",
            "munit_diff",
            "amount_ins",
            "remap_result",
            "db_result",
        ]
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for rec in sorted(cand, key=lambda r: r["qla"]):
            w.writerow(rec)

    outp = EVID / "issue143_independent_validation.json"
    outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k not in ("issue124", "ba_absent_detail")}, indent=2))
    print("wrote", outp)
    print("wrote", cand_csv)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
