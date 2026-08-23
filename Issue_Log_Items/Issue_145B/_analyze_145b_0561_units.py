"""Issue 145B read-only reconciliation. Does not change conversion emit."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
EVID.mkdir(exist_ok=True)

GOLD = ("9010815236", "9011050114", "9011069610")
OUT_OF_SCOPE_146 = ("9010761639", "9010760840")


def open_csv(path: Path):
    return path.open(newline="", encoding="latin-1", errors="replace")


def npol(v: str) -> str:
    return re.sub(r"[^0-9]", "", (v or "").strip())


def ncode(v: str) -> str:
    digits = re.sub(r"[^0-9]", "", (v or "").strip())
    return str(int(digits)) if digits else (v or "").strip().upper()


def namt(v: str) -> float | None:
    s = (v or "").strip().replace(",", "")
    if not s or set(s.replace(".", "")) <= {"-", " "}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def ndate(v: str) -> str:
    d = re.sub(r"[^0-9]", "", (v or "").strip())
    return d[:8] if len(d) >= 8 else ""


def close(a, b, tol=0.02) -> bool:
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


def load_ppolc():
    billing = Counter()
    meta = {}
    vb = set()
    vanish_flag = Counter()
    with open_csv(SRC / "PPOLC_PolicyMaster_Extract_20260630.csv") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("POLICY_NUMBER", ""))
            if not pol:
                continue
            br = (row.get("BILLING_REASON") or "").strip().upper()
            billing[br or "(blank)"] += 1
            if br == "VB":
                vb.add(pol)
            meta[pol] = {
                "billing_reason": br,
                "billing_code": (row.get("BILLING_CODE") or "").strip(),
                "billing_mode": (row.get("BILLING_MODE") or "").strip(),
                "contract_code": (row.get("CONTRACT_CODE") or "").strip(),
                "mode_prem": namt(row.get("MODE_PREMIUM", "")),
                "ann_prem": namt(row.get("ANNUAL_PREMIUM", "")),
                "paid_to": ndate(row.get("PAID_TO_DATE", "")),
                "issue_date": ndate(row.get("ISSUE_DATE", "")),
                "group": (row.get("GROUP_NUMBER") or "").strip(),
            }
    return vb, meta, dict(billing)


def load_ppben():
    rows = defaultdict(list)
    with open_csv(SRC / "PPBEN_PolicyBenefit_Extract_20260630.csv") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("POLICY_NUMBER", ""))
            if not pol:
                continue
            rec = {
                "seq": (row.get("BENEFIT_SEQ") or "").strip(),
                "type": (row.get("BENEFIT_TYPE") or "").strip().upper(),
                "status": (row.get("STATUS_CODE") or "").strip(),
                "plan": (row.get("PLAN_CODE") or "").strip(),
                "units": namt(row.get("NUMBER_OF_UNITS", "")),
                "vpu": namt(row.get("VALUE_PER_UNIT", "")),
                "mode_prem": namt(row.get("MODE_PREMIUM", "")),
            }
            rows[pol].append(rec)
    return rows


def load_ppbentyp():
    typ = {}
    vanish_flag = Counter()
    orig_nonzero = 0
    with open_csv(SRC / "PPBENTYP_BenefitType_Extract_20260630.csv") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("POLICY_NUMBER", ""))
            seq = (row.get("BENEFIT_SEQ") or "").strip()
            tcode = (row.get("TYPE_CODE") or "").strip().upper()
            vf = (row.get("BA_OR_VANISH_FLAG") or "").strip()
            vanish_flag[vf or "(blank)"] += 1
            orig = namt(row.get("ORIGINAL_UNITS", ""))
            if orig and abs(orig) > 0.00001:
                orig_nonzero += 1
            if not pol:
                continue
            if tcode not in {"BA", "BF"} and seq not in {"1", "01", "001"}:
                continue
            key = (pol, tcode or seq)
            typ[key] = {
                "type_code": tcode,
                "seq": seq,
                "original_units": orig,
                "ba_or_vanish_flag": vf,
                "bf_current_db": namt(row.get("BF_CURRENT_DB", "")),
            }
    return typ, dict(vanish_flag), orig_nonzero


def base_benefit(ppben_rows):
    for pref in ("BA", "BF"):
        for r in ppben_rows:
            if r["type"] == pref and r.get("units") is not None:
                return r
    for r in ppben_rows:
        if r["seq"] in {"1", "01", "001"}:
            return r
    return ppben_rows[0] if ppben_rows else None


def load_pactg_561():
    rows = []
    with open_csv(SRC / "PACTG_Accounting_Extract20260630.csv") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [((h or "").strip()) for h in (reader.fieldnames or [])]
        for raw in reader:
            row = {(k or "").strip(): v for k, v in raw.items()}
            if ncode(row.get("DEBIT_CODE", "")) != "561":
                continue
            rec = {
                "policy": npol(row.get("POLICY_NUMBER", "")),
                "debit": "561",
                "credit": ncode(row.get("CREDIT_CODE", "")),
                "eff": ndate(row.get("EFFECTIVE_DATE", "")),
                "added": ndate(row.get("DATE_ADDED", "")),
                "amt": namt(row.get("TRANS_AMOUNT", "")),
                "reversal": (row.get("REVERSAL_CODE") or "").strip().upper(),
                "date_reversed": ndate(row.get("DATE_REVERSED", "")),
                "control": (row.get("CONTROL_NUMBER") or "").strip(),
                "record_seq": (row.get("RECORD_SEQUENCE") or "").strip(),
                "benefit_seq": (row.get("BENEFIT_SEQ") or "").strip(),
                "plan": (row.get("PLAN_CODE") or "").strip(),
                "coder": (row.get("CODER_ADDED") or "").strip(),
            }
            rows.append(rec)
    return rows


def load_isrr():
    by = defaultdict(list)
    path = OUT / "QuikIsrr.csv"
    with open_csv(path) as f:
        for row in csv.DictReader(f):
            mp = (row.get("MPOLICY") or "").strip()
            pol = npol(mp)
            by[pol].append({
                "mpolicy": mp,
                "date": ndate(row.get("MSURRDATE", "")),
                "amt": namt(row.get("MSURRAMT", "")),
            })
    return by


def load_qla_units():
    ridr = {}
    with open_csv(OUT / "quikridr.csv") as f:
        for row in csv.DictReader(f):
            if (row.get("MPHASE") or "").strip() not in {"1", "01"}:
                continue
            pol = npol(row.get("MPOLICY", ""))
            ridr[pol] = {
                "mpolicy": (row.get("MPOLICY") or "").strip(),
                "mplan": (row.get("MPLAN") or "").strip(),
                "munit": namt(row.get("MUNIT", "")),
                "mvpu": namt(row.get("MVPU", "")),
                "mprem": namt(row.get("MPREM", "")),
                "mphstat": (row.get("MPHSTAT") or "").strip(),
            }
    iswl = {}
    with open_csv(OUT / "QuikIswl.csv") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("MPOLICY", ""))
            rec = {
                "mdb": namt(row.get("MDB", "")),
                "mcashval": namt(row.get("MCASHVAL", "")),
                "mmonth": (row.get("MMONTH") or "").strip(),
                "mlastannv": ndate(row.get("MLASTANNV", "")),
            }
            prev = iswl.get(pol)
            if prev is None or rec["mmonth"] in {"0", "00", ""}:
                iswl[pol] = rec
    spec = {}
    with open_csv(OUT / "quikspec.csv") as f:
        for row in csv.DictReader(f):
            pol = npol(row.get("MPOLICY", ""))
            spec[pol] = {
                "vanish": (row.get("VANISH") or "").strip().upper(),
                "vanishdt": (row.get("VANISHDT") or "").strip(),
            }
    return ridr, iswl, spec


def match_isrr(src_rows, isrr_rows):
    used = set()
    traces = []
    for s in src_rows:
        hit = None
        for i, t in enumerate(isrr_rows):
            if i in used:
                continue
            if s["eff"] == t["date"] and close(s["amt"], t["amt"]):
                hit = (i, t, "Exact Match")
                break
        if hit is None:
            for i, t in enumerate(isrr_rows):
                if i in used:
                    continue
                if close(s["amt"], t["amt"]):
                    hit = (i, t, "Transformed Match")
                    break
        if hit:
            used.add(hit[0])
            traces.append({"source": s, "isrr": hit[1], "status": hit[2]})
        else:
            traces.append({"source": s, "isrr": None, "status": "No QuikIsrr Match"})
    extras = [t for i, t in enumerate(isrr_rows) if i not in used]
    return traces, extras


def main():
    vb, ppolc, billing = load_ppolc()
    ppben = load_ppben()
    typ, vanish_flag_dist, orig_nonzero = load_ppbentyp()
    pactg = load_pactg_561()
    isrr = load_isrr()
    ridr, iswl, spec = load_qla_units()

    unrev = [r for r in pactg if r["reversal"] != "Y"]
    rev = [r for r in pactg if r["reversal"] == "Y"]

    vb_unrev = [r for r in unrev if r["policy"] in vb]
    vb_rev = [r for r in rev if r["policy"] in vb]
    nonvb_unrev = [r for r in unrev if r["policy"] not in vb]

    vb_with_unrev = {r["policy"] for r in vb_unrev}
    vb_with_isrr = {p for p in vb if isrr.get(p)}

    pop_rows = []
    reconcile_yes = 0
    reconcile_no = 0
    missing = 0
    units_already_reduced = 0
    emit_mismatch = 0

    for pol in sorted(vb):
        ben = base_benefit(ppben.get(pol, []))
        q = ridr.get(pol, {})
        iw = iswl.get(pol, {})
        evs = [r for r in vb_unrev if r["policy"] == pol]
        sum_amt = round(sum(r["amt"] or 0 for r in evs), 2)
        units = ben["units"] if ben else None
        vpu = (ben["vpu"] if ben and ben["vpu"] else None) or q.get("mvpu") or 1000.0
        if not vpu:
            vpu = 1000.0
        impact = round(sum_amt / vpu, 5) if evs else 0.0
        expected_if_applied = round(units - impact, 5) if units is not None else None
        munit = q.get("munit")
        mdb = iw.get("mdb")
        expected_mdb = round(units * vpu, 2) if units is not None else None
        # Conversion Output should still hold LifePRO units (reduction is post-load).
        output_holds_lp = close(units, munit, 0.0001) if units is not None and munit is not None else None
        if output_holds_lp is False:
            units_already_reduced += 1
        traces, extras = match_isrr(evs, isrr.get(pol, []))
        exact = sum(1 for t in traces if t["status"] == "Exact Match")
        if evs and exact != len(evs):
            emit_mismatch += 1
        pop_rows.append({
            "policy": pol,
            "billing_reason": "VB",
            "lp_units": units,
            "lp_vpu": vpu,
            "qla_munit": munit,
            "qla_mdb": mdb,
            "expected_mdb_from_lp": expected_mdb,
            "n_0561_unrev": len(evs),
            "sum_0561": sum_amt,
            "unit_impact_0561": impact,
            "counterfactual_qla_units": expected_if_applied,
            "output_munit_equals_lp": output_holds_lp,
            "isrr_exact_matches": exact,
            "isrr_rows": len(isrr.get(pol, [])),
            "vanish_flag": spec.get(pol, {}).get("vanish"),
        })

    gold = {}
    for pol in GOLD:
        ben = base_benefit(ppben.get(pol, []))
        typ_ba = typ.get((pol, "BA")) or typ.get((pol, "BF"))
        evs_all = [r for r in pactg if r["policy"] == pol]
        evs_u = [r for r in evs_all if r["reversal"] != "Y"]
        evs_r = [r for r in evs_all if r["reversal"] == "Y"]
        traces, extras = match_isrr(evs_u, isrr.get(pol, []))
        units = ben["units"] if ben else None
        vpu = (ben["vpu"] if ben and ben["vpu"] else 1000.0) or 1000.0
        sum_amt = round(sum(r["amt"] or 0 for r in evs_u), 2)
        impact = round(sum_amt / vpu, 5)
        q = ridr.get(pol, {})
        gold[pol] = {
            "is_vb": pol in vb,
            "ppolc": ppolc.get(pol),
            "ppben_base": ben,
            "ppbentyp": typ_ba,
            "qla_ridr": q,
            "qla_iswl": iswl.get(pol),
            "qla_spec": spec.get(pol),
            "pactg_unreversed": evs_u,
            "pactg_reversed": evs_r,
            "isrr": isrr.get(pol, []),
            "traces": traces,
            "isrr_unmatched": extras,
            "sum_0561": sum_amt,
            "vpu": vpu,
            "unit_impact": impact,
            "lp_units": units,
            "qla_output_munit": q.get("munit"),
            "counterfactual_after_anniv": round(units - impact, 5) if units is not None else None,
            "output_equals_lp": close(units, q.get("munit"), 0.0001),
            "hypothesis": (
                "QLA Output MUNIT still equals LifePRO units. "
                "If anniversary subtracts 0561 dollars from face (units*VPU), "
                "resulting units = LP units - sum(0561)/VPU."
            ),
        }

    summary = {
        "cut": "20260630",
        "vb_identification": {
            "source": "PPOLC_PolicyMaster_Extract_20260630.csv",
            "field": "BILLING_REASON",
            "code": "VB",
            "interpretation": "On vanish / vanish billing. Locked by Issue 145. Not 'eligible to vanish'.",
            "policy_count": len(vb),
            "billing_reason_distribution": billing,
            "ba_or_vanish_flag_distribution": vanish_flag_dist,
            "ba_or_vanish_usable": vanish_flag_dist.get("(blank)", 0) == sum(vanish_flag_dist.values()),
            "original_units_nonzero_rows": orig_nonzero,
        },
        "pactg_0561": {
            "all_561": len(pactg),
            "unreversed": len(unrev),
            "reversed": len(rev),
            "vb_unreversed_rows": len(vb_unrev),
            "vb_reversed_rows": len(vb_rev),
            "vb_policies_with_unreversed": len(vb_with_unrev),
            "vb_without_0561": len(vb - vb_with_unrev),
            "non_vb_unreversed_rows": len(nonvb_unrev),
            "non_vb_unreversed_policies": len({r["policy"] for r in nonvb_unrev}),
            "note_146": "non-VB 0561 population is Issue 146 — out of scope for 145B",
        },
        "quikisrr": {
            "output_rows": sum(len(v) for v in isrr.values()),
            "output_policies": len(isrr),
            "vb_policies_with_isrr": len(vb_with_isrr),
            "vb_isrr_rows": sum(len(isrr[p]) for p in vb_with_isrr),
        },
        "gold": gold,
        "population": {
            "vb_policies": len(vb),
            "output_munit_already_differs_from_lp": units_already_reduced,
            "vb_with_unrev_emit_not_exact": emit_mismatch,
        },
        "out_of_scope_146_examples": {},
    }

    for pol in OUT_OF_SCOPE_146:
        evs = [r for r in unrev if r["policy"] == pol]
        ben = base_benefit(ppben.get(pol, []))
        summary["out_of_scope_146_examples"][pol] = {
            "is_vb": pol in vb,
            "billing_reason": ppolc.get(pol, {}).get("billing_reason"),
            "lp_units": ben["units"] if ben else None,
            "n_0561": len(evs),
            "sum_0561": round(sum(r["amt"] or 0 for r in evs), 2),
            "scope": "Issue 146 — not analyzed as 145B candidates",
        }

    # compact population CSV
    csv_path = EVID / "issue145b_vb_population_recon.csv"
    fields = [
        "policy", "billing_reason", "lp_units", "lp_vpu", "qla_munit", "qla_mdb",
        "n_0561_unrev", "sum_0561", "unit_impact_0561", "counterfactual_qla_units",
        "output_munit_equals_lp", "isrr_exact_matches", "isrr_rows", "vanish_flag",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in pop_rows:
            w.writerow(r)

    gold_csv = EVID / "issue145b_gold_pactg_isrr_trace.csv"
    with gold_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "policy", "reversal", "eff", "added", "amt", "credit", "control",
                "isrr_date", "isrr_amt", "match_status",
            ],
        )
        w.writeheader()
        for pol in GOLD:
            for t in gold[pol]["traces"]:
                s = t["source"]
                i = t["isrr"] or {}
                w.writerow({
                    "policy": pol,
                    "reversal": s["reversal"],
                    "eff": s["eff"],
                    "added": s["added"],
                    "amt": s["amt"],
                    "credit": s["credit"],
                    "control": s["control"],
                    "isrr_date": i.get("date"),
                    "isrr_amt": i.get("amt"),
                    "match_status": t["status"],
                })
            for s in gold[pol]["pactg_reversed"]:
                w.writerow({
                    "policy": pol,
                    "reversal": "Y",
                    "eff": s["eff"],
                    "added": s["added"],
                    "amt": s["amt"],
                    "credit": s["credit"],
                    "control": s["control"],
                    "isrr_date": "",
                    "isrr_amt": "",
                    "match_status": "Reversed — excluded from emit by Issue 34",
                })

    out_json = EVID / "issue145b_analysis_summary.json"
    # gold traces contain nested source dicts — fine
    slim = {k: v for k, v in summary.items() if k != "gold"}
    slim["gold_keys"] = list(gold)
    # write full gold separately to keep json usable
    (EVID / "issue145b_gold_detail.json").write_text(
        json.dumps(gold, indent=2, default=str), encoding="utf-8"
    )
    out_json.write_text(json.dumps(slim, indent=2, default=str), encoding="utf-8")

    print(json.dumps(slim, indent=2, default=str))
    print("\n=== GOLD SNAPSHOT ===")
    for pol, g in gold.items():
        print(pol, {
            "vb": g["is_vb"],
            "lp_units": g["lp_units"],
            "vpu": g["vpu"],
            "orig_units": (g["ppbentyp"] or {}).get("original_units"),
            "munit": g["qla_output_munit"],
            "mdb": (g["qla_iswl"] or {}).get("mdb"),
            "n_unrev": len(g["pactg_unreversed"]),
            "n_rev": len(g["pactg_reversed"]),
            "sum_0561": g["sum_0561"],
            "impact": g["unit_impact"],
            "counterfactual": g["counterfactual_after_anniv"],
            "isrr": len(g["isrr"]),
            "exact": sum(1 for t in g["traces"] if t["status"] == "Exact Match"),
            "vanish": (g["qla_spec"] or {}).get("vanish"),
        })


if __name__ == "__main__":
    main()
