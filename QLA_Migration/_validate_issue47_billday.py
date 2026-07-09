"""
Issue #47 — validate quikmstr.MBILLDAY zero fallback from PAID_TO_DATE.

Checks (against Output/quikmstr.csv + Source PPOLC + crosswalk):
1. 018187C → MBILLDAY == 28
2. Non-zero POLICY_BILL_DAY (#21B) preserved on sample policies
3. Every former source-zero bill day equals Paid-To day (or still 0 if unparseable)
4. Non-zero source bill days unchanged vs POLICY_BILL_DAY

Exit 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

MIG = Path(__file__).resolve().parent
ROOT = MIG.parent
OUT = MIG / "Output" / "quikmstr.csv"
SRC = MIG / "Source" / "PPOLC_PolicyMaster_Extract_20260630.csv"
CW = MIG / "Mapping" / "Master_Crosswalk.csv"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_47" / "evidence"


def _norm_day(v) -> str:
    s = str(v).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s in ("", "nan", "None", "NaN"):
        return ""
    try:
        return str(int(float(s)))
    except (ValueError, TypeError):
        return s


def _day_from_yyyymmdd(s) -> str:
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    if len(digits) >= 8:
        try:
            return str(int(digits[6:8]))
        except (ValueError, TypeError):
            return ""
    return ""


def main() -> int:
    errors: list[str] = []
    if not OUT.is_file():
        print(f"FAIL: missing {OUT}")
        return 1
    if not SRC.is_file():
        print(f"FAIL: missing {SRC}")
        return 1

    qm = pd.read_csv(OUT, dtype=str, low_memory=False).fillna("")
    pp = pd.read_csv(SRC, dtype=str, low_memory=False, encoding="latin-1").fillna("")
    cw = pd.read_csv(CW, dtype=str).fillna("")
    qm.columns = [str(c).strip().upper() for c in qm.columns]
    pp["PN"] = pp["POLICY_NUMBER"].astype(str).str.strip()
    cw["Old_Value"] = cw["Old_Value"].astype(str).str.strip()
    cw["New_Value"] = cw["New_Value"].astype(str).str.strip()
    qm["MP"] = qm["MPOLICY"].astype(str).str.strip()

    m = (
        pp.merge(cw, left_on="PN", right_on="Old_Value", how="inner")
        .merge(qm, left_on="New_Value", right_on="MP", how="inner")
    )
    m["bd_src"] = m["POLICY_BILL_DAY"].map(_norm_day)
    m["mb"] = m["MBILLDAY"].map(_norm_day)
    m["paid_day"] = m["PAID_TO_DATE"].map(_day_from_yyyymmdd)
    m["expected"] = m.apply(
        lambda r: r["bd_src"] if r["bd_src"] not in ("", "0") else (r["paid_day"] or "0"),
        axis=1,
    )

    # 1) BA sample
    row = m.loc[m["New_Value"] == "018187C"]
    if row.empty:
        errors.append("018187C missing from joined output")
    else:
        got = row.iloc[0]["mb"]
        if got != "28":
            errors.append(f"018187C MBILLDAY={got!r} expected 28")

    # 2) #21B preserve samples
    preserve = {
        "010713704C": "15",
        "010765930C": "28",
        "010718309C": "22",
        "010818663C": "12",
    }
    for pol, expect in preserve.items():
        r = m.loc[m["New_Value"] == pol]
        if r.empty:
            errors.append(f"{pol} missing")
            continue
        got = r.iloc[0]["mb"]
        if got != expect:
            errors.append(f"{pol} MBILLDAY={got!r} expected {expect} (#21B)")

    # 3) Fleet: mb == expected
    bad = m[m["mb"] != m["expected"]]
    if len(bad):
        errors.append(f"fleet MBILLDAY mismatches vs expected: {len(bad)}")
        sample = bad[["New_Value", "POLICY_BILL_DAY", "PAID_TO_DATE", "MBILLDAY", "expected"]].head(10)
        print("Mismatch sample:\n", sample.to_string(index=False))

    zeros_src = m[m["bd_src"].isin(["", "0"])]
    still_zero = zeros_src[zeros_src["mb"].isin(["", "0"])]
    nonzero_src = m[~m["bd_src"].isin(["", "0"])]
    nonzero_ok = int((nonzero_src["mb"] == nonzero_src["bd_src"]).sum())

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(
        [
            {"metric": "matched_rows", "value": len(m)},
            {"metric": "source_zero_bill_day", "value": len(zeros_src)},
            {"metric": "source_zero_still_mbillday_zero", "value": len(still_zero)},
            {"metric": "nonzero_parity_ok", "value": nonzero_ok},
            {"metric": "nonzero_total", "value": len(nonzero_src)},
            {"metric": "fleet_mismatches", "value": len(bad)},
            {"metric": "018187C_mbillday", "value": row.iloc[0]["mb"] if len(row) else ""},
        ]
    )
    summary.to_csv(EVIDENCE / "issue47_validation_summary.csv", index=False)
    if len(bad):
        bad.head(100).to_csv(EVIDENCE / "issue47_validation_mismatches.csv", index=False)

    print(summary.to_string(index=False))
    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS: Issue #47 MBILLDAY fallback validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
