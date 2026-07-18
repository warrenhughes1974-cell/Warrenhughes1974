"""
Issue #80 validator — QuikPlCv / QuikPlTv / quikplan match Valuation_Setup for IN_SCOPE plans.

Compares Output to Issue_Log_Items/Issue_80/evidence/cso_valuation_setup_coded_expected.csv
(scope_issue80=IN_SCOPE only). PUA and missing-QLA rows are excluded.

Optional:
  --publish-test-validation  clean-publish quikplan + QuikPlCv/Tv to Test_Validation
"""
from __future__ import annotations

import argparse
import csv
import filecmp
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
TEST_VAL = OUT / "Test_Validation"
EXP_PATH = ROOT / "Issue_Log_Items" / "Issue_80" / "evidence" / "cso_valuation_setup_coded_expected.csv"
AUTH_PATH = ROOT / "plan_analysis" / "source_data" / "rates" / "CSO_Valuation_Setup.csv"

QUIKPLAN_ONLY_PLANS = frozenset({"10L171", "10L172", "117JPO"})
PUA_DEFER_PLANS = frozenset({
    "121PUA", "170PUA", "185PUA", "1970PA", "1OLPUA", "1POPUA", "261PUA", "265PUA", "280PUA",
})
ALLOWED_TEST_VAL = frozenset({
    "manifest.txt",
    "quikplan.csv",
    "rates/QuikPlCv.csv",
    "rates/QuikPlTv.csv",
})
PROHIBITED_OUTPUT_ARTIFACTS = (
    OUT / "quikplan.csv.bak_issue80",
    OUT / "Reports" / "issue80_quikplan_overlay_qa.csv",
)

CV_FIELDS = [
    ("MORT", "QuikPlCv_MORT"),
    ("ETIMORT", "QuikPlCv_ETIMORT"),
    ("NFOINT", "QuikPlCv_NFOINT"),
    ("INTMETHCV", "QuikPlCv_INTMETHCV"),
]
TV_FIELDS = [
    ("MORT", "QuikPlTv_MORT"),
    ("RSVINT", "QuikPlTv_RSVINT"),
    ("RSVMETH", "QuikPlTv_RSVMETH"),
    ("INTMETHTV", "QuikPlTv_INTMETHTV"),
    ("STOREMEANS", "QuikPlTv_STOREMEANS", True),
    ("CALCMIDS", "QuikPlTv_CALCMIDS", True),
]
QP_FIELDS = [
    ("NFOINT", "QuikPlCv_NFOINT"),
    ("INTMETHCV", "QuikPlCv_INTMETHCV"),
]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def header(path: Path) -> list[str]:
    rows = read(path)
    return list(rows[0].keys()) if rows else []


def norm_logical(v) -> str:
    if v is None or v == "":
        return ""
    s = str(v).strip().upper()
    if s in ("Y", "T", "TRUE", "1"):
        return "Y"
    if s in ("N", "F", "FALSE", "0"):
        return "N"
    return s


