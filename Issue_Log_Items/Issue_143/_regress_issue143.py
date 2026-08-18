"""Formal Issue #143 regression compare — no production code changes."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parent / "evidence"
BASE = EVID / "quikridr_pre_issue143_20260818T130527Z.csv"
CAND_CSV = EVID / "issue143_independent_candidates.csv"
GOLD = "9010757606C"
EPS = 0.01


def fnum(v):
    s = str(v or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_ridr(path):
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = []
        by = {}
        for row in reader:
            clean = {str(k).strip().upper() if k else k: ("" if v is None else v) for k, v in row.items()}
            key = (str(clean.get("MPOLICY", "")).strip(), str(clean.get("MPHASE", "")).strip())
            by[key] = clean
            rows.append(clean)
        return fields, rows, by


def table_rowcount(path):
    if not path.is_file():
        return None
    with path.open(newline="", encoding="latin1", errors="replace") as fh:
        n = sum(1 for _ in fh)
    return max(n - 1, 0)


def main():
    errors = []
    classifications = []

    pre_fields, pre_rows, pre_by = load_ridr(BASE)
    post_fields, post_rows, post_by = load_ridr(OUT / "quikridr.csv")

    candidates = set()
    if CAND_CSV.is_file():
        with CAND_CSV.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                candidates.add(str(row.get("qla") or "").strip())

    rowcount = {
        "pre": len(pre_rows),
        "post": len(post_rows),
        "fields_same": pre_fields == post_fields,
        "field_count": len(post_fields),
        "keys_same": set(pre_by) == set(post_by),
    }
    if rowcount["pre"] != 6934 or rowcount["post"] != 6934:
        errors.append(f"quikridr row count {rowcount}")
    if not rowcount["fields_same"]:
        errors.append("quikridr field order/name changed")
    if not rowcount["keys_same"]:
        errors.append("quikridr MPOLICY+MPHASE key set changed")

    field_hits = Counter()
    changed = []
    for pre, post in zip(pre_rows, post_rows):
        diffs = [k for k in pre_fields if pre.get(k) != post.get(k)]
        if not diffs:
            continue
        pol = str(pre.get("MPOLICY", "")).strip()
        ph = str(pre.get("MPHASE", "")).strip()
        changed.append({"mpolicy": pol, "mphase": ph, "fields": diffs})
        for k in diffs:
            field_hits[k] += 1
        if diffs == ["MUNIT"] and pol in candidates and ph in ("1", "01"):
            classifications.append(
                {
                    "table": "quikridr",
                    "mpolicy": pol,
                    "field": "MUNIT",
                    "class": "EXPECTED ISSUE #143",
                    "before": pre.get("MUNIT"),
                    "after": post.get("MUNIT"),
                }
            )
        else:
            classifications.append(
                {
                    "table": "quikridr",
                    "mpolicy": pol,
                    "field": ",".join(diffs),
                    "class": "UNEXPECTED REGRESSION",
                    "before": {k: pre.get(k) for k in diffs},
                    "after": {k: post.get(k) for k in diffs},
                }
            )
            errors.append(f"unexpected ridr diff {pol}/{ph} {diffs}")

    if len(changed) != 23:
        errors.append(f"changed rows {len(changed)} != 23")
    if set(field_hits) != {"MUNIT"}:
        errors.append(f"field hits {dict(field_hits)}")

    # Containment
    non_cand_changed = [c for c in changed if c["mpolicy"] not in candidates]
    if non_cand_changed:
        errors.append(f"non-candidate ridr changes {non_cand_changed}")

    # Protected fields on the 23
    protected_ok = True
    for rec in changed:
        pre = pre_by[(rec["mpolicy"], rec["mphase"])]
        post = post_by[(rec["mpolicy"], rec["mphase"])]
        for fld in ("MPREM", "MVPU", "MSAVEUNIT", "MPOLICY", "MPLAN", "MPHASE"):
            if pre.get(fld) != post.get(fld):
                protected_ok = False
                errors.append(f"protected {fld} changed on {rec['mpolicy']}")

    gold_pre = pre_by.get((GOLD, "1"), {})
    gold_post = post_by.get((GOLD, "1"), {})
    gold_ok = (
        gold_pre.get("MUNIT") == "25.00000"
        and gold_post.get("MUNIT") == "19.10196"
        and gold_post.get("MVPU") == "1000.00"
        and abs((fnum(gold_post.get("MUNIT")) or 0) * (fnum(gold_post.get("MVPU")) or 0) - 19101.96) <= 0.02
        and gold_pre.get("MPREM") == gold_post.get("MPREM")
        and str(gold_post.get("MSAVEUNIT") or "").strip() == ""
    )
    if not gold_ok:
        errors.append("gold regression failed")

    # #108A: all 23 MSAVEUNIT identical to baseline
    msave_changed = 0
    for rec in changed:
        if pre_by[(rec["mpolicy"], rec["mphase"])].get("MSAVEUNIT") != post_by[(rec["mpolicy"], rec["mphase"])].get(
            "MSAVEUNIT"
        ):
            msave_changed += 1
    if msave_changed:
        errors.append(f"#108A MSAVEUNIT changed on {msave_changed} candidate rows")

    # Other Output tables — row counts + schema; no #143 baseline except ridr
    other_tables = []
    for path in sorted(OUT.glob("quik*.csv")) + sorted(OUT.glob("Quik*.csv")):
        if path.name.lower() == "quikridr.csv":
            continue
        other_tables.append(
            {
                "table": path.name,
                "rows": table_rowcount(path),
                "mtime": path.stat().st_mtime,
            }
        )

    # QuikIswl downstream
    iswl_path = OUT / "QuikIswl.csv"
    i124 = []
    stored_vs_current_munit = 0
    stored_vs_expected_future = 0
    if iswl_path.is_file():
        iswl = {}
        with iswl_path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            for row in csv.DictReader(fh):
                iswl[str(row.get("MPOLICY") or "").strip()] = fnum(row.get("MDB"))
        for rec in changed:
            pol = rec["mpolicy"]
            post = post_by[(pol, rec["mphase"])]
            munit = fnum(post.get("MUNIT"))
            expected_future = round((munit or 0) * 1000.0, 2)
            stored = iswl.get(pol)
            if stored is not None and munit is not None and abs(stored - munit * 1000.0) > 0.011:
                stored_vs_current_munit += 1
            if stored is not None and abs((stored or 0) - expected_future) <= 0.02:
                stored_vs_expected_future += 1
            i124.append(
                {
                    "mpolicy": pol,
                    "plan": post.get("MPLAN"),
                    "current_stored_mdb": stored,
                    "expected_mdb_after_reseed": expected_future,
                    "class": "EXPECTED DOWNSTREAM CONSEQUENCE",
                }
            )
        gold_mdb = next((x for x in i124 if x["mpolicy"] == GOLD), None)
        if not gold_mdb or gold_mdb["current_stored_mdb"] != 25000.0:
            errors.append("gold stored MDB is not 25000.00")
        if not gold_mdb or abs(gold_mdb["expected_mdb_after_reseed"] - 19101.96) > 0.02:
            errors.append("gold expected future MDB is not 19101.96")

    # Output inventory
    inventory = []
    for path in sorted(OUT.glob("*.csv")):
        inventory.append({"table": path.name, "rows": table_rowcount(path)})

    summary = {
        "verdict": "PASS" if not errors else "FAIL",
        "baseline": str(BASE.relative_to(ROOT)),
        "quikridr": rowcount,
        "changed_rows": len(changed),
        "field_hits": dict(field_hits),
        "non_candidate_changes": len(non_cand_changed),
        "protected_fields_ok": protected_ok,
        "gold_ok": gold_ok,
        "issue108a_msave_unchanged": msave_changed == 0,
        "issue124_stored_mdb_ne_current_munit": stored_vs_current_munit,
        "issue124_class": "EXPECTED DOWNSTREAM CONSEQUENCE",
        "errors": errors,
        "other_tables": other_tables,
        "output_inventory": inventory,
    }
    EVID.mkdir(exist_ok=True)
    outp = EVID / "issue143_regression_summary.json"
    outp.write_text(
        json.dumps({"summary": summary, "classifications_sample": classifications[:5], "issue124": i124}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print("wrote", outp)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
