"""Policy Data Governance safe transforms for conversion output (not source DBFs).

Records automatic defaults/forced values for an internal audit CSV under Reports/.
"""

from __future__ import annotations

import csv
import os
from typing import Any


_AUDIT_ROWS: list[dict[str, str]] = []


def reset_policy_transform_audit() -> None:
    _AUDIT_ROWS.clear()


def record_policy_transform(
    *,
    table: str,
    record_id: str,
    field: str,
    original: Any,
    converted: Any,
    reason: str,
    rule_id: str,
) -> None:
    _AUDIT_ROWS.append(
        {
            "table": table,
            "record_id": str(record_id or ""),
            "field": field,
            "original_value": "" if original is None else str(original),
            "converted_value": "" if converted is None else str(converted),
            "reason": reason,
            "rule_id": rule_id,
        }
    )


def write_policy_transform_audit(reports_dir: str) -> str | None:
    if not _AUDIT_ROWS:
        return None
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "policy_data_transformation_audit.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "table",
                "record_id",
                "field",
                "original_value",
                "converted_value",
                "reason",
                "rule_id",
            ],
        )
        writer.writeheader()
        writer.writerows(_AUDIT_ROWS)
    return path


def extract_day_from_date_value(raw: Any) -> str:
    """Return calendar day 1–31 as string, or '' if not parseable."""
    if raw is None:
        return ""
    if hasattr(raw, "day"):
        try:
            d = int(raw.day)
            return str(d) if 1 <= d <= 31 else ""
        except Exception:
            return ""
    text = str(raw).strip()
    if not text or text in (".", "None", "nan"):
        return ""
    # YYYYMMDD
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        try:
            d = int(digits[6:8])
            return str(d) if 1 <= d <= 31 else ""
        except ValueError:
            return ""
    # M/D/Y or similar
    for sep in ("/", "-", "."):
        if sep in text:
            parts = text.split(sep)
            if len(parts) >= 2:
                try:
                    d = int(parts[1] if len(parts[0]) == 4 else parts[0])
                    # if ISO year-first, day is last
                    if len(parts[0]) == 4 and len(parts) >= 3:
                        d = int(parts[2])
                    return str(d) if 1 <= d <= 31 else ""
                except ValueError:
                    return ""
    return ""


def apply_mbillday_from_issue_date(bill_day: str, issue_raw: Any) -> tuple[str, bool]:
    """If bill_day blank/0, derive from issue date. Returns (value, changed)."""
    norm = str(bill_day or "").strip()
    if norm.endswith(".0"):
        norm = norm[:-2]
    if norm not in ("", "0", "0.0", "00"):
        return norm, False
    day = extract_day_from_date_value(issue_raw)
    if day:
        return day, True
    return norm, False


POLICY_LEVEL_RELATIONS = frozenset(
    {"OWNR", "OWNC", "PAYR", "PRIM", "ASGN", "BENP", "BENC"}
)


def apply_quikclid_phase_for_relation(phase: str, relation: str) -> tuple[str, bool, str]:
    """Non-INSD → phase 0. INSD blank/0 → phase 1 (base insured default)."""
    rel = (relation or "").strip().upper()
    ph = str(phase or "").strip()
    if ph.endswith(".0"):
        ph = ph[:-2]
    if rel and rel != "INSD":
        if ph != "0":
            return "0", True, "DG-QUIKCLID-004"
        return "0", False, "DG-QUIKCLID-004"
    # INSD
    if not ph or ph == "0":
        return "1", True, "DG-QUIKCLID-005"
    return ph, False, "DG-QUIKCLID-005"


def uppercase_alpha_field(value: Any) -> tuple[str, bool]:
    """Uppercase alphabetic codes (state, sex). Returns (value, changed)."""
    text = "" if value is None else str(value).strip()
    if not text:
        return "", False
    upper = text.upper()
    if upper == text:
        return text, False
    return upper, True
