"""Issue #143 — BF RPU MUNIT override from PPBENTYP Column DD (BF_CURRENT_DB).

Locked rule (Risk 2026-08-18):
    IF PAID_UP_TYPE=RU
    AND TYPE_CODE=BF
    AND BF_CURRENT_DB > 0
    AND abs(NUMBER_OF_UNITS - BF_CURRENT_DB / VALUE_PER_UNIT) > 0.01
    THEN MUNIT = BF_CURRENT_DB / VALUE_PER_UNIT

Isolated post-map override. Default NUMBER_OF_UNITS→MUNIT mapping is unchanged.
Issue #55 decimal emit still formats/floors the result after this hook.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Callable, Iterable

ISSUE143_EPS = 0.01
ISSUE143_SEQS = frozenset({"1", "01"})


def parse_issue143_num(val) -> float | None:
    if val is None:
        return None
    s = str(val).replace(",", "").strip()
    if s == "" or s.lower() in ("nan", "none", "null", "-"):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def seq_is_phase1(seq) -> bool:
    s = str(seq or "").strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = s.lstrip("0") or "0"
    return s == "1"


def is_rpu_paid_up_type(put) -> bool:
    s = str(put or "").strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s == "RU"


def expected_rpu_munit(bf_current_db: float, value_per_unit: float) -> float:
    return bf_current_db / value_per_unit


def should_remap_issue143(
    *,
    units: float | None,
    value_per_unit: float | None,
    bf_current_db: float | None,
    type_code,
    is_rpu: bool,
) -> bool:
    if not is_rpu:
        return False
    if str(type_code or "").strip().upper() != "BF":
        return False
    if units is None or value_per_unit is None or bf_current_db is None:
        return False
    if value_per_unit <= 0 or bf_current_db <= 0:
        return False
    expected = expected_rpu_munit(bf_current_db, value_per_unit)
    return abs(units - expected) > ISSUE143_EPS


def apply_issue143_rpu_munit(
    row_data: dict,
    *,
    is_rpu: bool,
    type_code,
    bf_current_db,
    value_per_unit,
) -> bool:
    """Override mapped MUNIT in place. Returns True when remapped."""
    units = parse_issue143_num(row_data.get("MUNIT"))
    vpu = parse_issue143_num(value_per_unit)
    dd = parse_issue143_num(bf_current_db)
    if not should_remap_issue143(
        units=units,
        value_per_unit=vpu,
        bf_current_db=dd,
        type_code=type_code,
        is_rpu=is_rpu,
    ):
        return False
    row_data["MUNIT"] = expected_rpu_munit(dd, vpu)
    return True


def find_extract_csv(search_dirs: Iterable[str], keyword: str) -> str | None:
    matches: list[str] = []
    key = keyword.lower()
    for d in search_dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            fl = name.lower()
            if key not in fl or not fl.endswith(".csv"):
                continue
            if any(bad in fl for bad in ("copy", "old", "backup", "archive")):
                continue
            matches.append(os.path.normpath(os.path.join(d, name)))
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def load_issue143_rpu_set(ppolc_path: str, normalize_fn: Callable) -> set[str]:
    out: set[str] = set()
    with open(ppolc_path, newline="", encoding="latin1", errors="replace") as fh:
        for row in csv.DictReader(fh):
            keys = {str(k).strip().upper(): k for k in row.keys() if k}
            put_k = keys.get("PAID_UP_TYPE")
            pol_k = keys.get("POLICY_NUMBER")
            if not put_k or not pol_k:
                continue
            if not is_rpu_paid_up_type(row.get(put_k)):
                continue
            pol = normalize_fn(row.get(pol_k))
            if pol:
                out.add(pol)
    return out


def load_issue143_bf_cache(ppbentyp_path: str, normalize_fn: Callable) -> dict[str, dict]:
    """Seq-1 TYPE_CODE + BF_CURRENT_DB keyed by normalized source POLICY_NUMBER."""
    cache: dict[str, dict] = {}
    with open(ppbentyp_path, newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        fieldmap = {str(k).strip().upper(): k for k in (reader.fieldnames or []) if k}
        pol_k = fieldmap.get("POLICY_NUMBER")
        seq_k = fieldmap.get("BENEFIT_SEQ")
        tc_k = fieldmap.get("TYPE_CODE")
        dd_k = fieldmap.get("BF_CURRENT_DB")
        if not pol_k or not seq_k:
            return cache
        for row in reader:
            if not seq_is_phase1(row.get(seq_k)):
                continue
            pol = normalize_fn(row.get(pol_k))
            if not pol:
                continue
            cache[pol] = {
                "type_code": str(row.get(tc_k, "") or "").strip().upper() if tc_k else "",
                "bf_current_db": row.get(dd_k) if dd_k else "",
            }
    return cache


@dataclass
class Issue143Class:
    kind: str  # candidate | aligned_bf | ba
    policy: str
    source_units: float | None
    value_per_unit: float | None
    bf_current_db: float | None
    type_code: str
    expected_munit: float | None


def classify_issue143_row(
    *,
    policy: str,
    units,
    value_per_unit,
    type_code,
    bf_current_db,
    is_rpu: bool,
) -> Issue143Class:
    u = parse_issue143_num(units)
    vpu = parse_issue143_num(value_per_unit)
    dd = parse_issue143_num(bf_current_db)
    tc = str(type_code or "").strip().upper()
    if not is_rpu:
        return Issue143Class("other", policy, u, vpu, dd, tc, None)
    if should_remap_issue143(
        units=u,
        value_per_unit=vpu,
        bf_current_db=dd,
        type_code=tc,
        is_rpu=True,
    ):
        return Issue143Class(
            "candidate",
            policy,
            u,
            vpu,
            dd,
            tc,
            expected_rpu_munit(dd, vpu),  # type: ignore[arg-type]
        )
    if tc == "BF" and (dd or 0) > 0 and (vpu or 0) > 0:
        return Issue143Class("aligned_bf", policy, u, vpu, dd, tc, expected_rpu_munit(dd, vpu))  # type: ignore[arg-type]
    return Issue143Class("ba", policy, u, vpu, dd, tc, None)
