#!/usr/bin/env python3
"""Focused validator — Issue #135 surgical payees for 9011156655C."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CLMS = ROOT / "QLA_Migration" / "Output" / "quikclms.csv"
CLMP = ROOT / "QLA_Migration" / "Output" / "quikclmp.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
META = EVID / "issue135_9011156655C_apply_meta.json"
COHORT_META = EVID / "issue135_match_cso_zero_payee_apply_meta.json"
OUT = EVID / "issue135_9011156655C_validation.json"

POL = "9011156655C"
TOL = 0.01
# QLAdmin indexes payees on MPOLICY+MPHASE+MSEQ matching the claim header (MSEQ=0).
# Duplicate MSEQ=0 keys are required for multi-payee display.
EXPECTED = [
    {"name": "LINVILLE L BRASWELL", "amount": 1286.42},
    {"name": "CHERI ROSE BRASWELL", "amount": 1286.41},
    {"name": "DANIEL L BRASWELL JR", "amount": 1286.42},
    {"name": "ROBERT C BRASWELL", "amount": 1286.42},
]


def _strip(v) -> str:
    return "" if v is None else str(v).strip()


def _money(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    checks: list[dict] = []
    fails = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal fails
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            fails += 1

    clms = pd.read_csv(CLMS, dtype=str).fillna("")
    clmp = pd.read_csv(CLMP, dtype=str).fillna("")
    hdr = clms[clms["MPOLICY"].map(_strip) == POL]
    pay = clmp[clmp["MPOLICY"].map(_strip) == POL].copy()

    check("HEADER_EXISTS", len(hdr) >= 1, f"rows={len(hdr)}")
    if len(hdr):
        h = hdr.iloc[0]
        check("MPAID_5145_67", abs(_money(h["MPAID"]) - 5145.67) <= TOL, h.get("MPAID", ""))
        check("MFACE_5000", abs(_money(h["MFACE"]) - 5000.0) <= TOL, h.get("MFACE", ""))
        check("NETDB_5000", abs(_money(h["NETDB"]) - 5000.0) <= TOL, h.get("NETDB", ""))
        check("MINTAMT_ZERO", abs(_money(h["MINTAMT"])) <= TOL, h.get("MINTAMT", ""))
        check("PREMIUM_ZERO", abs(_money(h["PREMIUM"])) <= TOL, h.get("PREMIUM", ""))
        check("CLAIMSTAT_2", _strip(h["CLAIMSTAT"]) == "2", h.get("CLAIMSTAT", ""))
        check("CLAIMNUM_RC", _strip(h["CLAIMNUM"]) == "RC-9011156655", h.get("CLAIMNUM", ""))

    check("EXACTLY_4_PAYEES", len(pay) == 4, f"count={len(pay)}")
    if len(hdr) and len(pay):
        header_mseq = _strip(hdr.iloc[0].get("MSEQ", "0")) or "0"
        check(
            "ALL_PAYEE_MSEQ_MATCH_HEADER",
            all(_strip(x) == header_mseq for x in pay["MSEQ"]),
            f"header={header_mseq} payee_mseqs={sorted(set(pay['MSEQ'].map(_strip)))}",
        )
    if len(pay):
        amt_sum = round(pay["MAMOUNT"].map(_money).sum(), 2)
        check("PAYEE_SUM_5145_67", abs(amt_sum - 5145.67) <= TOL, f"sum={amt_sum}")
        check("MCHECKNO_BLANK_OR_0", all(_strip(x) in ("", "0") for x in pay["MCHECKNO"]), "")
        for exp in EXPECTED:
            row = pay[
                (pay["MPAYNAME"].map(_strip).str.upper() == exp["name"].upper())
                & (pay["MAMOUNT"].map(_money).sub(exp["amount"]).abs() <= TOL)
            ]
            check(f"PAYEE_{exp['name'].split()[0]}_EXISTS", len(row) >= 1, f"n={len(row)}")
            if len(row):
                r = row.iloc[0]
                check(f"PAYEE_{exp['name'].split()[0]}_MPHASE", _strip(r["MPHASE"]) == "1", r.get("MPHASE", ""))

    # Unrelated row stability via apply meta when present.
    # Prefer cohort meta after fleet expansion; fall back to single-policy meta.
    # Later surrender backfill may add more clmp rows — require at least the meta total.
    meta_path = COHORT_META if COHORT_META.is_file() else META
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        expected_total = int(meta.get("before_clmp_rows", 0)) + int(meta.get("rows_added", 0))
        check(
            "CLMP_TOTAL_DELTA_MATCHES_META",
            int(len(clmp)) >= expected_total,
            f"len={len(clmp)} expected>={expected_total} meta={meta_path.name}",
        )
        check("QUIKCLMS_NOT_MUTATED_FLAG", meta.get("quikclms_mutated") is False, str(meta.get("quikclms_mutated")))
        check(
            "HEADER_MONEY_UNCHANGED_FLAG",
            bool(meta.get("header_money_unchanged")),
            str(meta.get("header_money_unchanged")),
        )
        if meta_path == COHORT_META:
            check(
                "GOLDEN_PAYEES_IN_COHORT_META",
                int(meta.get("golden_9011156655C_payees", 0) or 0) == 4,
                str(meta.get("golden_9011156655C_payees")),
            )
    else:
        check("APPLY_META_PRESENT", False, "missing apply meta")

    result = {
        "policy": POL,
        "reason": "MATCH_CSO_EXISTING_HEADER_ZERO_PAYEE",
        "pass": fails == 0,
        "fail_count": fails,
        "checks": checks,
        "payee_rows": int(len(pay)),
        "clmp_total_rows": int(len(clmp)),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "fail_count": fails, "checks": checks}, indent=2))
    print("Wrote", OUT)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
