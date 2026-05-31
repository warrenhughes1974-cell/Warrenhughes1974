"""quikactg plan-level accounting setup from PACTG (Phase P3F).

One output row per distinct PACTG.PLAN_CODE. Account columns pivot from PACTG
rows where CREDIT_CODE or DEBIT_CODE matches rulebook transaction codes.
MPLAN uses the same closed resolver as quikridr (P3E).
"""

from __future__ import annotations

import os
import re
from typing import Any

import pandas as pd

from qla_core.mplan_authority import resolution_to_trace_row, validate_emitted_mplan
from qla_core.product_catalog_authority import (
    MplanResolution,
    resolve_authoritative_mplan,
    strip_val,
)

QUIKACTG_SCHEMA = [
    "MCOMP", "MPLAN", "MPREM1ST", "MPREMREN", "MDIVCASH", "MDIVPREM", "MDIVACCM",
    "MDIVPUA", "MDIVPUT", "MDVDPINT", "MLOAN", "MLOANINT", "MSCHG", "MDEATH",
    "MCLAIM", "MCOM1ST", "MCOMREN", "MCOMMSGL",
]

DEFAULT_ACCOUNT_FIELD_CODES: dict[str, str] = {
    "MPREM1ST": "110",
    "MPREMREN": "110",
    "MDIVCASH": "515",
    "MDIVPREM": "516",
    "MDIVACCM": "514",
    "MDIVPUA": "517",
    "MDIVPUT": "518",
    "MDVDPINT": "641",
    "MLOAN": "411",
    "MLOANINT": "412",
    "MSCHG": "1020",
    "MDEATH": "530",
    "MCLAIM": "567",
    "MCOM1ST": "1110",
    "MCOMREN": "1111",
    "MCOMMSGL": "1115",
}

PACTG_USECOLS = [
    "PLAN_CODE",
    "CREDIT_CODE",
    "DEBIT_CODE",
    "CREDIT_ACCOUNT",
    "BENEFIT_TYPE",
    "BENEFIT_SEQ",
]

_DASH_ONLY_RE = re.compile(r"^-+$")


def load_account_field_codes(rulebook_path: str | None = None) -> dict[str, str]:
    """Load account-code mapping from Sync_Rulebook_quikactg.csv when available."""
    codes = dict(DEFAULT_ACCOUNT_FIELD_CODES)
    if not rulebook_path or not os.path.isfile(rulebook_path):
        return codes

    rb = pd.read_csv(rulebook_path, dtype=str, keep_default_na=False)
    rb.columns = [strip_val(c) for c in rb.columns]
    for _, row in rb.iterrows():
        target = strip_val(row.get("Target_Field", ""))
        note = strip_val(row.get("Transformation_Note", ""))
        if target not in QUIKACTG_SCHEMA or target in ("MCOMP", "MPLAN"):
            continue
        match = re.search(r"=\s*(\d+)", note)
        if match:
            codes[target] = match.group(1)
    return codes


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [strip_val(c) for c in out.columns]
    return out


def is_valid_source_plan_code(plan_code: str) -> bool:
    """Skip blank, separator, and non-plan placeholder rows."""
    raw = plan_code if isinstance(plan_code, str) else str(plan_code)
    if not strip_val(raw):
        return False
    if _DASH_ONLY_RE.match(raw.strip()):
        return False
    return True


def _normalize_code(value: str) -> str:
    s = strip_val(value)
    if s.endswith(".0"):
        s = s[:-2]
    return s


def find_credit_account(plan_rows: pd.DataFrame, transaction_code: str) -> str:
    """First CREDIT_ACCOUNT where CREDIT_CODE or DEBIT_CODE matches transaction_code."""
    code = _normalize_code(transaction_code)
    for _, row in plan_rows.iterrows():
        credit = _normalize_code(row.get("CREDIT_CODE", ""))
        debit = _normalize_code(row.get("DEBIT_CODE", ""))
        if credit == code or debit == code:
            acct = strip_val(row.get("CREDIT_ACCOUNT", ""))
            if acct:
                return acct
    return ""


def load_pactg_plan_index(pactg_path: str) -> tuple[dict[str, pd.DataFrame], int]:
    """Load PACTG and group rows by exact PLAN_CODE (preserves spaces)."""
    df = pd.read_csv(
        pactg_path,
        encoding="latin1",
        dtype=str,
        usecols=lambda c: strip_val(c) in PACTG_USECOLS,
        on_bad_lines="skip",
        keep_default_na=False,
    )
    df = _normalize_columns(df)
    if "PLAN_CODE" not in df.columns:
        return {}, 0

    grouped: dict[str, pd.DataFrame] = {}
    for plan_code, grp in df.groupby("PLAN_CODE", sort=False):
        if not is_valid_source_plan_code(plan_code):
            continue
        grouped[plan_code] = grp.reset_index(drop=True)
    return grouped, len(df)


