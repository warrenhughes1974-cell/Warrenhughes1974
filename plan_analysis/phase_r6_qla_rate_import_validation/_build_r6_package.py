"""
R6 — build the QLAdmin rate import & functional validation package (READ-ONLY).

Reads the R5 emitted DBFs and produces:
  qla_import_package_manifest.csv     row counts + EFFDATE values + status per table
  rate_test_policy_selection.csv      representative test cases (real plans/segments)
  rate_lookup_test_matrix.csv         concrete lookup cases with EXPECTED_VALUE from the DBFs

Does not modify any DBF or emitted value. Run:
  python plan_analysis/phase_r6_qla_rate_import_validation/_build_r6_package.py
"""
import os, sys, csv, collections

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import dbf
from qla_core import rate_dbf_schema as S

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EMIT_DIR = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf")

FACTOR_TABLES = ["QuikGps", "QuikDvs", "QuikDbs", "QuikCvs", "QuikTvs", "QuikNps"]
KEY_TABLES = ["QuikPlGp", "QuikPlDv", "QuikPlDb", "QuikPlCv", "QuikPlTv"]
KEYFLD = ("PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def effdate_str(d):
    if d is None:
        return ""
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def load_factor(table):
    """Return list of row dicts (factor cells as text) + a key->row index."""
    path = os.path.join(EMIT_DIR, f"{table}.dbf")
    t = dbf.Table(path); t.open(mode=dbf.READ_ONLY)
    rows = []
    for r in t:
        d = {f: (r[f].strip() if isinstance(r[f], str) else r[f]) for f in t.field_names}
        d["EFFDATE"] = effdate_str(r.EFFDATE)
        rows.append(d)
    t.close()
    return rows


def main():
    # ---- manifest ----
    manifest = []
    factor_cache = {}
    for fn in sorted(os.listdir(EMIT_DIR)):
        if not fn.lower().endswith(".dbf"):
            continue
        name = fn[:-4]
        path = os.path.join(EMIT_DIR, fn)
        t = dbf.Table(path); t.open(mode=dbf.READ_ONLY)
        has_eff = "EFFDATE" in t.field_names
        eff = collections.Counter()
        n = len(t)
        if has_eff:
            for r in t:
                eff[effdate_str(r.EFFDATE)] += 1
        t.close()
        if name in FACTOR_TABLES:
            kind = "factor table"
        elif name in S.MEMBER_TABLES:
            kind = "member/dimension table"
        else:
            kind = "rate-key table"
        if has_eff:
            vals = "|".join(sorted(eff))
            status = "PASS" if vals == S.STANDARD_EFFDATE else "REVIEW"
        else:
            vals = "N/A (no EFFDATE field)"
            status = "PASS"
        manifest.append({"TABLE_NAME": name,
                         "FILE_PATH": os.path.relpath(path, ROOT).replace("\\", "/"),
                         "ROW_COUNT": n, "EFFDATE_VALUES": vals,
                         "VALIDATION_STATUS": status,
                         "NOTES": kind})
    with open(os.path.join(HERE, "qla_import_package_manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["TABLE_NAME", "FILE_PATH", "ROW_COUNT",
                                          "EFFDATE_VALUES", "VALIDATION_STATUS", "NOTES"])
        w.writeheader(); w.writerows(manifest)

    # cache factor rows
    for table in FACTOR_TABLES:
        factor_cache[table] = load_factor(table)

    # ---- test policy selection + lookup matrix ----
    selection = []
    matrix = []

    def add_case(table, row, reason, notes=""):
        pfx = S.PREFIX[table]
        fam = S.FAMILY[table]
        # choose up to 2 populated duration columns
        cols = [i for i in range(S.N_DURATION_COLS) if row.get(f"{pfx}{i}", "")]
        if not cols:
            return
        chosen = [cols[0]] + ([cols[len(cols) // 2]] if len(cols) > 1 else [])
        cntl_i = int(row["CNTL"])
        for col in chosen:
            src_dur = cntl_i * 10 + col + 1  # source (1-based) duration
            selection.append({
                "PLAN": row["PLAN"], "RATE_FAMILY": fam, "SEX": row["GENDER"], "BAND": row["BAND"],
                "UWCLASS": row["UWCLASS"], "ISSUE_AGE": row["AGE"], "TEST_DURATION": src_dur,
                "EXPECTED_RATE_SOURCE": f"{table}.dbf (emitted)",
                "SPECIAL_TEST_REASON": reason, "NOTES": notes,
            })
            matrix.append({
                "PLAN": row["PLAN"], "RATE_FAMILY": fam, "TABLE_NAME": table,
                "KEY_TABLE_NAME": S.KEY_TABLE[table], "SEX": row["GENDER"], "BAND": row["BAND"],
                "UWCLASS": row["UWCLASS"], "EFFDATE": row["EFFDATE"], "ISSUE_AGE": row["AGE"],
                "DURATION": src_dur, "CNTL": row["CNTL"], "FACTOR_COLUMN": f"{pfx}{col}",
                "EXPECTED_VALUE": row[f"{pfx}{col}"], "TEST_RESULT": "", "NOTES": reason,
            })

    # one representative plan per family (broad coverage)
    for table in FACTOR_TABLES:
        rows = factor_cache[table]
        by_plan = collections.defaultdict(list)
        for r in rows:
            by_plan[r["PLAN"]].append(r)
        # pick up to 2 plans, prefer ones with segmentation variety
        plans = sorted(by_plan)[:2]
        for plan in plans:
            # pick a row whose factor cells are populated
            rep = next((r for r in by_plan[plan]
                        if any(r.get(f"{S.PREFIX[table]}{i}", "") for i in range(10))), by_plan[plan][0])
            add_case(table, rep, f"{S.FAMILY[table]} representative coverage")

    # special scenarios
    def find_row(table, plan, age=None, predicate=None):
        for r in factor_cache[table]:
            if r["PLAN"] != plan:
                continue
            if age is not None and r["AGE"] != age:
                continue
            if predicate and not predicate(r):
                continue
            return r
        return None

    r = find_row("QuikCvs", "1L10OD", age="99")
    if r:
        add_case("QuikCvs", r, "AGE 100 capped to 99 (collision protection)",
                 "genuine AGE 99 CV retained; capped terminal value dropped + audited")
    r = find_row("QuikDbs", "2665ST")
    if r:
        add_case("QuikDbs", r, "large DB factor (>9999.99) stored as 7-char text",
                 "physically validated storable text; magnitude preserved")
    # A96DAR: find a precision-reduced cell (value with a single decimal that was 2dp source)
    r = find_row("QuikCvs", "A96DAR",
                 predicate=lambda x: any("." in x.get(f"CV{i}", "") and len(x[f"CV{i}"].split(".")[1]) == 1
                                         for i in range(10)))
    if r:
        add_case("QuikCvs", r, "large CV factor (precision-reduced to fit CHAR(7))",
                 "magnitude preserved; 2nd decimal reduced to fit 7 chars")

    with open(os.path.join(HERE, "rate_test_policy_selection.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "RATE_FAMILY", "SEX", "BAND", "UWCLASS",
                                          "ISSUE_AGE", "TEST_DURATION", "EXPECTED_RATE_SOURCE",
                                          "SPECIAL_TEST_REASON", "NOTES"])
        w.writeheader(); w.writerows(selection)

    with open(os.path.join(HERE, "rate_lookup_test_matrix.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "RATE_FAMILY", "TABLE_NAME", "KEY_TABLE_NAME",
                                          "SEX", "BAND", "UWCLASS", "EFFDATE", "ISSUE_AGE", "DURATION",
                                          "CNTL", "FACTOR_COLUMN", "EXPECTED_VALUE", "TEST_RESULT", "NOTES"])
        w.writeheader(); w.writerows(matrix)

    print("manifest tables:", len(manifest), "| total rows:", sum(m["ROW_COUNT"] for m in manifest))
    print("test cases (selection):", len(selection), "| lookup matrix rows:", len(matrix))
    for m in manifest:
        print(f"  {m['VALIDATION_STATUS']} {m['TABLE_NAME']:10} rows={m['ROW_COUNT']:>6} eff={m['EFFDATE_VALUES']}")


if __name__ == "__main__":
    main()
