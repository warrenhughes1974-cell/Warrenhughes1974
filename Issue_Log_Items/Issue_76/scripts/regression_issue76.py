"""Issue #76 Regression — read-only fleet checks (no production changes)."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
RISK = ROOT / "Issue_Log_Items" / "Issue_76" / "evidence" / "issue76_risk_phase1_simulation.csv"
BASE60_HDR = ROOT / "Issue_Log_Items" / "Issue_60" / "evidence" / "quikridr_pre_v5785_baseline.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_76" / "evidence" / "issue76_regression_checks.csv"

MPREM26 = {
    "010310404C": "13.20",
    "010331768C": "10.96",
    "010367131C": "9.12",
}
PUA_SAMPLE = "010407670C"
ACTIVE = "010367131C"
SYS_YEAR = datetime.now().year


def n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def ymd(v: object) -> str:
    d = "".join(c for c in n(v) if c.isdigit())
    return d[:8] if len(d) >= 8 else ""


def prem_match(got: str, exp: str) -> bool:
    try:
        return abs(float(got or 0) - float(exp)) < 0.001
    except ValueError:
        return got == exp


def load_ridr() -> tuple[list[str], dict[tuple[str, str], dict[str, str]]]:
    with (OUT / "quikridr.csv").open(newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows: dict[tuple[str, str], dict[str, str]] = {}
        for row in r:
            key = (n(row.get("MPOLICY")), n(row.get("MPHASE")))
            rows[key] = {k: n(v) for k, v in row.items()}
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
    }
    for table, exp in expected_counts.items():
        p = OUT / f"{table}.csv"
        if not p.exists():
            add(f"rowcount_{table}", "FAIL", "missing")
            continue
        with p.open(encoding="utf-8", errors="replace") as f:
            count = sum(1 for _ in f) - 1
        add(f"rowcount_{table}", "PASS" if count == exp else "FAIL", f"got={count} exp={exp}")

    headers, ridr = load_ridr()
    if BASE60_HDR.exists():
        with BASE60_HDR.open(newline="", encoding="utf-8", errors="replace") as f:
            base_hdr = list(csv.DictReader(f).fieldnames or [])
        add(
            "quikridr_schema_headers",
            "PASS" if headers == base_hdr else "FAIL",
            f"cols={len(headers)} base={len(base_hdr)}",
        )

    keys60: set[tuple[str, str]] = set()
    if BASE60_HDR.exists():
        with BASE60_HDR.open(newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                keys60.add((n(row.get("MPOLICY")), n(row.get("MPHASE"))))
    cur_keys = set(ridr.keys())
    add(
        "quikridr_key_identity",
        "PASS" if keys60 == cur_keys else "FAIL",
        f"missing={len(keys60-cur_keys)} orphan={len(cur_keys-keys60)}",
    )

    blank_mridr = sum(1 for r in ridr.values() if not n(r.get("MRIDRID")))
    add("blank_MRIDRID", "PASS" if blank_mridr == 0 else "FAIL", f"count={blank_mridr}")

    mstr = {
        n(r["MPOLICY"]): r
        for r in csv.DictReader(
            (OUT / "quikmstr.csv").open(newline="", encoding="utf-8", errors="replace")
        )
    }

    # Risk-backed candidate collateral: payup/mlast changed; MEFFDATE/MPLAN untouched
    risk_rows = list(csv.DictReader(RISK.open(newline="", encoding="utf-8", errors="replace")))
    payup_ok = mlast_ok = meff_ok = plan_ok = 0
    for row in risk_rows:
        pol = n(row.get("MPOLICY"))
        cur = ridr.get((pol, "1"))
        if not cur:
            add("risk_candidate_row", "FAIL", f"missing {pol}")
            break
        if ymd(cur.get("MPAYUP")) != ymd(row.get("MPAYUP_AFTER")):
            payup_ok += 1
        if n(cur.get("MLASTANN")) != n(row.get("MLASTANN_AFTER_SYS")):
            mlast_ok += 1
        if ymd(cur.get("MEFFDATE")) != ymd(row.get("MEFFDATE")):
            meff_ok += 1
        if n(cur.get("MPLAN")) != n(row.get("MPLAN")):
            plan_ok += 1
    else:
        add("candidate_MPAYUP_vs_risk", "PASS" if payup_ok == 0 else "FAIL", f"bad={payup_ok}")
        add("candidate_MLASTANN_vs_risk", "PASS" if mlast_ok == 0 else "FAIL", f"bad={mlast_ok}")
        add("candidate_MEFFDATE_unchanged", "PASS" if meff_ok == 0 else "FAIL", f"bad={meff_ok}")
        add("candidate_MPLAN_unchanged", "PASS" if plan_ok == 0 else "FAIL", f"bad={plan_ok}")

    # Non-candidate: issue76 formula not applied
    false_override = 0
    for r in ridr.values():
        pol = n(r.get("MPOLICY"))
        if n(r.get("MPHASE")) != "1":
            continue
        st = n(mstr.get(pol, {}).get("MSTATUS"))
        if st in ("44", "45"):
            continue
        paidto = ymd(mstr.get(pol, {}).get("MPAIDTO"))
        payup = ymd(r.get("MPAYUP"))
        mlast = n(r.get("MLASTANN"))
        if paidto and payup == paidto and mlast == str(SYS_YEAR - int(paidto[:4])):
            false_override += 1
    add("non_candidate_false_override", "PASS" if false_override == 0 else "FAIL", f"count={false_override}")

    # #60 PUA later phases on ETI/RPU
    pua_bad = 0
    pua_n = 0
    for r in ridr.values():
        pol = n(r.get("MPOLICY"))
        ph = n(r.get("MPHASE"))
        if ph == "1":
            continue
        st = n(mstr.get(pol, {}).get("MSTATUS"))
        if st not in ("44", "45"):
            continue
        plan = n(r.get("MPLAN")).upper()
        if not (plan.endswith("PA") or "PUA" in plan):
            continue
        pua_n += 1
        if ymd(r.get("MPAYUP")) != ymd(r.get("MEFFDATE")):
            pua_bad += 1
    add("pua_phase_gt1_MPAYUP", "PASS" if pua_bad == 0 else "FAIL", f"checked={pua_n} bad={pua_bad}")

    p2 = ridr.get((PUA_SAMPLE, "2"))
    if not p2:
        add("pua_sample_phase2", "FAIL", "missing")
    elif ymd(p2.get("MPAYUP")) != ymd(p2.get("MEFFDATE")):
        add("pua_sample_phase2", "FAIL", f"payup={ymd(p2.get('MPAYUP'))}")
    else:
        add("pua_sample_phase2", "PASS", PUA_SAMPLE)

    active = ridr.get((ACTIVE, "1"))
    if active and n(mstr.get(ACTIVE, {}).get("MSTATUS")) == "22":
        paidto = ymd(mstr[ACTIVE].get("MPAIDTO"))
        if ymd(active.get("MPAYUP")) == paidto:
            add("active_control_payup", "FAIL", "incorrectly set to paidto")
        else:
            add("active_control_payup", "PASS", ACTIVE)
    else:
        add("active_control_payup", "FAIL", "missing control")

    for pol, exp in MPREM26.items():
        r = ridr.get((pol, "1"))
        got = n(r.get("MPREM")) if r else ""
        add(f"mprem_{pol}", "PASS" if prem_match(got, exp) else "FAIL", f"got={got} exp={exp}")

    i72 = mstr.get(PUA_SAMPLE, {})
    add(
        "issue72_sample_mnfopt",
        "PASS" if n(i72.get("MSTATUS")) == "45" and n(i72.get("MNFOPT")) == "3" else "FAIL",
        f"st={n(i72.get('MSTATUS'))} nfo={n(i72.get('MNFOPT'))}",
    )

    EVID.parent.mkdir(parents=True, exist_ok=True)
    with EVID.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["CHECK", "RESULT", "DETAIL"])
        w.writeheader()
        w.writerows(checks)

    print(f"regression_issue76 checks={len(checks)} errors={len(errors)}")
    for c in checks:
        print(f"  [{c['RESULT']}] {c['CHECK']}: {c['DETAIL']}")
    if errors:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
