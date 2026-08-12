#!/usr/bin/env python3
"""Full-batch smoke: Issue 104 validated advance-loan pilot cohort.

Cut-agnostic. Does not require all historical 176 policies to exist.
Fails only when:
  - non-allowlisted loans changed vs gross LOAN_BALANCE mapping, or
  - allowlisted policies are adjusted without passing runtime formula checks.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.issue104_loan_pilot import (  # noqa: E402
    DEFAULT_ALLOWLIST_PATH,
    issue104_loan_pilot_enabled,
    load_issue104_allowlist,
    runtime_formula_ok,
)
from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize  # noqa: E402
from qla_core.quikloan_converter import (  # noqa: E402
    _DATE_COLS,
    load_derivation_rules,
    load_ploan_extract,
    parse_ploan_date,
    sanitize_ploan_rows,
    select_latest_ploan_row_per_policy,
)

OUT = ROOT / "QLA_Migration" / "Output" / "quikloan.csv"
SRC = ROOT / "QLA_Migration" / "Source"


def _latest_active_by_mpolicy() -> dict[str, dict]:
    path, _ = resolve_table_source(str(SRC), "quikloan")
    if not path:
        return {}
    rules = load_derivation_rules()
    raw = load_ploan_extract(path)
    valid, _ = sanitize_ploan_rows(raw)
    for col in _DATE_COLS:
        if col in valid.columns:
            valid[f"_{col}_TS"] = valid[col].map(parse_ploan_date)
    latest = select_latest_ploan_row_per_policy(valid, rules)
    out: dict[str, dict] = {}
    for _, row in latest.iterrows():
        if str(row.get("_LATEST_BALANCE_CLASS", "")) != "ACTIVE_CANDIDATE":
            continue
        mp = format_qladmin_mpolicy(row.get("POLICY_NUMBER", ""))
        if mp:
            out[mp] = row.to_dict()
    return out


def main() -> int:
    summary = {
        "approved_cohort_encountered": 0,
        "cohort_adjusted": 0,
        "runtime_formula_failures": 0,
        "non_cohort_loans_changed": 0,
        "missing_required_source_fields": 0,
    }
    failures: list[str] = []

    if not OUT.is_file():
        # QuikLoan emit is gated; missing file is not an Issue 104 failure when emit is off.
        if os_env_quikloan_enabled():
            print("FAIL: quikloan.csv missing while QuikLoan emit is enabled")
            return 1
        print("PASS: Issue 104 smoke skipped — quikloan.csv not emitted this run")
        _print(summary)
        return 0

    if not issue104_loan_pilot_enabled():
        print("PASS: Issue 104 pilot flag disabled (QLA_ISSUE104_VALIDATED_LOAN_BACKOUT=0)")
        _print(summary)
        return 0

    allow = load_issue104_allowlist(DEFAULT_ALLOWLIST_PATH)
    if not allow:
        print(f"FAIL: missing/empty Issue 104 allowlist at {DEFAULT_ALLOWLIST_PATH}")
        return 1

    ql = pd.read_csv(OUT, dtype=str).fillna("")
    ql.columns = [str(c).strip().upper() for c in ql.columns]
    for col in ("MPOLICY", "MLOANPRIN", "MLOANBAL"):
        if col not in ql.columns:
            print(f"FAIL: quikloan missing {col}")
            return 1

    source_by_mp = _latest_active_by_mpolicy()
    for _, row in ql.iterrows():
        mp = format_qladmin_mpolicy(row.get("MPOLICY", ""))
        if not mp:
            continue
        prin = str(row.get("MLOANPRIN", "")).strip()
        bal = str(row.get("MLOANBAL", "")).strip()
        src = source_by_mp.get(mp)
        if src is None:
            continue
        gross = src.get("LOAN_BALANCE", "")
        try:
            gross_s = f"{float(str(gross).replace(',', '').strip()):.2f}"
        except Exception:
            gross_s = str(gross).strip()

        if mp in allow:
            summary["approved_cohort_encountered"] += 1
            ok, backed, reason = runtime_formula_ok(
                orig_loan_amount=src.get("ORIG_LOAN_AMOUNT"),
                loan_amt_added=src.get("LOAN_AMT_ADDED"),
                loan_balance=src.get("LOAN_BALANCE"),
                interest_rate=src.get("INTEREST_RATE"),
            )
            if "MISSING_REQUIRED" in reason:
                summary["missing_required_source_fields"] += 1
            if not ok:
                summary["runtime_formula_failures"] += 1
                # Must NOT be adjusted when formula fails.
                if prin != gross_s or bal != gross_s:
                    failures.append(
                        f"{mp}: allowlisted but runtime fail ({reason}) yet balances adjusted"
                    )
                continue
            expect = f"{backed:.2f}"
            if prin == expect and bal == expect:
                summary["cohort_adjusted"] += 1
            else:
                failures.append(
                    f"{mp}: allowlisted+formula OK but MLOANPRIN/BAL={prin}/{bal} expected {expect}"
                )
        else:
            # Non-cohort must remain on gross LOAN_BALANCE mapping.
            if prin != gross_s or bal != gross_s:
                summary["non_cohort_loans_changed"] += 1
                if summary["non_cohort_loans_changed"] <= 8:
                    failures.append(
                        f"{mp}: non-cohort changed prin/bal={prin}/{bal} gross={gross_s}"
                    )

    _print(summary)
    if summary["non_cohort_loans_changed"] > 0:
        failures.append(
            f"non-cohort loans changed={summary['non_cohort_loans_changed']}"
        )
    if failures:
        for f in failures[:20]:
            print(f"FAIL detail: {f}")
        print("FAIL: Issue 104 validated advance-loan pilot smoke")
        return 1

    print(
        "PASS: Issue 104 loan pilot smoke — "
        f"encountered={summary['approved_cohort_encountered']} "
        f"adjusted={summary['cohort_adjusted']} "
        f"runtime_fail={summary['runtime_formula_failures']} "
        f"non_cohort_changed=0"
    )
    return 0


def os_env_quikloan_enabled() -> bool:
    import os

    return os.environ.get("QLA_ENABLE_QUIKLOAN_EMIT", "").strip() == "1" and (
        os.environ.get("QLA_QUIKLOAN_WRITE_OUTPUT", "").strip() == "1"
    )


def _print(summary: dict) -> None:
    print("| Issue 104 Loan Pilot Check     | Result |")
    print("| ------------------------------ | ------ |")
    print(f"| Approved cohort encountered    | {summary['approved_cohort_encountered']:<6} |")
    print(f"| Cohort adjusted                | {summary['cohort_adjusted']:<6} |")
    print(f"| Runtime formula failures       | {summary['runtime_formula_failures']:<6} |")
    print(f"| Non-cohort loans changed       | {summary['non_cohort_loans_changed']:<6} |")
    print(f"| Missing required source fields | {summary['missing_required_source_fields']:<6} |")


if __name__ == "__main__":
    raise SystemExit(main())
