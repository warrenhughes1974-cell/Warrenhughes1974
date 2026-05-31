"""
R6B — QLAdmin sandbox import execution package (READ-ONLY).

Reads R5 emitted DBFs and R6/R6A test artifacts to produce:
  sandbox_import_manifest.csv
  rate_import_validation_matrix.csv
  qladmin_lookup_trace_template.csv

Does not modify DBFs, loaders, or governance. Run:
  python plan_analysis/phase_r6b_sandbox_import_execution/_build_r6b_package.py
"""
import os, sys, csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import dbf
from qla_core import rate_dbf_schema as S

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EMIT_DIR = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf")

LOAD_ORDER = [
    ("QuikPlGd", 1, "member/dimension — gender members"),
    ("QuikPlUw", 2, "member/dimension — UW-class members"),
    ("QuikPlBd", 3, "member/dimension — band members (BDLOWVAL=0 placeholder)"),
    ("QuikPlSt", 4, "member/dimension — state/country members (MLOANINT blank)"),
    ("QuikPlNb", 5, "member/dimension — new-business window (TERMDATE open)"),
    ("QuikPlGp", 6, "rate key — gross premium"),
    ("QuikPlDv", 7, "rate key — dividend"),
    ("QuikPlDb", 8, "rate key — death benefit"),
    ("QuikPlCv", 9, "rate key — cash value"),
    ("QuikPlTv", 10, "rate key — terminal reserve + net premium (shared)"),
    ("QuikGps", 11, "factor — gross premium"),
    ("QuikDvs", 12, "factor — dividend"),
    ("QuikDbs", 13, "factor — death benefit"),
    ("QuikCvs", 14, "factor — cash value"),
    ("QuikTvs", 15, "factor — terminal reserve"),
    ("QuikNps", 16, "factor — net premium"),
]

FACTOR_TABLES = ["QuikGps", "QuikDvs", "QuikDbs", "QuikCvs", "QuikTvs", "QuikNps"]
KEY_TABLES = ["QuikPlGp", "QuikPlDv", "QuikPlDb", "QuikPlCv", "QuikPlTv"]

# Representative lookup cases (EXPECTED_FACTOR from R6 rate_lookup_test_matrix.csv)
LOOKUP_CASES = [
    ("2665ST", "GROSS_PREMIUM", "M", "00", "01", "00", 1, "222.22", "GROSS_PREMIUM representative"),
    ("5L01MA", "GROSS_PREMIUM", "M", "SM", "01", "15", 1, "1.39", "GROSS_PREMIUM representative"),
    ("130JEB", "DIVIDEND", "M", "00", "01", "00", 1, ".00", "DIVIDEND representative"),
    ("130JEB", "DIVIDEND", "M", "00", "01", "00", 6, "2.80", "DIVIDEND representative"),
    ("1659SR", "DEATH_BENEFIT", "M", "SM", "01", "00", 1, "300.00", "DEATH_BENEFIT representative"),
    ("17CSI3", "DEATH_BENEFIT", "M", "00", "01", "46", 1, "4.00", "DEATH_BENEFIT representative"),
    ("130JEB", "CASH_VALUE", "M", "00", "01", "00", 1, ".00", "CASH_VALUE representative"),
    ("1658C1", "CASH_VALUE", "F", "PR", "01", "00", 6, "11.00", "CASH_VALUE representative"),
    ("130JEB", "TERMINAL_RESERVE", "F", "00", "01", "00", 6, "164.19", "TERMINAL_RESERVE representative"),
    ("1658C1", "TERMINAL_RESERVE", "F", "PR", "01", "00", 1, "1.00", "TERMINAL_RESERVE representative"),
    ("130JEB", "NET_PREMIUM", "F", "00", "01", "00", 1, "22.03", "NET_PREMIUM representative"),
    ("1658C1", "NET_PREMIUM", "F", "PR", "01", "00", 6, "11.00", "NET_PREMIUM representative"),
    ("1L10OD", "CASH_VALUE", "M", "ST", "01", "99", 1, "1000.00", "AGE 100 capped to 99; genuine AGE-99 retained"),
    ("2665ST", "DEATH_BENEFIT", "M", "00", "01", "00", 1, "28134.0", "Large DB factor (>9999.99) as 7-char text"),
    ("2665ST", "DEATH_BENEFIT", "M", "00", "01", "00", 6, "28134.0", "Large DB factor (>9999.99) as 7-char text"),
    ("A96DAR", "CASH_VALUE", "M", "00", "01", "00", 41, "9723.28", "Large CV factor (precision-reduced)"),
    ("A96DAR", "CASH_VALUE", "M", "00", "01", "00", 46, "12164.9", "Large CV factor (precision-reduced)"),
]

