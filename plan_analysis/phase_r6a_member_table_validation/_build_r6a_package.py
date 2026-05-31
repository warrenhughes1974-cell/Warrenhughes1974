"""
R6A — QLAdmin member-table import validation package (READ-ONLY).

Reads the R5 emitted member DBFs and cross-checks against rate-key tables.
Produces:
  r6a_member_table_manifest.csv
  r6a_member_sample_validation.csv
  r6a_member_validation_results.json   (machine-readable structural results)

Does not modify any DBF, loader, or rate logic. Run:
  python plan_analysis/phase_r6a_member_table_validation/_build_r6a_package.py
"""
import os, sys, csv, json, collections

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import dbf
from qla_core import rate_dbf_schema as S

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EMIT_DIR = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf")
KEY_TABLES = ["QuikPlGp", "QuikPlDv", "QuikPlDb", "QuikPlCv", "QuikPlTv"]

MEMBER_CODE_FIELD = {
    "QuikPlGd": ("GDCODE", "GDDESCR", "GENDER"),
    "QuikPlUw": ("UWCODE", "UWDESCR", "UWCLASS"),
    "QuikPlBd": ("BDCODE", "BDDESCR", "BAND"),
    "QuikPlSt": ("ISSCNTRY", "CNTRYTXT", "STATE_COUNTRY"),
    "QuikPlNb": (None, None, "NEW_BUSINESS"),
}


def _s(v):
    if v is None:
        return ""
    if hasattr(v, "isoformat"):
        return f"{v.year:04d}{v.month:02d}{v.day:02d}"
    return str(v).strip()


def _load_member(table):
    path = os.path.join(EMIT_DIR, f"{table}.dbf")
    t = dbf.Table(path)
    t.open(mode=dbf.READ_ONLY)
    rows = []
    for r in t:
        rows.append({f: _s(r[f]) for f in t.field_names})
    t.close()
    return rows


def _load_key_plans_and_segments():
    """Union of PLAN + segmentation tuples from all rate-key tables."""
    plans = set()
    gender = collections.defaultdict(set)
    uw = collections.defaultdict(set)
    band = collections.defaultdict(set)
    st = collections.defaultdict(set)
    for kt in KEY_TABLES:
        path = os.path.join(EMIT_DIR, f"{kt}.dbf")
        if not os.path.isfile(path):
            continue
        t = dbf.Table(path)
        t.open(mode=dbf.READ_ONLY)
        for r in t:
            plan = _s(r.PLAN)
            if not plan:
                continue
            plans.add(plan)
            gender[plan].add(_s(r.GENDER))
            uw[plan].add(_s(r.UWCLASS))
            band[plan].add(_s(r.BAND))
            st[plan].add((_s(r.ISSCNTRY), _s(r.ISSUEST)))
        t.close()
    return plans, gender, uw, band, st


def _dup_key(table, row):
    if table == "QuikPlGd":
        return (row["PLAN"], row["GDCODE"])
    if table == "QuikPlUw":
        return (row["PLAN"], row["UWCODE"])
    if table == "QuikPlBd":
        return (row["PLAN"], row["BDCODE"])
    if table == "QuikPlSt":
        return (row["PLAN"], row["ISSCNTRY"], row["ISSUEST"])
    if table == "QuikPlNb":
        return (row["PLAN"], row["ISSCNTRY"], row["ISSUEST"], row["EFFDATE"])
    return tuple(row.values())


