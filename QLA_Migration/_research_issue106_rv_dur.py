"""Read-only Issue #106 diagnostics: QuikTvs Dur shift + 1L1095 source lineage."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUIKTVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"
RATE_TABLE = ROOT / "plan_analysis" / "source_data" / "rates" / "Rate_Table_Extract_20260427.csv"


def quiktvs_slice(plan: str, gender: str, age: int, uw: str | None = None) -> dict[int, str]:
    age_s = str(age).zfill(2)
    vals: dict[int, str] = {}
    pages = 0
    uws: set[str] = set()
    with QUIKTVS.open(newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["PLAN"].strip() != plan:
                continue
            if r["GENDER"].strip() != gender:
                continue
            if r["AGE"].strip() != age_s:
                continue
            if uw is not None and r["UWCLASS"].strip() != uw:
                continue
            pages += 1
            uws.add(r["UWCLASS"].strip())
            cntl = int(r["CNTL"])
            for i in range(10):
                v = (r.get(f"TV{i}") or "").strip()
                if v:
                    vals[cntl * 10 + i] = v
    print(f"=== QuikTvs {plan} {gender}/{age_s} uw={uw} pages={pages} uws={sorted(uws)[:8]}")
    for d in (0, 1, 2, 3, 82, 83, 84):
        print(f"  Dur {d}: {vals.get(d, '<blank>')}")
    return vals


def rate_table_rv(coverage: str, age: int, sex: str, durs: tuple[str, ...]) -> None:
    age_s = str(age)
    print(f"=== Rate_Table RV {coverage} {sex}/{age} durs={durs}")
    with RATE_TABLE.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if (row.get("TYPE_CODE") or "").strip() != "RV":
                continue
            if (row.get("COVERAGE_ID") or "").strip() != coverage:
                continue
            if (row.get("AGE") or "").strip().lstrip("0") != age_s.lstrip("0"):
                # allow 17 vs 017
                if (row.get("AGE") or "").strip() not in (age_s, age_s.zfill(2), age_s.zfill(3)):
                    continue
            if (row.get("SEX") or "").strip() != sex:
                continue
            dur = (row.get("DURATION") or "").strip()
            if dur not in durs:
                continue
            rate = (row.get("RATE") or row.get("FACTOR") or "").strip()
            uw = (row.get("UWCLASS") or row.get("UW_CLASS") or row.get("SMOKER") or "").strip()
            band = (row.get("BAND") or "").strip()
            print(f"  Dur {dur}: {rate} uw={uw} band={band}")


def count_coverage_contains(needle: str) -> int:
    n = 0
    with RATE_TABLE.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if needle in (row.get("COVERAGE_ID") or ""):
                n += 1
    return n


def main() -> None:
    print("QuikTvs exists:", QUIKTVS.exists(), "Rate_Table exists:", RATE_TABLE.exists())
    quiktvs_slice("170858", "M", 17)
    quiktvs_slice("1659C2", "M", 17, "SM")
    quiktvs_slice("221END", "M", 17)
    quiktvs_slice("1960OL", "M", 17)
    quiktvs_slice("1L1095", "M", 17)
    quiktvs_slice("17085M", "M", 17)
    rate_table_rv("670 GL85-8", 17, "M", ("1", "2", "83", "0"))
    rate_table_rv("659 CEN II", 17, "M", ("1", "0", "83"))
    print("Rate_Table rows with COVERAGE_ID containing LP9595:", count_coverage_contains("LP9595"))
    print("Rate_Table rows with COVERAGE_ID containing L10 LP95:", count_coverage_contains("L10 LP95"))


if __name__ == "__main__":
    main()
