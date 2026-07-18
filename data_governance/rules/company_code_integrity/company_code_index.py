"""Shared QuikComp company-code index for Item 1 rules."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from data_governance.data_access.normalization import normalize_dbf_character
from data_governance.data_access.table_loader import field_value


@dataclass
class CompanyCodeIndex:
    """Normalized MCOMP → list of 1-based QuikComp record numbers."""

    code_to_records: dict[str, list[int]] = field(default_factory=dict)
    blank_record_numbers: list[int] = field(default_factory=list)

    def count(self, code: str) -> int:
        return len(self.code_to_records.get(code, []))

    def exists_once(self, code: str) -> bool:
        return self.count(code) == 1

    def exists(self, code: str) -> bool:
        return self.count(code) > 0

    def is_duplicated(self, code: str) -> bool:
        return self.count(code) > 1

    @property
    def unique_codes(self) -> set[str]:
        return set(self.code_to_records.keys())


def build_company_code_index(quikcomp_rows: list[dict]) -> CompanyCodeIndex:
    code_to_records: dict[str, list[int]] = defaultdict(list)
    blanks: list[int] = []
    for idx, row in enumerate(quikcomp_rows, start=1):
        code = normalize_dbf_character(field_value(row, "MCOMP"))
        if not code:
            blanks.append(idx)
            continue
        code_to_records[code].append(idx)
    return CompanyCodeIndex(
        code_to_records=dict(code_to_records),
        blank_record_numbers=blanks,
    )
