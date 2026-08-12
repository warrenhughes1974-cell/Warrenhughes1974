"""Issue 104 — Validated Advance Loan Pilot Cohort.

Controlled back-out of LifePRO advance-interest gross-up for an allowlisted
policy set only. Non-cohort loans keep Issue #32 LOAN_BALANCE → MLOANPRIN/BAL.

Flag: QLA_ISSUE104_VALIDATED_LOAN_BACKOUT (default ON; set 0 to disable).
"""
from __future__ import annotations

import csv
import os
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from typing import Any

from qla_core.normalize_utils import format_qladmin_mpolicy, normalize

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST_PATH = (
    _REPO_ROOT
    / "Issue_Log_Items"
    / "Issue_104"
    / "Issue_104_Validated_Advance_Loans.csv"
)
APPROVED_STATUSES = frozenset({"EXACT", "ROUNDING"})
MONETARY_TOLERANCE = Decimal("0.02")


def issue104_loan_pilot_enabled() -> bool:
    """Default ON for the approved pilot; set QLA_ISSUE104_VALIDATED_LOAN_BACKOUT=0 to rollback."""
    return (os.environ.get("QLA_ISSUE104_VALIDATED_LOAN_BACKOUT", "1").strip() or "1") != "0"


def _money(val: Any) -> Decimal | None:
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if not s or s.lower() in {"nan", "none"} or set(s) <= {"-", "."}:
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def interest_rate_fraction(val: Any) -> Decimal | None:
    """Return LifePRO INTEREST_RATE as a fraction (0.05 for 5%)."""
    rate = _money(val)
    if rate is None:
        return None
    if rate < 0:
        return None
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


def round_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def load_issue104_allowlist(path: str | Path | None = None) -> dict[str, str]:
    """Return {MPOLICY: VALIDATION_STATUS} for EXACT/ROUNDING rows only."""
    allow_path = Path(path) if path else DEFAULT_ALLOWLIST_PATH
    if not allow_path.is_file():
        return {}
    out: dict[str, str] = {}
    with allow_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            status = normalize(row.get("VALIDATION_STATUS", ""))
            if status not in APPROVED_STATUSES:
                continue
            mp = format_qladmin_mpolicy(row.get("MPOLICY") or row.get("SOURCE_POLICY") or "")
            if not mp:
                continue
            out[mp] = status
    return out


def runtime_formula_ok(
    *,
    orig_loan_amount: Any,
    loan_amt_added: Any,
    loan_balance: Any,
    interest_rate: Any,
    tolerance: Decimal = MONETARY_TOLERANCE,
) -> tuple[bool, Decimal | None, str]:
    """
    Re-validate advance-interest identity on the current source row.

    Check 1: ORIG + ADDED ≈ LOAN_BALANCE
    Check 2: LOAN_BALANCE × (1 - rate) ≈ ORIG_LOAN_AMOUNT
    """
    orig = _money(orig_loan_amount)
    added = _money(loan_amt_added)
    bal = _money(loan_balance)
    rate = interest_rate_fraction(interest_rate)
    if None in (orig, added, bal, rate):
        return False, None, "MISSING_REQUIRED_SOURCE_FIELDS"
    if bal <= 0:
        return False, None, "NON_POSITIVE_LOAN_BALANCE"
    check1 = abs((orig + added) - bal)
    if check1 > tolerance:
        return False, None, f"CHECK1_FAIL_DIFF={check1}"
    backed = round_money(bal * (Decimal("1") - rate))
    check2 = abs(backed - orig)
    if check2 > tolerance:
        return False, None, f"CHECK2_FAIL_DIFF={check2}"
    return True, backed, "OK"


def apply_issue104_pilot_backout(
    *,
    mpolicy: str,
    source_row: dict[str, Any] | Any,
    current_prin: str,
    current_bal: str,
    allowlist: dict[str, str] | None = None,
    enabled: bool | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """
    Maybe replace MLOANPRIN/MLOANBAL with backed-out balance.

    Returns (prin, bal, audit_dict).
    """
    audit: dict[str, Any] = {
        "MPOLICY": mpolicy,
        "PILOT_ELIGIBLE": "N",
        "PILOT_APPLIED": "N",
        "REASON": "NOT_ENABLED_OR_NOT_ELIGIBLE",
        "GROSS_BALANCE": current_bal,
        "ADJUSTED_BALANCE": "",
        "DIFFERENCE_REMOVED": "",
        "VALIDATION_STATUS": "",
    }
    if enabled is None:
        enabled = issue104_loan_pilot_enabled()
    if not enabled:
        audit["REASON"] = "FLAG_DISABLED"
        return current_prin, current_bal, audit

    allow = allowlist if allowlist is not None else load_issue104_allowlist()
    mp = format_qladmin_mpolicy(mpolicy)
    if not mp or mp not in allow:
        audit["REASON"] = "NOT_ON_ALLOWLIST"
        return current_prin, current_bal, audit

    audit["PILOT_ELIGIBLE"] = "Y"
    audit["VALIDATION_STATUS"] = allow[mp]
    get = source_row.get if hasattr(source_row, "get") else lambda k, d="": d
    ok, backed, reason = runtime_formula_ok(
        orig_loan_amount=get("ORIG_LOAN_AMOUNT", ""),
        loan_amt_added=get("LOAN_AMT_ADDED", ""),
        loan_balance=get("LOAN_BALANCE", ""),
        interest_rate=get("INTEREST_RATE", ""),
    )
    if not ok or backed is None:
        audit["REASON"] = f"RUNTIME_FORMULA_FAIL:{reason}"
        return current_prin, current_bal, audit

    adjusted = f"{backed:.2f}"
    gross = _money(get("LOAN_BALANCE", current_bal))
    diff = "" if gross is None else f"{(gross - backed):.2f}"
    audit.update(
        {
            "PILOT_APPLIED": "Y",
            "REASON": "APPLIED",
            "GROSS_BALANCE": f"{gross:.2f}" if gross is not None else current_bal,
            "ADJUSTED_BALANCE": adjusted,
            "DIFFERENCE_REMOVED": diff,
            "ORIG_LOAN_AMOUNT": str(get("ORIG_LOAN_AMOUNT", "")).strip(),
            "LOAN_AMT_ADDED": str(get("LOAN_AMT_ADDED", "")).strip(),
            "INTEREST_RATE": str(get("INTEREST_RATE", "")).strip(),
        }
    )
    return adjusted, adjusted, audit
