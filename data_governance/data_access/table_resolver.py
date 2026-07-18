"""Centralized QLAdmin table → file resolution for a data region.

Logical names (QuikComp, QuikAgts, QuikMstr, …) map to files in the selected
region. Matching is case-insensitive. Rules must not resolve paths themselves.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from data_governance.config.settings import TABLE_FILE_STEMS


@dataclass(frozen=True)
class ResolvedTableFile:
    logical_name: str
    path: str
    format: str  # "dbf" | "csv"
    filename: str


class TableResolver:
    """Resolve logical QLAdmin table names inside one data region."""

    def __init__(self, data_region_path: str):
        self.data_region_path = os.path.normpath(data_region_path)
        self._lower_map: dict[str, str] | None = None

    def _entries(self) -> dict[str, str]:
        if self._lower_map is None:
            if not os.path.isdir(self.data_region_path):
                self._lower_map = {}
            else:
                self._lower_map = {
                    name.lower(): name for name in os.listdir(self.data_region_path)
                }
        return self._lower_map

    def refresh(self) -> None:
        self._lower_map = None

    def resolve(self, logical_name: str) -> ResolvedTableFile | None:
        """Return the resolved file for a logical table, or None if missing.

        Prefers ``.dbf`` over ``.csv`` when both exist.
        """
        stems = TABLE_FILE_STEMS.get(logical_name)
        if not stems:
            raise ValueError(f"Unknown logical QLAdmin table name: {logical_name}")
        entries = self._entries()
        for stem in stems:
            for ext, fmt in ((".dbf", "dbf"), (".csv", "csv")):
                key = stem.lower() + ext
                if key in entries:
                    filename = entries[key]
                    return ResolvedTableFile(
                        logical_name=logical_name,
                        path=os.path.join(self.data_region_path, filename),
                        format=fmt,
                        filename=filename,
                    )
        return None

    def exists(self, logical_name: str) -> bool:
        return self.resolve(logical_name) is not None

    def missing_tables(self, logical_names: list[str] | tuple[str, ...]) -> list[str]:
        return [name for name in logical_names if not self.exists(name)]

    def expected_filenames(self, logical_name: str) -> list[str]:
        stems = TABLE_FILE_STEMS.get(logical_name, ())
        names: list[str] = []
        for stem in stems:
            names.append(f"{stem.upper()}.DBF")
            names.append(f"{stem}.csv")
        return names