def build_quikactg_row(
    source_plan_code: str,
    plan_rows: pd.DataFrame,
    account_codes: dict[str, str],
    *,
    cw_map: dict[str, str],
    resolver: Any,
    closed_authority: bool,
    allow_legacy: bool,
    default_mcomp: str = "C",
    quikplan_plan_set: set[str] | None = None,
    source_file: str = "",
    source_row_number: int = 0,
) -> tuple[dict[str, str], dict | None, MplanResolution]:
    """Build one quikactg row and MPLAN resolution trace metadata."""
    quikplan_plan_set = quikplan_plan_set or set()
    legacy_candidate = cw_map.get(strip_val(source_plan_code), strip_val(source_plan_code))

    if closed_authority and resolver is not None:
        resolution = resolve_authoritative_mplan(
            source_plan_code,
            legacy_candidate,
            resolver,
            allow_legacy=allow_legacy,
        )
        resolved_mplan = resolution.resolved_mplan
    else:
        resolution = MplanResolution(
            resolved_mplan=legacy_candidate,
            resolution_path="LEGACY_CROSSWALK",
            fallback_value=legacy_candidate,
            is_authoritative=legacy_candidate in quikplan_plan_set,
            source_plan_code=source_plan_code,
            candidate_mplan=legacy_candidate,
        )
        resolved_mplan = legacy_candidate

    row_data: dict[str, str] = {
        "MCOMP": default_mcomp,
        "MPLAN": resolved_mplan,
    }
    for field, txn_code in account_codes.items():
        if field in ("MCOMP", "MPLAN"):
            continue
        row_data[field] = find_credit_account(plan_rows, txn_code)

    benefit_type = ""
    if "BENEFIT_TYPE" in plan_rows.columns and not plan_rows.empty:
        benefit_type = strip_val(plan_rows.iloc[0].get("BENEFIT_TYPE", ""))

    trace = resolution_to_trace_row(
        resolution,
        source_file=source_file,
        source_row_number=source_row_number,
        mpolicy="",
        mphase="PLAN",
        row_data=row_data,
        quikplan_plan_set=quikplan_plan_set,
        allow_legacy=allow_legacy,
        source_benefit_type=benefit_type,
    )
    return row_data, trace, resolution


def convert_quikactg_from_pactg(
    pactg_path: str,
    *,
    cw_map: dict[str, str] | None = None,
    resolver: Any = None,
    quikplan_plan_set: set[str] | None = None,
    closed_authority: bool = False,
    allow_legacy: bool = False,
    rulebook_path: str | None = None,
    default_mcomp: str = "C",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Convert PACTG to quikactg with optional closed MPLAN authority."""
    cw_map = cw_map or {}
    quikplan_plan_set = quikplan_plan_set or set()
    account_codes = load_account_field_codes(rulebook_path)
    plan_index, pactg_rows_read = load_pactg_plan_index(pactg_path)
    source_file = os.path.basename(pactg_path)

    output_rows: list[list[str]] = []
    trace_rows: list[dict] = []

    for row_num, (source_plan, plan_rows) in enumerate(sorted(plan_index.items(), key=lambda x: strip_val(x[0]).upper()), start=1):
        row_data, trace, _ = build_quikactg_row(
            source_plan,
            plan_rows,
            account_codes,
            cw_map=cw_map,
            resolver=resolver,
            closed_authority=closed_authority,
            allow_legacy=allow_legacy,
            default_mcomp=default_mcomp,
            quikplan_plan_set=quikplan_plan_set,
            source_file=source_file,
            source_row_number=row_num + 1,
        )
        output_rows.append([row_data.get(h, "") for h in QUIKACTG_SCHEMA])
        if trace:
            trace_rows.append(trace)

    output_df = pd.DataFrame(output_rows, columns=QUIKACTG_SCHEMA)
    trace_df = pd.DataFrame(trace_rows)
    passed, val_stats = validate_emitted_mplan(output_df, quikplan_plan_set)

    stats = {
        "pactg_rows_read": pactg_rows_read,
        "distinct_plans": len(plan_index),
        "emitted_rows": len(output_df),
        "validation_passed": passed,
        **val_stats,
    }
    return output_df, trace_df, stats