def validate_structural(table, rows):
    issues = []
    blank_plan = sum(1 for r in rows if not r.get("PLAN", "").strip())
    if blank_plan:
        issues.append({"severity": "BLOCKER", "code": "BLANK_PLAN", "count": blank_plan})

    keys = [_dup_key(table, r) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup:
        issues.append({"severity": "BLOCKER", "code": "DUPLICATE_KEY", "count": dup})

    plans = {r["PLAN"] for r in rows if r.get("PLAN", "").strip()}
    if not rows:
        issues.append({"severity": "BLOCKER", "code": "EMPTY_TABLE", "count": 0})

    # placeholder governance (expected, not defects)
    placeholders = collections.Counter()
    if table == "QuikPlBd":
        for r in rows:
            try:
                v = float(r.get("BDLOWVAL") or 0)
            except ValueError:
                v = None
            if v == 0.0:
                placeholders["BDLOWVAL_ZERO"] += 1
            else:
                issues.append({"severity": "INFO", "code": "BDLOWVAL_NON_ZERO",
                               "detail": f"PLAN={r['PLAN']} BDCODE={r['BDCODE']} BDLOWVAL={r.get('BDLOWVAL')}"})
    if table == "QuikPlSt":
        for r in rows:
            if not (r.get("MLOANINT") or "").strip():
                placeholders["MLOANINT_BLANK"] += 1
            else:
                issues.append({"severity": "INFO", "code": "MLOANINT_POPULATED",
                               "detail": f"PLAN={r['PLAN']} MLOANINT={r.get('MLOANINT')}"})
    if table == "QuikPlNb":
        for r in rows:
            if r.get("EFFDATE") != S.STANDARD_EFFDATE:
                issues.append({"severity": "BLOCKER", "code": "EFFDATE_NOT_STANDARD",
                               "detail": f"PLAN={r['PLAN']} EFFDATE={r.get('EFFDATE')}"})
            if not (r.get("TERMDATE") or "").strip():
                placeholders["TERMDATE_OPEN"] += 1
            else:
                issues.append({"severity": "INFO", "code": "TERMDATE_SET",
                               "detail": f"PLAN={r['PLAN']} TERMDATE={r.get('TERMDATE')}"})

    blockers = [i for i in issues if i["severity"] == "BLOCKER"]
    status = "PASS" if not blockers and rows else "FAIL"
    return {
        "table": table,
        "row_count": len(rows),
        "distinct_plan_count": len(plans),
        "status": status,
        "issues": issues,
        "placeholders": dict(placeholders),
    }


def validate_referential(member_data, key_plans, key_gender, key_uw, key_band, key_st):
    """Member PLAN must exist in rate keys; member codes must cover key segmentation."""
    issues = []
    all_member_plans = set()
    for table, rows in member_data.items():
        for r in rows:
            p = r.get("PLAN", "").strip()
            if p:
                all_member_plans.add(p)

    orphan_member_plans = sorted(all_member_plans - key_plans)
    if orphan_member_plans:
        issues.append({"severity": "BLOCKER", "code": "ORPHAN_MEMBER_PLAN",
                       "count": len(orphan_member_plans),
                       "examples": orphan_member_plans[:10]})

    missing_member_for_key = sorted(key_plans - all_member_plans)
    if missing_member_for_key:
        issues.append({"severity": "BLOCKER", "code": "KEY_PLAN_MISSING_MEMBER",
                       "count": len(missing_member_for_key),
                       "examples": missing_member_for_key[:10]})

    # per-plan code coverage vs keys
    gd = collections.defaultdict(set)
    uw = collections.defaultdict(set)
    bd = collections.defaultdict(set)
    st = collections.defaultdict(set)
    for r in member_data["QuikPlGd"]:
        gd[r["PLAN"]].add(r["GDCODE"])
    for r in member_data["QuikPlUw"]:
        uw[r["PLAN"]].add(r["UWCODE"])
    for r in member_data["QuikPlBd"]:
        bd[r["PLAN"]].add(r["BDCODE"])
    for r in member_data["QuikPlSt"]:
        st[r["PLAN"]].add((r["ISSCNTRY"], r["ISSUEST"]))

    for plan in sorted(key_plans):
        for g in key_gender.get(plan, set()) - gd.get(plan, set()):
            issues.append({"severity": "BLOCKER", "code": "MISSING_GENDER_MEMBER",
                           "detail": f"PLAN={plan} GDCODE={g}"})
        for u in key_uw.get(plan, set()) - uw.get(plan, set()):
            issues.append({"severity": "BLOCKER", "code": "MISSING_UW_MEMBER",
                           "detail": f"PLAN={plan} UWCODE={u}"})
        for b in key_band.get(plan, set()) - bd.get(plan, set()):
            issues.append({"severity": "BLOCKER", "code": "MISSING_BAND_MEMBER",
                           "detail": f"PLAN={plan} BDCODE={b}"})
        for s in key_st.get(plan, set()) - st.get(plan, set()):
            issues.append({"severity": "BLOCKER", "code": "MISSING_STATE_MEMBER",
                           "detail": f"PLAN={plan} ISSCNTRY={s[0]} ISSUEST={s[1]}"})

    blockers = [i for i in issues if i["severity"] == "BLOCKER"]
    return issues, len(blockers) == 0


def build_sample_validation(member_data):
    """Representative sample rows for QLAdmin plan-maintenance display checks."""
    samples = []
    seen = set()

    def add(plan, table, member_type, code, display):
        k = (plan, table, member_type, code)
        if k in seen:
            return
        seen.add(k)
        samples.append({
            "PLAN": plan,
            "TABLE_NAME": table,
            "MEMBER_TYPE": member_type,
            "MEMBER_CODE": code,
            "EXPECTED_DISPLAY": display,
            "VALIDATED": "",
        })

    # curated special / coverage plans
    special = [
        ("130JEB", "QuikPlGd", "GENDER", "M", S.GENDER_LABEL.get("M", "MALE")),
        ("130JEB", "QuikPlGd", "GENDER", "F", S.GENDER_LABEL.get("F", "FEMALE")),
        ("1658C1", "QuikPlUw", "UWCLASS", "PR", S.UWCLASS_LABEL.get("PR", "PREFERRED")),
        ("1658C1", "QuikPlUw", "UWCLASS", "SM", S.UWCLASS_LABEL.get("SM", "SMOKER")),
        ("1658C1", "QuikPlBd", "BAND", "01", S.BAND_LABEL.get("01", "BAND 1")),
        ("1L10OD", "QuikPlGd", "GENDER", "M", S.GENDER_LABEL.get("M", "MALE")),
        ("2665ST", "QuikPlBd", "BAND", "01", S.BAND_LABEL.get("01", "BAND 1")),
        ("A96DAR", "QuikPlGd", "GENDER", "F", S.GENDER_LABEL.get("F", "FEMALE")),
    ]
    for plan, table, mtype, code, disp in special:
        add(plan, table, mtype, code, disp)

    # ensure coverage of all standard code domains present in data
    domain_targets = [
        ("QuikPlGd", "GENDER", {"M", "F", "J"}, S.GENDER_LABEL),
        ("QuikPlUw", "UWCLASS", {"00", "NS", "SM", "PR", "ST"}, S.UWCLASS_LABEL),
        ("QuikPlBd", "BAND", {"01", "02", "03"}, S.BAND_LABEL),
    ]
    for table, mtype, targets, label_map in domain_targets:
        code_field, descr_field, _ = MEMBER_CODE_FIELD[table]
        for r in member_data[table]:
            code = r[code_field]
            if code not in targets:
                continue
            add(r["PLAN"], table, mtype, code, r.get(descr_field) or label_map.get(code, code))
            targets.discard(code)
            if not targets:
                break

    # state/country from segmentation tuples
    for r in member_data["QuikPlSt"][:8]:
        code = f"{r['ISSCNTRY']}/{r['ISSUEST']}"
        disp = f"{r.get('CNTRYTXT', '')} / {r.get('STATETXT', '')}".strip(" /")
        add(r["PLAN"], "QuikPlSt", "STATE_COUNTRY", code, disp)

    # new-business window sample
    for r in member_data["QuikPlNb"][:5]:
        code = f"{r['ISSCNTRY']}/{r['ISSUEST']}"
        disp = f"EFFDATE={r['EFFDATE']} TERMDATE=open"
        add(r["PLAN"], "QuikPlNb", "NEW_BUSINESS", code, disp)

    # placeholder governance rows (document expected deferred values)
    for r in member_data["QuikPlBd"]:
        if r["PLAN"] == "2665ST":
            add(r["PLAN"], "QuikPlBd", "MEMBER_PLACEHOLDER_DEFERRED", "BDLOWVAL",
                "BDLOWVAL=0 (band breakpoint; business input pending)")
            break
    for r in member_data["QuikPlSt"]:
        if r["PLAN"] == "130JEB":
            add(r["PLAN"], "QuikPlSt", "MEMBER_PLACEHOLDER_DEFERRED", "MLOANINT",
                "MLOANINT=blank (loan interest; business input pending)")
            break
    for r in member_data["QuikPlNb"]:
        if r["PLAN"] == "130JEB":
            add(r["PLAN"], "QuikPlNb", "MEMBER_PLACEHOLDER_DEFERRED", "TERMDATE",
                "TERMDATE=open (availability end date pending)")
            break

    return samples


def main():
    member_data = {t: _load_member(t) for t in S.MEMBER_TABLES}
    key_plans, key_gender, key_uw, key_band, key_st = _load_key_plans_and_segments()

    manifest_rows = []
    structural = []
    all_structural_pass = True
    for table in S.MEMBER_TABLES:
        res = validate_structural(table, member_data[table])
        structural.append(res)
        manifest_rows.append({
            "TABLE_NAME": table,
            "ROW_COUNT": res["row_count"],
            "DISTINCT_PLAN_COUNT": res["distinct_plan_count"],
            "STATUS": res["status"],
        })
        all_structural_pass = all_structural_pass and res["status"] == "PASS"
        print(f"{res['status']:4} {table:10} rows={res['row_count']:>4} plans={res['distinct_plan_count']:>3} "
              f"placeholders={res['placeholders']}")

    ref_issues, ref_ok = validate_referential(member_data, key_plans, key_gender, key_uw, key_band, key_st)
    ref_blockers = [i for i in ref_issues if i["severity"] == "BLOCKER"]
    print(f"referential: {'PASS' if ref_ok else 'FAIL'} blockers={len(ref_blockers)}")

    samples = build_sample_validation(member_data)

    manifest_path = os.path.join(HERE, "r6a_member_table_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["TABLE_NAME", "ROW_COUNT", "DISTINCT_PLAN_COUNT", "STATUS"])
        w.writeheader()
        w.writerows(manifest_rows)

    sample_path = os.path.join(HERE, "r6a_member_sample_validation.csv")
    with open(sample_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "TABLE_NAME", "MEMBER_TYPE", "MEMBER_CODE",
                                          "EXPECTED_DISPLAY", "VALIDATED"])
        w.writeheader()
        w.writerows(samples)

    results = {
        "phase": "R6A MEMBER TABLE VALIDATION",
        "emit_dir": os.path.relpath(EMIT_DIR, ROOT).replace("\\", "/"),
        "member_tables": len(S.MEMBER_TABLES),
        "total_member_rows": sum(len(v) for v in member_data.values()),
        "distinct_plans_in_keys": len(key_plans),
        "structural": structural,
        "referential_issues": ref_issues,
        "referential_pass": ref_ok,
        "placeholder_governance": {
            "BDLOWVAL": "0 — MEMBER_PLACEHOLDER_DEFERRED (band breakpoints; business input pending)",
            "MLOANINT": "blank — MEMBER_PLACEHOLDER_DEFERRED (loan interest; business input pending)",
            "TERMDATE": "open/blank — MEMBER_PLACEHOLDER_DEFERRED (availability end date pending)",
            "note": "These are expected and must NOT be treated as defects.",
        },
        "sample_validation_rows": len(samples),
        "overall_pass": all_structural_pass and ref_ok,
    }
    results_path = os.path.join(HERE, "r6a_member_validation_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nmanifest: {len(manifest_rows)} tables | sample rows: {len(samples)} | overall_pass={results['overall_pass']}")
    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
