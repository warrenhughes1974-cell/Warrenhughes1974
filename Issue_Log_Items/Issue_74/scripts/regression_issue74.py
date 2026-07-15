"""Read-only regression checks for Issue #74 — quikplan VARDB 4→0 only."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "QLA_Migration" / "Output"
TV = OUTPUT / "Test_Validation"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"
RULEBOOK = ROOT / "QLA_Migration" / "Configs" / "Sync_Rulebook_quikplan.csv"

EXPECTED_COUNTS = {
    "quikmstr.csv": 5083,
    "quikridr.csv": 6934,
    "quikplan.csv": 141,
    "quikclnt.csv": 13597,
    "quikprmh.csv": 209470,
}


def _load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    checks: list[tuple] = []

    for name, exp in EXPECTED_COUNTS.items():
        path = OUTPUT / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        n = len(_load(path))
        checks.append(("rowcount", name, n))
        if n != exp:
            errors.append(f"{name} row count {n} != expected {exp}")

    qp_o = _load(OUTPUT / "quikplan.csv")
    qp_t = _load(TV / "quikplan.csv")
    by_o = {(r.get("PLAN") or "").strip(): r for r in qp_o}
    by_t = {(r.get("PLAN") or "").strip(): r for r in qp_t}
    parity_bad = 0
    for plan in set(by_o) | set(by_t):
        ro, rt = by_o.get(plan), by_t.get(plan)
        if not ro or not rt:
            parity_bad += 1
            continue
        if (ro.get("VARDB") or "").strip() != (rt.get("VARDB") or "").strip():
            parity_bad += 1
    checks.append(("tv_parity_mismatch", parity_bad))
    if parity_bad:
        errors.append(f"Output vs Test_Validation quikplan mismatches: {parity_bad}")

    if not RULEBOOK.is_file() or ",VARDB,0,,," not in RULEBOOK.read_text(encoding="utf-8", errors="replace"):
        errors.append("Sync_Rulebook_quikplan VARDB default != 0")

    m = _load(OUTPUT / "quikmstr.csv")
    bad44 = sum(
        1 for r in m if (r.get("MSTATUS") or "").strip() == "44" and (r.get("MNFOPT") or "").strip() != "2"
    )
    bad45 = sum(
        1 for r in m if (r.get("MSTATUS") or "").strip() == "45" and (r.get("MNFOPT") or "").strip() != "3"
    )
    checks.append(("issue72_bad44", bad44))
    checks.append(("issue72_bad45", bad45))
    if bad44 or bad45:
        errors.append(f"Issue #72 MNFOPT regression: bad44={bad44} bad45={bad45}")

    pol = by_o.get("010407670C") if "010407670C" in by_o else None
    if pol:
        checks.append(("sample_010407670C", "N/A"))
    else:
        pass
    by_m = {(r.get("MPOLICY") or "").strip(): r for r in m}
    r72 = by_m.get("010407670C")
    if r72:
        if (r72.get("MSTATUS") or "").strip() != "45" or (r72.get("MNFOPT") or "").strip() != "3":
            errors.append("010407670C MSTATUS/MNFOPT drift from Issue #72 expected")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    reg_path = EVIDENCE / "issue74_regression_checks.csv"
    with reg_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["check", "value1", "value2", "value3"])
        for c in checks:
            w.writerow(list(c) + [""] * (3 - len(c)))
        w.writerow(["result", "PASS" if not errors else "FAIL", "", ""])

    print(f"Issue #74 regression checks")
    for c in checks:
        print(f"  {c}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