MEMBER_FUNCTIONAL = [
    ("130JEB", "QuikPlGd", "GENDER_DISPLAY", "M", "MALE displays in plan maintenance"),
    ("130JEB", "QuikPlGd", "GENDER_DISPLAY", "F", "FEMALE displays in plan maintenance"),
    ("7687J3", "QuikPlGd", "GENDER_DISPLAY", "J", "JOINT displays in plan maintenance"),
    ("1658C1", "QuikPlUw", "UWCLASS_DISPLAY", "PR", "PREFERRED displays in plan maintenance"),
    ("1L14SC", "QuikPlUw", "UWCLASS_DISPLAY", "NS", "NON-SMOKER displays in plan maintenance"),
    ("1L1095", "QuikPlUw", "UWCLASS_DISPLAY", "ST", "STANDARD displays in plan maintenance"),
    ("5L01MA", "QuikPlBd", "BAND_DISPLAY", "02", "BAND 2 displays in plan maintenance"),
    ("5L01MA", "QuikPlBd", "BAND_DISPLAY", "03", "BAND 3 displays in plan maintenance"),
    ("130JEB", "QuikPlSt", "STATE_COUNTRY_DISPLAY", "0000/00", "ALL (OTHER) / ALL (OTHER) displays"),
    ("130JEB", "QuikPlNb", "NEW_BUSINESS_DISPLAY", "0000/00", "EFFDATE=19000101 TERMDATE=open"),
    ("2665ST", "QuikPlBd", "PLACEHOLDER_GOVERNANCE", "BDLOWVAL=0", "MEMBER_PLACEHOLDER_DEFERRED — not a defect"),
]

PLAN_LOOKUP = [
    ("130JEB", "QuikPlan", "PLAN_LOOKUP", "Plan exists and opens in QLAdmin plan maintenance"),
    ("2665ST", "QuikPlan", "PLAN_LOOKUP", "Large-factor plan exists and is selectable"),
    ("A96DAR", "QuikPlan", "PLAN_LOOKUP", "Large CV plan exists and is selectable"),
    ("1L10OD", "QuikPlan", "PLAN_LOOKUP", "AGE-cap scenario plan exists and is selectable"),
]


def row_count(table):
    path = os.path.join(EMIT_DIR, f"{table}.dbf")
    t = dbf.Table(path)
    t.open(mode=dbf.READ_ONLY)
    n = len(t)
    t.close()
    return n


def build_manifest():
    rows = []
    for table, seq, note in LOAD_ORDER:
        n = row_count(table)
        rel = os.path.relpath(os.path.join(EMIT_DIR, f"{table}.dbf"), ROOT).replace("\\", "/")
        rows.append({
            "TABLE_NAME": table,
            "ROW_COUNT": n,
            "SOURCE_PATH": rel,
            "LOAD_SEQUENCE": seq,
            "IMPORT_STATUS": "",
            "NOTES": note,
        })
    return rows


