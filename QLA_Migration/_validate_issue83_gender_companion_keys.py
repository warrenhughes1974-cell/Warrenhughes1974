"""
Issue #83 validator - fleet F/M companion rate keys.

Checks:
  * No remaining F/M companion gaps across QuikPlGp/Db/Cv/Tv/Dv.
  * 221END Cash Value has M Values=Y and F Values=N.
  * quikplan PVO is enabled for plans that gained companion keys.
  * Test_Validation mirrors the modified rate key/member tables.
  * Both app.py copies carry v58.02.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
TEST_VAL = OUT / "Test_Validation"

FAMILIES = ("QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv")
FACTORS = {
    "QuikPlGp": "QuikGps",
    "QuikPlDb": "QuikDbs",
    "QuikPlCv": "QuikCvs",
    "QuikPlTv": "QuikTvs",
    "QuikPlDv": "QuikDvs",
}
KEY_FILES = tuple(f"{t}.csv" for t in FAMILIES)
MEMBER_FILES = ("QuikPlGd.csv", "QuikPlUw.csv", "QuikPlBd.csv", "QuikPlSt.csv", "QuikPlNb.csv")
EXPECTED_VERSION = 'APP_VERSION = "v58.02"'


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def rows_equal(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


def key_genders(table: str) -> dict[str, set[str]]:
    by = defaultdict(set)
    for r in read(RATES / f"{table}.csv"):
        by[(r.get("PLAN") or "").strip()].add((r.get("GENDER") or "").strip())
    return by


def factor_genders(table: str) -> dict[str, set[str]]:
    by = defaultdict(set)
    for r in read(RATES / f"{FACTORS[table]}.csv"):
        by[(r.get("PLAN") or "").strip()].add((r.get("GENDER") or "").strip())
    return by


def companion_gaps() -> list[str]:
    gd = defaultdict(set)
    for r in read(RATES / "QuikPlGd.csv"):
        gd[(r.get("PLAN") or "").strip()].add((r.get("GDCODE") or "").strip())

    gaps = []
    for table in FAMILIES:
        keys = key_genders(table)
        for plan, members in sorted(gd.items()):
            if not {"F", "M"}.issubset(members):
                continue
            have = keys.get(plan, set())
            if not (have & {"F", "M"}):
                continue
            missing = sorted({"F", "M"} - have)
            for gender in missing:
                gaps.append(f"{table}:{plan}:{gender}")
    return gaps


def validate_anchor(fails: list[str]) -> None:
    rows = [r for r in read(RATES / "QuikPlCv.csv") if (r.get("PLAN") or "").strip() == "221END"]
    by_gender = {(r.get("GENDER") or "").strip(): r for r in rows}
    if not {"F", "M"}.issubset(by_gender):
        fails.append(f"221END_QuikPlCv_missing_gender have={sorted(by_gender)}")
        return
    cv_factors = factor_genders("QuikPlCv").get("221END", set())
    if "M" not in cv_factors:
        fails.append("221END_QuikPlCv_M_expected_ValuesY_missing_factor")
    if "F" in cv_factors:
        fails.append("221END_QuikPlCv_F_expected_ValuesN_but_factor_exists")
    for gender in ("F", "M"):
        r = by_gender[gender]
        expected = {"MORT": "N1", "ETIMORT": "N1", "NFOINT": "2", "INTMETHCV": "0"}
        bad = {k: r.get(k) for k, v in expected.items() if (r.get(k) or "").strip() != v}
        if bad:
            fails.append(f"221END_QuikPlCv_{gender}_assumption_mismatch {bad}")


def validate_pvo(fails: list[str]) -> None:
    qp = {(r.get("PLAN") or "").strip(): r for r in read(OUT / "quikplan.csv")}
    for plan in ("221END", "222END", "2665ST", "130JEB"):
        row = qp.get(plan)
        if not row:
            fails.append(f"quikplan_missing_{plan}")
            continue
        if (row.get("GDVARYCV") or "").strip() != "Y":
            fails.append(f"{plan}_GDVARYCV_not_Y")
        if (row.get("PLANVALOPT") or "").strip() != "Y":
            fails.append(f"{plan}_PLANVALOPT_not_Y")


def validate_test_validation(fails: list[str]) -> None:
    if not rows_equal(OUT / "quikplan.csv", TEST_VAL / "quikplan.csv"):
        fails.append("Test_Validation_quikplan_not_in_sync")
    for fname in KEY_FILES + MEMBER_FILES:
        if not rows_equal(RATES / fname, TEST_VAL / "rates" / fname):
            fails.append(f"Test_Validation_rates_not_in_sync:{fname}")


def validate_versions(fails: list[str]) -> None:
    for rel in ("app.py", "QLA_Migration/app.py"):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if EXPECTED_VERSION not in text:
            fails.append(f"APP_VERSION_not_v58.02:{rel}")


def main() -> int:
    fails: list[str] = []
    gaps = companion_gaps()
    if gaps:
        fails.append(f"COMPANION_GAPS count={len(gaps)} sample={gaps[:10]}")
    validate_anchor(fails)
    validate_pvo(fails)
    validate_test_validation(fails)
    validate_versions(fails)

    print("Issue #83 validation")
    print(f"  companion gaps: {len(gaps)}")
    print("  anchor: 221END QuikPlCv F=Values N, M=Values Y")
    print("  Test_Validation parity checked")
    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS")
    print("  fleet F/M companion keys, anchor, PVO, version, and parity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
