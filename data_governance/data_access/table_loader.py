"""Load QLAdmin tables from a data region (read-only).

Uses the centralized TableResolver for path lookup.
Never modifies source files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from data_governance.config.settings import TABLE_FILE_STEMS
from data_governance.data_access.table_resolver import TableResolver


@dataclass
class LoadedTable:
    logical_name: str
    path: str
    format: str  # "dbf" | "csv" | "memory"
    rows: list[dict[str, Any]] = field(default_factory=list)
    read_only: bool = True

    def __len__(self) -> int:
        return len(self.rows)


@dataclass
class GovernanceDataStore:
    """In-memory store of tables used by governance rules."""

    data_dir: str
    tables: dict[str, LoadedTable] = field(default_factory=dict)
    load_errors: dict[str, str] = field(default_factory=dict)
    resolver: TableResolver | None = None
    source_files_opened_read_only: bool = True

    def get(self, logical_name: str) -> LoadedTable | None:
        return self.tables.get(logical_name)

    def rows(self, logical_name: str) -> list[dict[str, Any]]:
        table = self.tables.get(logical_name)
        return list(table.rows) if table else []

    def missing(self, logical_name: str) -> bool:
        return logical_name not in self.tables

    def load_error(self, logical_name: str) -> str | None:
        return self.load_errors.get(logical_name)


def _resolve_column(row_or_columns: Any, *names: str) -> str | None:
    if isinstance(row_or_columns, dict):
        lookup = {str(k).strip().upper(): k for k in row_or_columns.keys()}
    else:
        lookup = {str(c).strip().upper(): c for c in row_or_columns}
    for name in names:
        key = name.upper()
        if key in lookup:
            return lookup[key]
    return None


def field_value(row: dict[str, Any], *names: str) -> Any:
    """Return the first matching field value (case-insensitive column names)."""
    col = _resolve_column(row, *names)
    if col is None:
        return None
    return row.get(col)


def _load_csv(path: str) -> list[dict[str, Any]]:
    df = pd.read_csv(path, dtype=str, low_memory=False, keep_default_na=False)
    return df.to_dict(orient="records")


def _load_dbf_readonly(path: str) -> list[dict[str, Any]]:
    """Open a DBF in read-only binary mode via dbfread (does not modify the file)."""
    from dbfread import DBF

    # dbfread opens the file with mode 'rb' (read-only binary).
    table = DBF(
        path,
        load=True,
        ignore_missing_memofile=True,
        char_decode_errors="ignore",
        raw=False,
    )
    rows: list[dict[str, Any]] = []
    for rec in table:
        rows.append({str(k): rec.get(k) for k in rec.keys()})
    return rows


def load_table_via_resolver(resolver: TableResolver, logical_name: str) -> LoadedTable:
    resolved = resolver.resolve(logical_name)
    if resolved is None:
        expected = ", ".join(resolver.expected_filenames(logical_name))
        raise FileNotFoundError(
            f"{logical_name} not found under '{resolver.data_region_path}' "
            f"(expected one of: {expected})"
        )
    if resolved.format == "dbf":
        # Confirm read access before load
        if not os.access(resolved.path, os.R_OK):
            raise PermissionError(f"No read permission for {resolved.path}")
        rows = _load_dbf_readonly(resolved.path)
    else:
        if not os.access(resolved.path, os.R_OK):
            raise PermissionError(f"No read permission for {resolved.path}")
        rows = _load_csv(resolved.path)
    return LoadedTable(
        logical_name=logical_name,
        path=resolved.path,
        format=resolved.format,
        rows=rows,
        read_only=True,
    )


def load_governance_tables(
    data_dir: str,
    logical_names: list[str] | None = None,
    preloaded: dict[str, list[dict[str, Any]]] | None = None,
    resolver: TableResolver | None = None,
) -> GovernanceDataStore:
    """Load requested tables. Preloaded in-memory rows take precedence (tests)."""
    resolver = resolver or TableResolver(data_dir)
    store = GovernanceDataStore(data_dir=data_dir, resolver=resolver)
    names = logical_names or list(TABLE_FILE_STEMS.keys())
    for name in names:
        if preloaded and name in preloaded:
            store.tables[name] = LoadedTable(
                logical_name=name,
                path="(memory)",
                format="memory",
                rows=list(preloaded[name]),
                read_only=True,
            )
            continue
        try:
            store.tables[name] = load_table_via_resolver(resolver, name)
        except Exception as exc:
            store.load_errors[name] = str(exc)
    return store