def build_validation_matrix(manifest):
    tests = []
    tid = 1

    def add(test_type, plan, table, expected, notes=""):
        nonlocal tid
        tests.append({
            "TEST_ID": f"R6B-{tid:03d}",
            "TEST_TYPE": test_type,
            "PLAN": plan,
            "TABLE": table,
            "EXPECTED_RESULT": expected,
            "ACTUAL_RESULT": "",
            "PASS_FAIL": "",
            "TESTER": "",
            "TEST_DATE": "",
            "NOTES": notes,
        })
        tid += 1

    # import verification per table
    for m in manifest:
        add("IMPORT_VERIFY", "", m["TABLE_NAME"],
            f"Import succeeds; row count = {m['ROW_COUNT']}",
            f"Load sequence {m['LOAD_SEQUENCE']}; source {m['SOURCE_PATH']}")

    # structural post-load
    add("STRUCTURAL", "", "ALL",
        "No orphan PLAN references; no import errors; EFFDATE-bearing tables = 19000101",
        "Cross-check member + key + factor PLAN alignment after full load")

    # plan lookup
    for plan, table, ttype, expected in PLAN_LOOKUP:
        add(ttype, plan, table, expected)

    # member functional
    for plan, table, ttype, code, expected in MEMBER_FUNCTIONAL:
        add(ttype, plan, table, f"{code}: {expected}")

    # rate key recognition
    for kt in KEY_TABLES:
        add("RATE_KEY_RECOGNITION", "", kt,
            f"Rate key table {kt} recognized; keys link to factors",
            "Verify in QLAdmin plan rate key maintenance")

    # factor retrieval (one smoke per family)
    family_smoke = [
        ("2665ST", "QuikGps", "GROSS_PREMIUM", "Factor retrieval succeeds"),
        ("130JEB", "QuikDvs", "DIVIDEND", "Factor retrieval succeeds"),
        ("2665ST", "QuikDbs", "DEATH_BENEFIT", "Factor retrieval succeeds"),
        ("130JEB", "QuikCvs", "CASH_VALUE", "Factor retrieval succeeds"),
        ("130JEB", "QuikTvs", "TERMINAL_RESERVE", "Factor/reserve retrieval succeeds"),
        ("130JEB", "QuikNps", "NET_PREMIUM", "Factor retrieval succeeds"),
    ]
    for plan, table, fam, expected in family_smoke:
        add(f"{fam}_RETRIEVAL", plan, table, expected)

    # detailed lookup cases
    for plan, fam, sex, uw, band, age, dur, factor, notes in LOOKUP_CASES:
        table = {"GROSS_PREMIUM": "QuikGps", "DIVIDEND": "QuikDvs", "DEATH_BENEFIT": "QuikDbs",
                 "CASH_VALUE": "QuikCvs", "TERMINAL_RESERVE": "QuikTvs", "NET_PREMIUM": "QuikNps"}[fam]
        test_type = {
            "GROSS_PREMIUM": "GROSS_PREMIUM_LOOKUP",
            "DIVIDEND": "DIVIDEND_LOOKUP",
            "DEATH_BENEFIT": "DEATH_BENEFIT_LOOKUP",
            "CASH_VALUE": "CASH_VALUE_LOOKUP",
            "TERMINAL_RESERVE": "RESERVE_LOOKUP",
            "NET_PREMIUM": "NET_PREMIUM_LOOKUP",
        }[fam]
        if plan == "1L10OD":
            test_type = "AGE_99_SCENARIO"
        if plan == "2665ST" and fam == "DEATH_BENEFIT":
            test_type = "LARGE_FACTOR_2665ST"
        if plan == "A96DAR":
            test_type = "LARGE_FACTOR_A96DAR"
        add(test_type, plan, table,
            f"Factor={factor} at AGE={age} DURATION={dur} SEX={sex} UW={uw} BAND={band}",
            notes)

    return tests


def build_lookup_trace():
    rows = []
    for plan, fam, sex, uw, band, age, dur, factor, notes in LOOKUP_CASES:
        rows.append({
            "PLAN": plan,
            "RATE_FAMILY": fam,
            "SEX": sex,
            "UWCLASS": uw,
            "BAND": band,
            "AGE": age,
            "DURATION": dur,
            "EXPECTED_FACTOR": factor,
            "ACTUAL_FACTOR": "",
            "MATCH_STATUS": "",
            "NOTES": notes,
        })
    return rows


def main():
    manifest = build_manifest()
    matrix = build_validation_matrix(manifest)
    trace = build_lookup_trace()

    manifest_path = os.path.join(HERE, "sandbox_import_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["TABLE_NAME", "ROW_COUNT", "SOURCE_PATH",
                                          "LOAD_SEQUENCE", "IMPORT_STATUS", "NOTES"])
        w.writeheader()
        w.writerows(manifest)

    matrix_path = os.path.join(HERE, "rate_import_validation_matrix.csv")
    with open(matrix_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["TEST_ID", "TEST_TYPE", "PLAN", "TABLE",
                                          "EXPECTED_RESULT", "ACTUAL_RESULT", "PASS_FAIL",
                                          "TESTER", "TEST_DATE", "NOTES"])
        w.writeheader()
        w.writerows(matrix)

    trace_path = os.path.join(HERE, "qladmin_lookup_trace_template.csv")
    with open(trace_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "RATE_FAMILY", "SEX", "UWCLASS", "BAND",
                                          "AGE", "DURATION", "EXPECTED_FACTOR", "ACTUAL_FACTOR",
                                          "MATCH_STATUS", "NOTES"])
        w.writeheader()
        w.writerows(trace)

    total = sum(m["ROW_COUNT"] for m in manifest)
    print(f"manifest: {len(manifest)} tables | total rows: {total}")
    print(f"validation matrix: {len(matrix)} tests")
    print(f"lookup trace template: {len(trace)} rows")
    for m in manifest:
        print(f"  seq={m['LOAD_SEQUENCE']:2d} {m['TABLE_NAME']:10} rows={m['ROW_COUNT']:>6}")


if __name__ == "__main__":
    main()
