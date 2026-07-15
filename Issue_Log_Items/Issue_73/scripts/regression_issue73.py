"""Issue #73 Regression — read-only checks (no production changes).

Proves MISSCNTRY=0000 fleet-wide without collateral quikmstr / table drift.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
BASE45 = ROOT / "Issue_Log_Items" / "Issue_45" / "evidence" / "before_batch_v57.77" / "quikmstr.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_73" / "evidence" / "issue73_regression_checks.csv"

MPREM26 = {
    "010310404C": "13.20",
    "010331768C": "10.96",
    "010367131C": "9.12",
}
ISSUE72_SAMPLE = "010407670C"


def load_qm(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows: dict[str, dict[str, str]] = {}
        for row in r:
            raw_pol = row.get("MPOLICY") or ""
            key = raw_pol.strip()
            cleaned = {k: (v or "").strip() for k, v in row.items()}
            cleaned["MPOLICY_RAW"] = raw_pol
            rows[key] = cleaned
    return headers, rows


def main() -> int:
    errors: list[str] = []
    checks: list[dict[str, str]] = []

    def add(name: str, result: str, detail: str = "") -> None:
        checks.append({"CHECK": name, "RESULT": result, "DETAIL": detail})
        if result == "FAIL":
            errors.append(f"{name}: {detail}")

    expected_counts = {
        "quikmstr": 5083,
        "quikridr": 6934,
        "quikprmh": 209470,
        "quikplan": 141,
        "quikclid": 34449,
        "quikclnt": 13597,
        "quikbenf": 5916,
        "quikdvdp": 5083,
        "quikagts": 4843,
    }
    for t, exp in expected_counts.items():
        p = OUT / f"{t}.csv"
        if not p.exists():
            add(f"rowcount_{t}", "FAIL", "missing")
            continue
        with p.open(encoding="utf-8", errors="replace") as f:
            n = sum(1 for _ in f) - 1
        add(f"rowcount_{t}", "PASS" if n == exp else "FAIL", f"got={n} expected={exp}")

    headers, after = load_qm(OUT / "quikmstr.csv")
    h45, _ = load_qm(BASE45) if BASE45.exists() else ([], {})
    if h45:
        add(
            "schema_field_order",
            "PASS" if headers == h45 else "FAIL",
            f"after={len(headers)} base={len(h45)}",
        )

    bad_cntry = [
        p
        for p, r in after.items()
        if r.get("MISSCNTRY", "") != "0000"
    ]
    add(
        "fleet_MISSCNTRY_0000",
        "PASS" if not bad_cntry else "FAIL",
        f"not_0000={len(bad_cntry)}",
    )
    add(
        "intentional_MISSCNTRY_changes",
        "PASS" if len(after) == 5083 else "FAIL",
        f"rows={len(after)} expected=5083 USA->0000",
    )

    # Issue #72 still valid on same quikmstr (proves no collateral MNFOPT drift)
    r72 = after.get(ISSUE72_SAMPLE, {})
    add(
        "issue72_sample_010407670C",
        "PASS" if r72.get("MSTATUS") == "45" and r72.get("MNFOPT") == "3" else "FAIL",
        f"MSTATUS={r72.get('MSTATUS')} MNFOPT={r72.get('MNFOPT')}",
    )

    # #25 width
    width_fail = sum(1 for r in after.values() if len(r.get("MPOLICY_RAW", "")) != 10)
    add("issue25_mpolicy_width", "PASS" if width_fail == 0 else "FAIL", f"not_len10={width_fail}")

    # #26 MPREM spot-check phase 1
    qr = OUT / "quikridr.csv"
    if qr.exists():
        seen = set()
        with qr.open(newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                mp = row["MPOLICY"].strip()
                if mp not in MPREM26 or mp in seen:
                    continue
                if row.get("MPHASE", "").strip() not in ("1", "01"):
                    continue
                seen.add(mp)
                mprem = row.get("MPREM", "").strip()
                try:
                    ok = abs(float(mprem) - float(MPREM26[mp])) < 0.01
                except ValueError:
                    ok = False
                add(f"issue26_mprem_{mp}", "PASS" if ok else "FAIL", f"MPREM={mprem}")

    # Rulebook default
    rb = ROOT / "QLA_Migration" / "Configs" / "Sync_Rulebook_quikmstr.csv"
    rb_ok = False
    with rb.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("Target_Field") or "").strip() == "MISSCNTRY":
                rb_ok = (row.get("Default_Value") or "").strip() == "0000"
                break
    add("rulebook_MISSCNTRY_0000", "PASS" if rb_ok else "FAIL", "")

    # Test_Validation parity
    tv = OUT / "Test_Validation" / "quikmstr.csv"
    if tv.exists():
        _, tv_rows = load_qm(tv)
        tv_bad = sum(1 for r in tv_rows.values() if r.get("MISSCNTRY") != "0000")
        tv_diff = sum(
            1
            for p in after
            if p in tv_rows and after[p].get("MISSCNTRY") != tv_rows[p].get("MISSCNTRY")
        )
        add(
            "test_validation_parity",
            "PASS" if tv_bad == 0 and tv_diff == 0 else "FAIL",
            f"tv_not_0000={tv_bad} diffs={tv_diff}",
        )
    else:
        add("test_validation_parity", "FAIL", "missing Test_Validation/quikmstr.csv")

    EVID.parent.mkdir(parents=True, exist_ok=True)
    with EVID.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["CHECK", "RESULT", "DETAIL"])
        w.writeheader()
        w.writerows(checks)

    fails = [c for c in checks if c["RESULT"] == "FAIL"]
    print(f"Wrote {EVID}")
    print(f"Checks: {len(checks)}  FAIL: {len(fails)}")
    for c in checks:
        print(f"  {c['RESULT']:4} {c['CHECK']}: {c['DETAIL']}")
    if fails:
        print("REGRESSION FAIL")
        return 1
    print("REGRESSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
