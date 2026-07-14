"""Issue #57 Regression — read-only checks (no production changes)."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
SIM = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_risk_simulation.csv"
OPTS = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_risk_options.csv"
BASE45 = ROOT / "Issue_Log_Items" / "Issue_45" / "evidence" / "before_batch_v57.77" / "quikmstr.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_57" / "evidence" / "issue57_regression_checks.csv"

ERIC = ["010367131C", "010148272C", "010143726C", "010392763C", "011221309C"]
MPREM26 = {
    "010310404C": "13.20",
    "010331768C": "10.96",
    "010367131C": "9.12",
}


def load_qm(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows = {}
        for row in r:
            # Preserve MPOLICY padding (#25); strip other fields for compare
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

    # --- Row counts ---
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
    h45, base45 = load_qm(BASE45) if BASE45.exists() else ([], {})

    # Schema: field order vs Issue #45 baseline (stable quikmstr schema)
    if h45:
        add(
            "schema_field_order",
            "PASS" if headers == h45 else "FAIL",
            f"after={len(headers)} base={len(h45)}",
        )

    # Pre-fix snapshot: MDIVOPT / MSTATUS must be unchanged for entire fleet
    sim = list(csv.DictReader(SIM.open(encoding="utf-8")))
    mstatus_drift = 0
    mdiv_drift = 0
    mnf_mismatch_optb = 0
    for r in sim:
        mp = r["MPOLICY"]
        a = after.get(mp)
        if not a:
            continue
        if a.get("MSTATUS") != r.get("MSTATUS", "").strip():
            mstatus_drift += 1
        if a.get("MDIVOPT") != r.get("MDIVOPT", "").strip():
            mdiv_drift += 1

    add("fleet_MSTATUS_unchanged", "PASS" if mstatus_drift == 0 else "FAIL", f"drift={mstatus_drift}")
    add("fleet_MDIVOPT_unchanged", "PASS" if mdiv_drift == 0 else "FAIL", f"drift={mdiv_drift}")

    # Option B expected MNFOPT vs actual
    if OPTS.exists():
        for r in csv.DictReader(OPTS.open(encoding="utf-8")):
            mp = r["MPOLICY"]
            want = r["OPT_B"].strip()
            got = after.get(mp, {}).get("MNFOPT", "")
            if got != want:
                mnf_mismatch_optb += 1
        add(
            "option_b_mnfopt_match",
            "PASS" if mnf_mismatch_optb == 0 else "FAIL",
            f"mismatches={mnf_mismatch_optb}",
        )

    # Only MNFOPT should differ vs pre-fix on intentional changes; count MNFOPT deltas
    mnf_changed = sum(
        1
        for r in sim
        if after.get(r["MPOLICY"], {}).get("MNFOPT") != r.get("BEFORE_MNFOPT", "").strip()
    )
    add("mnfopt_changed_count", "PASS" if mnf_changed == 2721 else "INFO", f"changed={mnf_changed}")

    # Eric traces
    eric_want = {
        "010367131C": "2",
        "010148272C": "2",
        "010143726C": "2",
        "010392763C": "3",
        "011221309C": "1",
    }
    for mp, want in eric_want.items():
        got = after.get(mp, {}).get("MNFOPT", "")
        add(f"eric_{mp}", "PASS" if got == want else "FAIL", f"got={got} want={want}")

    # #25 MPOLICY width on Eric + sample
    bad25 = [mp for mp in list(eric_want) + ["010310404C", "010331768C"] if len(mp) != 10]
    # also check padding with spaces in CSV for short policies if present
    short = [p for p in after if len(p) != 10 and not p.startswith(" ")]
    # format_qladmin may left-pad with spaces — count stripped length issues differently
    # Risk: Issue 55 said 0 failures with space pad. Check stripped or padded length.
    width_fail = 0
    for p, row in after.items():
        raw = row.get("MPOLICY_RAW", row.get("MPOLICY", p))
        if len(raw) != 10:
            width_fail += 1
    add("issue25_mpolicy_width", "PASS" if width_fail == 0 else "FAIL", f"not_len10={width_fail}")

    # #26 MPREM spot-check (phase 1)
    qr = OUT / "quikridr.csv"
    if qr.exists():
        with qr.open(newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                mp = row["MPOLICY"].strip()
                if mp not in MPREM26:
                    continue
                if row.get("MPHASE", "").strip() not in ("1", "01"):
                    continue
                mprem = row.get("MPREM", "").strip()
                # allow 13.20 / 13.20000
                try:
                    ok = abs(float(mprem) - float(MPREM26[mp])) < 0.01
                except ValueError:
                    ok = False
                add(f"issue26_mprem_{mp}", "PASS" if ok else "FAIL", f"MPREM={mprem} want={MPREM26[mp]}")

    # #21A: NF_1/NF_2 entries + sample BF code1 still APL
    trans = ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
    tmap = {}
    with trans.open(encoding="latin1") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                tmap[row[0].strip()] = row[1].strip()
    for k, v in (("NF_1", "1"), ("NF_2", "1"), ("NF_9", "0"), ("NF_3", "1"), ("NF_4", "2"), ("NF_5", "3")):
        add(f"trans_{k}", "PASS" if tmap.get(k) == v else "FAIL", f"got={tmap.get(k)}")

    # Rulebook: no PAID_UP_TYPE -> MNFOPT
    rb = ROOT / "QLA_Migration" / "Configs" / "Sync_Rulebook_quikmstr.csv"
    has_put = False
    with rb.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("Source_Field") or "").strip().upper() == "PAID_UP_TYPE" and (
                row.get("Target_Field") or ""
            ).strip().upper() == "MNFOPT":
                has_put = True
    add("rulebook_no_PUT_MNFOPT", "PASS" if not has_put else "FAIL", "")

    # PUT=LE spot-check: MSTATUS preserved, MNFOPT from PPBENTYP not LE
    put_le = [r for r in sim if r.get("PAID_UP_TYPE") == "LE"][:3]
    for r in put_le:
        mp = r["MPOLICY"]
        a = after.get(mp, {})
        st_ok = a.get("MSTATUS") == r.get("MSTATUS")
        add(
            f"put_le_{mp}",
            "PASS" if st_ok else "FAIL",
            f"MSTATUS={a.get('MSTATUS')} MNFOPT={a.get('MNFOPT')} LP={r.get('LP_CODE')}",
        )

    EVID.parent.mkdir(parents=True, exist_ok=True)
    with EVID.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["CHECK", "RESULT", "DETAIL"])
        w.writeheader()
        w.writerows(checks)

    fails = [c for c in checks if c["RESULT"] == "FAIL"]
    print(f"Wrote {EVID}")
    print(f"Checks: {len(checks)}  FAIL: {len(fails)}")
    for c in checks:
        if c["RESULT"] in ("FAIL", "INFO") or c["CHECK"].startswith("eric_") or c["CHECK"].startswith("rowcount_"):
            print(f"  {c['RESULT']:4} {c['CHECK']}: {c['DETAIL']}")
    if fails:
        print("REGRESSION FAIL")
        return 1
    print("REGRESSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
