"""Shared helpers for governance rule modules."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Iterable

import pandas as pd

from data_governance.governance_config import AuditFinding, make_finding


def get_df(data: dict, *keys: str) -> pd.DataFrame | None:
    """Return the first matching dataframe from data by filename key variants."""
    for key in keys:
        for candidate in (key, key.lower(), key.upper(), f"{key}.csv", f"{key.lower()}.csv"):
            if candidate in data and data[candidate] is not None:
                df = data[candidate]
                if isinstance(df, pd.DataFrame):
                    return df
    # Case-insensitive fallback
    lower_map = {str(k).lower(): k for k in data.keys()}
    for key in keys:
        for candidate in (key.lower(), f"{key.lower()}.csv"):
            if candidate in lower_map:
                df = data[lower_map[candidate]]
                if isinstance(df, pd.DataFrame):
                    return df
    return None


def col(df: pd.DataFrame, *names: str) -> str | None:
    """Resolve a column name case-insensitively; return actual column or None."""
    if df is None or df.empty and len(df.columns) == 0:
        return None
    lookup = {str(c).strip().upper(): c for c in df.columns}
    for name in names:
        if name.upper() in lookup:
            return lookup[name.upper()]
    return None


def s(val: Any) -> str:
    """Normalize a cell value to a stripped string; blank for nulls."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    text = str(val).strip()
    if text.lower() in ("nan", "none", "<na>", "nat"):
        return ""
    return text


def is_blank(val: Any) -> bool:
    return s(val) == ""


def to_float(val: Any, default: float | None = None) -> float | None:
    text = s(val)
    if text == "":
        return default
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def to_int(val: Any, default: int | None = None) -> int | None:
    f = to_float(val, None)
    if f is None:
        return default
    try:
        return int(f)
    except (TypeError, ValueError):
        return default


def parse_date(val: Any) -> date | None:
    """Parse common QLA / LifePRO date formats to date, or None."""
    text = s(val)
    if not text:
        return None
    # Excel serial
    try:
        if text.isdigit() and len(text) <= 5:
            serial = int(text)
            if serial > 0:
                return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    except (ValueError, OverflowError):
        pass
    candidates = [text]
    if len(text) >= 10 and text[4] in "-/":
        candidates.append(text[:10])
    if len(text) == 8 and text.isdigit():
        candidates.append(text)
    for candidate in candidates:
        for fmt in (
            "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y",
            "%Y%m%d", "%m/%d/%y", "%d-%b-%Y", "%d-%b-%y",
        ):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    # ISO with time
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def last_day_previous_month(today: date | None = None) -> date:
    today = today or date.today()
    first_this = today.replace(day=1)
    return first_this - timedelta(days=1)


def max_allowed_date(today: date | None = None) -> date:
    today = today or date.today()
    # today + ~12 months
    year = today.year + (today.month + 11) // 12
    month = (today.month + 11) % 12 + 1
    day = min(today.day, 28)
    return date(year, month, day)


def date_out_of_range(d: date, today: date | None = None) -> bool:
    today = today or date.today()
    return d < date(1900, 1, 1) or d > max_allowed_date(today)


def sample_rows(df: pd.DataFrame, idxs: Iterable, cols: list[str] | None = None, limit: int = 10) -> list[dict]:
    out = []
    use_cols = cols or list(df.columns)[:12]
    use_cols = [c for c in use_cols if c in df.columns]
    for i, idx in enumerate(idxs):
        if i >= limit:
            break
        try:
            row = df.loc[idx]
        except (KeyError, TypeError):
            continue
        out.append({c: s(row.get(c, "")) for c in use_cols})
    return out


def unique_values(series: pd.Series) -> set[str]:
    return {s(v) for v in series.dropna().unique() if s(v)}


def company_codes(df: pd.DataFrame | None) -> set[str]:
    if df is None:
        return set()
    for name in ("MCOMP", "COMP", "COMPANY", "COMPCODE", "CCOMP"):
        c = col(df, name)
        if c:
            return unique_values(df[c])
    return set()


def plan_codes(df: pd.DataFrame | None) -> set[str]:
    if df is None:
        return set()
    for name in ("PLAN", "MPLAN", "PLANCODE"):
        c = col(df, name)
        if c:
            return unique_values(df[c])
    return set()


def client_ids(df: pd.DataFrame | None) -> set[str]:
    if df is None:
        return set()
    c = col(df, "MCLIENTID", "CLIENTID")
    if c:
        return unique_values(df[c])
    return set()


def policy_set(df: pd.DataFrame | None) -> set[str]:
    if df is None:
        return set()
    c = col(df, "MPOLICY")
    if c:
        return unique_values(df[c])
    return set()


def group_findings_by_key(
    rule_id: str,
    rule_category: str,
    severity: str,
    source_file: str,
    description: str,
    field_name: str,
    expected: str,
    reason_fn,
    keys: list[str],
    actuals: dict[str, str] | None = None,
    samples: list[dict] | None = None,
) -> list[AuditFinding]:
    """One finding summarizing many keys (preferred for volume)."""
    if not keys:
        return []
    actuals = actuals or {}
    sample_actual = actuals.get(keys[0], "") if keys else ""
    reason = reason_fn(keys[0], sample_actual, len(keys))
    return [
        make_finding(
            rule_id=rule_id,
            rule_category=rule_category,
            severity=severity,
            source_file=source_file,
            description=description,
            reason=reason,
            field_name=field_name,
            expected=expected,
            actual=sample_actual,
            affected_keys=keys,
            sample_records=samples or [{"key": k, "actual": actuals.get(k, "")} for k in keys[:10]],
            affected_count=len(keys),
        )
    ]


def finding_per_key(
    rule_id: str,
    rule_category: str,
    severity: str,
    source_file: str,
    description: str,
    field_name: str,
    expected: str,
    items: list[tuple[str, str, str]],
    max_individual: int = 50,
) -> list[AuditFinding]:
    """
    items: list of (key, actual, reason).
    If many items, emit one aggregated finding plus samples.
    """
    if not items:
        return []
    if len(items) <= max_individual:
        return [
            make_finding(
                rule_id=rule_id,
                rule_category=rule_category,
                severity=severity,
                source_file=source_file,
                description=description,
                reason=reason,
                field_name=field_name,
                expected=expected,
                actual=actual,
                affected_keys=[key],
                sample_records=[{"key": key, field_name: actual}],
                affected_count=1,
            )
            for key, actual, reason in items
        ]
    keys = [k for k, _, _ in items]
    return [
        make_finding(
            rule_id=rule_id,
            rule_category=rule_category,
            severity=severity,
            source_file=source_file,
            description=description,
            reason=items[0][2] + f" ({len(items)} total records affected; showing aggregate.)",
            field_name=field_name,
            expected=expected,
            actual=items[0][1],
            affected_keys=keys,
            sample_records=[{"key": k, field_name: a} for k, a, _ in items[:10]],
            affected_count=len(items),
        )
    ]
