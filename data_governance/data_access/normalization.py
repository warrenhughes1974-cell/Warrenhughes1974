"""DBF / CSV character-field normalization for governance checks."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

_NULL_TOKENS = {"", "nan", "none", "<na>", "nat", "null"}


def is_null_value(value: Any) -> bool:
    """True when the source value is null / missing (not merely blank text)."""
    if value is None:
        return True
    try:
        if value != value:  # NaN
            return True
    except Exception:
        pass
    # pandas NA / pd.NA
    try:
        import pandas as pd

        if value is pd.NA:
            return True
    except Exception:
        pass
    return False


def normalize_dbf_character(value: Any) -> str:
    """Normalize a QLAdmin CHARACTER field for comparison.

    - Treat None / NaN-like values as blank
    - Convert to string
    - Trim leading/trailing DBF padding (spaces)
    - Preserve the actual character content and case
    """
    if is_null_value(value):
        return ""
    text = str(value).strip()
    if text.lower() in _NULL_TOKENS:
        return ""
    return text


def normalize_character_casefold(value: Any) -> tuple[str | None, str, bool]:
    """Normalize a CHARACTER default field with case folding to uppercase.

    Returns:
        (normalized_upper_or_empty, original_display, is_null)
    """
    if is_null_value(value):
        return None, "", True
    original_display = str(value)
    trimmed = original_display.strip()
    if trimmed.lower() in _NULL_TOKENS:
        return "", original_display, False
    return trimmed.upper(), original_display, False


@dataclass(frozen=True)
class NumericZeroDecode:
    """Result of decoding a DBF/CSV value for zero-default checks."""

    is_null: bool = False
    is_blank: bool = False
    is_unreadable: bool = False
    is_zero: bool = False
    original_display: str = ""
    decoded_display: str = ""


def parse_governance_run_date(run_timestamp: str) -> date:
    """Parse framework run timestamp ``YYYY-MM-DD HH:MM:SS`` to a calendar date."""
    text = (run_timestamp or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(f"Unrecognized governance run timestamp: {run_timestamp!r}") from exc


def prior_month_end(controlling_date: date) -> date:
    """Return the last calendar day of the month before ``controlling_date``'s month."""
    first_of_month = controlling_date.replace(day=1)
    return first_of_month - timedelta(days=1)


def add_calendar_months(value: date, months: int) -> date:
    """Add whole calendar months, clamping the day to the target month length.

    Example: 2024-02-29 + 12 months → 2025-02-28 (February has 28 days in 2025).
    """
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def format_iso_date(value: date | None) -> str:
    return value.isoformat() if value is not None else ""


@dataclass(frozen=True)
class DateDecode:
    """Result of decoding a DBF/CSV date value for governance checks."""

    is_null: bool = False
    is_blank: bool = False
    is_unreadable: bool = False
    date_value: date | None = None
    original_display: str = ""
    decoded_display: str = ""


_APPROVED_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y%m%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
)


def decode_dbf_date(value: Any) -> DateDecode:
    """Decode a QuikDate DATE (or character-date) field.

    Supported empty DBF dates (None / null tokens / blank) are blank, not errors.
    Only approved date formats are parsed for character values.
    """
    if is_null_value(value):
        return DateDecode(is_null=True, is_blank=True)

    if isinstance(value, datetime):
        d = value.date()
        return DateDecode(
            date_value=d,
            original_display=str(value),
            decoded_display=d.isoformat(),
        )

    if isinstance(value, date):
        return DateDecode(
            date_value=value,
            original_display=value.isoformat(),
            decoded_display=value.isoformat(),
        )

    original_display = str(value)
    text = original_display.strip()
    if text == "" or text.lower() in _NULL_TOKENS:
        return DateDecode(is_blank=True, original_display=original_display)

    # Reject clearly non-date tokens without guessing
    for fmt in _APPROVED_DATE_FORMATS:
        try:
            d = datetime.strptime(text, fmt).date()
            return DateDecode(
                date_value=d,
                original_display=original_display,
                decoded_display=d.isoformat(),
            )
        except ValueError:
            continue

    return DateDecode(
        is_unreadable=True,
        original_display=original_display,
        decoded_display=text,
    )


def decode_numeric_zero(value: Any) -> NumericZeroDecode:
    """Decode a field for semantic-zero governance checks.

    Accepts numeric representations that are exactly zero after safe decode
    (0, 0.0, '0', '000', Decimal('0')). Null and blank are never treated as zero.
    """
    if is_null_value(value):
        return NumericZeroDecode(is_null=True)

    original_display = str(value)
    if isinstance(value, bool):
        # bool is a subclass of int; do not treat True/False as numeric zeros
        return NumericZeroDecode(
            is_unreadable=True,
            original_display=original_display,
            decoded_display=original_display.strip(),
        )

    if isinstance(value, (int, float, Decimal)):
        try:
            if Decimal(str(value)) == 0:
                return NumericZeroDecode(
                    is_zero=True,
                    original_display=original_display,
                    decoded_display="0",
                )
        except (InvalidOperation, ValueError):
            return NumericZeroDecode(
                is_unreadable=True,
                original_display=original_display,
                decoded_display=original_display.strip(),
            )
        return NumericZeroDecode(
            original_display=original_display,
            decoded_display=original_display.strip(),
        )

    text = original_display.strip()
    if text == "" or text.lower() in _NULL_TOKENS:
        return NumericZeroDecode(is_blank=True, original_display=original_display)

    try:
        if Decimal(text) == 0:
            return NumericZeroDecode(
                is_zero=True,
                original_display=original_display,
                decoded_display="0",
            )
        return NumericZeroDecode(
            original_display=original_display,
            decoded_display=text,
        )
    except (InvalidOperation, ValueError):
        return NumericZeroDecode(
            is_unreadable=True,
            original_display=original_display,
            decoded_display=text,
        )


def normalize_policy_number_for_length(value: Any) -> tuple[str | None, str, bool]:
    """Normalize MPOLICY for length validation.

    Returns:
        (normalized_or_none, original_display, is_null)

    - Removes only leading/trailing DBF padding
    - Preserves internal spaces and all inner characters
    - Does not invent, pad, truncate, or correct the value
    """
    if is_null_value(value):
        return None, "", True
    original_display = str(value)
    normalized = original_display.strip()
    return normalized, original_display, False


def normalize_identifier_preserve_zeros(value: Any) -> tuple[str | None, str, bool]:
    """Normalize a CHARACTER identifier (company, plan, account).

    - Null-safe
    - Trim leading/trailing DBF padding only
    - Preserve leading zeros and internal characters
    - Do not convert to numeric
    """
    if is_null_value(value):
        return None, "", True
    original_display = str(value)
    normalized = original_display.strip()
    return normalized, original_display, False


def derive_policy_company_code(policy_number: Any) -> str | None:
    """Return the final non-space character of a normalized policy number.

    Returns None when a company code cannot be derived (blank policy).
    This is a supplied business rule: the final character of MPOLICY
    represents the policy company code. It is not documented as a
    QLAdmin manual rule in this repository.
    """
    policy = normalize_dbf_character(policy_number)
    if not policy:
        return None
    return policy[-1]