def norm_char(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def norm_expected(v, logical: bool) -> str:
    if logical:
        return norm_logical(v)
    return norm_char(v)


def load_expected() -> dict[str, dict]:
    exp = {}
    for r in read(EXP_PATH):
        if (r.get("scope_issue80") or "").strip() != "IN_SCOPE":
            continue
        plan = (r.get("qla_plan") or "").strip()
        if plan:
            exp[plan] = r
    return exp


def authority_plans() -> set[str]:
    return {(r.get("qla_plan") or "").strip() for r in read(AUTH_PATH) if (r.get("qla_plan") or "").strip()}


def compare_rows(rows, plan_set, exp, field_specs, table_label, fails, sample_limit=12):
    by_plan = defaultdict(list)
    for r in rows:
        p = (r.get("PLAN") or "").strip()
        if p in plan_set:
            by_plan[p].append(r)

    missing_plans = sorted(plan_set - set(by_plan))
    if missing_plans:
        fails.append(f"{table_label}_MISSING_PLANS count={len(missing_plans)} sample={missing_plans[:8]}")

    mismatches = []
    for plan in sorted(plan_set):
        for r in by_plan.get(plan, []):
            e = exp[plan]
            for spec in field_specs:
                logical = len(spec) > 2 and spec[2]
                fld, efld = spec[0], spec[1]
                got = norm_expected(r.get(fld), logical)
                want = norm_expected(e.get(efld), logical)
                if got != want:
                    mismatches.append(
                        f"{table_label}:{plan}:{fld} got={got!r} want={want!r} "
                        f"G={r.get('GENDER','')} UW={r.get('UWCLASS','')}"
                    )
                    if len(mismatches) >= sample_limit:
                        break
            if len(mismatches) >= sample_limit:
                break
        if len(mismatches) >= sample_limit:
            break

    if mismatches:
        fails.append(f"{table_label}_MISMATCH count>={len(mismatches)} sample={mismatches[:sample_limit]}")


def check_schema(path: Path, expected_cols: list[str], label: str, fails: list[str]) -> None:
    cols = header(path)
    if not cols:
        fails.append(f"{label}_SCHEMA empty or missing")
        return
    if cols != expected_cols:
        fails.append(f"{label}_SCHEMA order mismatch got={cols[:6]}... want={expected_cols[:6]}...")


def check_test_validation_purity(fails: list[str]) -> None:
    if not TEST_VAL.is_dir():
        fails.append("TEST_VALIDATION missing")
        return
    found = set()
    for p in TEST_VAL.rglob("*"):
        if p.is_file():
            rel = p.relative_to(TEST_VAL).as_posix()
            found.add(rel)
    extra = sorted(found - ALLOWED_TEST_VAL)
    missing = sorted(ALLOWED_TEST_VAL - found)
    if extra:
        fails.append(f"TEST_VALIDATION_EXTRA count={len(extra)} sample={extra[:8]}")
    if missing:
        fails.append(f"TEST_VALIDATION_MISSING count={len(missing)} sample={missing[:8]}")


def check_test_validation_matches_output(fails: list[str]) -> None:
    pairs = [
        (OUT / "quikplan.csv", TEST_VAL / "quikplan.csv"),
        (RATES / "QuikPlCv.csv", TEST_VAL / "rates" / "QuikPlCv.csv"),
        (RATES / "QuikPlTv.csv", TEST_VAL / "rates" / "QuikPlTv.csv"),
    ]
    for src, dst in pairs:
        if not dst.is_file():
            fails.append(f"TEST_VALIDATION missing {dst.name}")
            continue
        if not filecmp.cmp(src, dst, shallow=False):
            fails.append(f"TEST_VALIDATION_STALE {dst.relative_to(OUT)}")


def check_quikplan_only_absent(cv: list[dict], tv: list[dict], fails: list[str]) -> None:
    cv_plans = {(r.get("PLAN") or "").strip() for r in cv}
    tv_plans = {(r.get("PLAN") or "").strip() for r in tv}
    for plan in sorted(QUIKPLAN_ONLY_PLANS):
        if plan in cv_plans:
            fails.append(f"INVENTED_QuikPlCv_KEY plan={plan}")
        if plan in tv_plans:
            fails.append(f"INVENTED_QuikPlTv_KEY plan={plan}")


def check_pua_isolation(auth: set[str], fails: list[str]) -> None:
    leaked = sorted(PUA_DEFER_PLANS & auth)
    if leaked:
        fails.append(f"PUA_IN_AUTHORITY count={len(leaked)} sample={leaked[:8]}")


def check_output_artifacts(fails: list[str]) -> None:
    for p in PROHIBITED_OUTPUT_ARTIFACTS:
        if p.exists():
            fails.append(f"PROHIBITED_OUTPUT_ARTIFACT {p.relative_to(ROOT)}")


def check_app_version(fails: list[str]) -> None:
    for rel in ("app.py", "QLA_Migration/app.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if 'APP_VERSION = "v58.01"' not in text:
            fails.append(f"APP_VERSION not v58.01 in {rel}")


def publish_test_validation() -> None:
    script = ROOT / "tools" / "publish_test_validation.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--clean",
            "--issue",
            "Issue_80",
            "quikplan",
            "--rates",
            "QuikPlCv",
            "QuikPlTv",
        ],
        check=True,
        cwd=str(ROOT),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #80 validation")
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="Clean-publish Issue #80 tables to Output/Test_Validation before checks",
    )
    args = ap.parse_args()

    if args.publish_test_validation:
        publish_test_validation()

    fails: list[str] = []
    exp = load_expected()
    if not exp:
        print(f"FAIL: no IN_SCOPE rows in {EXP_PATH}")
        return 1

    plan_set = set(exp)
    rate_key_plans = plan_set - QUIKPLAN_ONLY_PLANS
    auth = authority_plans()

    cv_path = RATES / "QuikPlCv.csv"
    tv_path = RATES / "QuikPlTv.csv"
    qp_path = OUT / "quikplan.csv"
    cv = read(cv_path)
    tv = read(tv_path)
    qp = read(qp_path)

    from qla_core import rate_dbf_schema as S
    from qla_core.schema_constants import QUIKPLAN_SCHEMA

    check_schema(cv_path, [f[0] for f in S.key_table_fields("QuikPlCv")], "QuikPlCv", fails)
    check_schema(tv_path, [f[0] for f in S.key_table_fields("QuikPlTv")], "QuikPlTv", fails)
    check_schema(qp_path, list(QUIKPLAN_SCHEMA), "quikplan", fails)

    compare_rows(cv, rate_key_plans, exp, CV_FIELDS, "QuikPlCv", fails)
    compare_rows(tv, rate_key_plans, exp, TV_FIELDS, "QuikPlTv", fails)
    check_quikplan_only_absent(cv, tv, fails)
    check_pua_isolation(auth, fails)
    check_output_artifacts(fails)
    check_app_version(fails)
    check_test_validation_purity(fails)
    check_test_validation_matches_output(fails)

    qp_by = {(r.get("PLAN") or "").strip(): r for r in qp}
    qp_miss = sorted(plan_set - set(qp_by))
    if qp_miss:
        fails.append(f"quikplan_MISSING_PLANS count={len(qp_miss)} sample={qp_miss[:8]}")

    qp_mismatch = []
    for plan in sorted(plan_set):
        r = qp_by.get(plan)
        if not r:
            continue
        e = exp[plan]
        for fld, efld in QP_FIELDS:
            got = norm_char(r.get(fld))
            want = norm_char(e.get(efld))
            if got != want:
                qp_mismatch.append(f"quikplan:{plan}:{fld} got={got!r} want={want!r}")
    if qp_mismatch:
        fails.append(f"quikplan_MISMATCH count={len(qp_mismatch)} sample={qp_mismatch[:12]}")

    print("Issue #80 validation (Valuation_Setup IN_SCOPE)")
    print(f"  expected plans: {len(plan_set)} (rate keys: {len(rate_key_plans)}, quikplan-only: {len(QUIKPLAN_ONLY_PLANS)})")
    print(f"  authority file plans: {len(auth)}")
    print(f"  QuikPlCv rows (in-scope plans): {sum(1 for r in cv if (r.get('PLAN') or '').strip() in plan_set)}")
    print(f"  QuikPlTv rows (in-scope plans): {sum(1 for r in tv if (r.get('PLAN') or '').strip() in plan_set)}")
    print(f"  quikplan rows matched: {len(plan_set) - len(qp_miss)}")

    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        return 1

    print("PASS")
    print("  values, schema, package purity, PUA isolation, and Test_Validation parity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
