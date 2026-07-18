"""Shared reference indexes for plan-value governance lookups."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import field_value


@dataclass
class ReferenceIndex:
    """Normalized key → 1-based record numbers."""

    key_to_records: dict[str, list[int]] = field(default_factory=dict)

    def count(self, key: str) -> int:
        return len(self.key_to_records.get(key, []))

    def exists_once(self, key: str) -> bool:
        return self.count(key) == 1

    def exists(self, key: str) -> bool:
        return self.count(key) > 0

    def is_duplicated(self, key: str) -> bool:
        return self.count(key) > 1


def _norm_char(value) -> str:
    normalized, _original, is_null = normalize_identifier_preserve_zeros(value)
    if is_null or normalized is None:
        return ""
    return normalized


def build_single_field_index(rows: list[dict], field_name: str, *, uppercase: bool = False) -> ReferenceIndex:
    key_to_records: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows, start=1):
        key = _norm_char(field_value(row, field_name))
        if not key:
            continue
        if uppercase:
            key = key.upper()
        key_to_records[key].append(idx)
    return ReferenceIndex(key_to_records=dict(key_to_records))


def build_composite_plan_code_index(
    rows: list[dict],
    *,
    plan_field: str,
    code_field: str,
    uppercase_code: bool = True,
) -> ReferenceIndex:
    """Index key format: ``PLAN\\x1fCODE`` (plan + code, same normalization as sources)."""
    key_to_records: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows, start=1):
        plan = _norm_char(field_value(row, plan_field))
        code = _norm_char(field_value(row, code_field))
        if not code:
            continue
        if uppercase_code:
            code = code.upper()
        key_to_records[f"{plan}\x1f{code}"].append(idx)
    return ReferenceIndex(key_to_records=dict(key_to_records))


def composite_key(plan: str, code: str, *, uppercase_code: bool = True) -> str:
    c = code.upper() if uppercase_code else code
    return f"{plan}\x1f{c}"
