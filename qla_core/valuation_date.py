"""Align QLA_VALUATION_DATE with the active LifePRO source package."""
from __future__ import annotations

import os
import re
from pathlib import Path

from qla_core.lifepro_source_resolver import resolve_table_source

_PPOLC_DATE_RE = re.compile(r"_Extract_(\d{8})\.csv$", re.IGNORECASE)
_YE_VALUATION = "20251231"


def parse_ppolc_valuation_date(filename: str) -> str:
    """Return YYYYMMDD embedded in a PPOLC extract filename, or empty string."""
    match = _PPOLC_DATE_RE.search(filename or "")
    return match.group(1) if match else ""


def active_ppolc_path(source_dir: str | Path) -> tuple[str, str]:
    """Return (absolute_path, YYYYMMDD) for the newest PPOLC extract under source_dir."""
    path, _label = resolve_table_source(str(source_dir), "quikmstr")
    if not path:
        return "", ""
    return path, parse_ppolc_valuation_date(os.path.basename(path))


def ppolc_candidates_for_valuation(
    source_dir: str | Path,
    valuation_date: str,
    *,
    force_ppolc: str = "",
) -> list[str]:
    """Ordered PPOLC paths to try for a valuation date (year-end has special paths)."""
    src = Path(source_dir)
    if force_ppolc:
        forced = Path(force_ppolc)
        if not forced.is_absolute():
            forced = src / forced
        return [str(forced)]

    vd = "".join(c for c in valuation_date if c.isdigit())[:8]
    if vd == _YE_VALUATION:
        return [
            str(src / "12312025_Data" / "PPOLC_PolicyMaster_Extract_20260102.csv"),
            str(src / "PPOLC_PolicyMaster_Extract_20260102.csv"),
        ]
    return [str(src / f"PPOLC_PolicyMaster_Extract_{vd}.csv")]


def select_ppolc_path(
    source_dir: str | Path,
    valuation_date: str,
    *,
    force_ppolc: str = "",
) -> str:
    """Return the PPOLC extract path that matches valuation_date, or raise ValueError."""
    candidates = ppolc_candidates_for_valuation(
        source_dir, valuation_date, force_ppolc=force_ppolc
    )
    path = next((p for p in candidates if os.path.isfile(p)), "")
    if not path:
        vd = "".join(c for c in valuation_date if c.isdigit())[:8]
        raise ValueError(
            f"No PPOLC policy extract matches QLA_VALUATION_DATE={vd}: "
            f"{candidates[-1] if candidates else '(none)'}"
        )

    vd = "".join(c for c in valuation_date if c.isdigit())[:8]
    if vd != _YE_VALUATION:
        extract_date = parse_ppolc_valuation_date(os.path.basename(path))
        if extract_date and extract_date != vd:
            raise ValueError(
                f"Valuation/source mismatch: QLA_VALUATION_DATE={vd} "
                f"but selected policy extract is {os.path.basename(path)}"
            )
    return path


def resolve_valuation_date_yyyymmdd(
    *,
    source_dir: str | Path | None = None,
    explicit: str | None = None,
    force_ppolc: str = "",
) -> tuple[str, str]:
    """
    Resolve the batch valuation date.

    Priority: explicit argument > QLA_VALUATION_DATE env > date from active PPOLC.
    When explicit/env is set, validate that a matching PPOLC extract exists.
    """
    raw = (explicit or os.environ.get("QLA_VALUATION_DATE", "")).strip()
    digits = "".join(c for c in raw if c.isdigit())[:8]

    if source_dir is not None:
        if len(digits) == 8:
            select_ppolc_path(source_dir, digits, force_ppolc=force_ppolc)
            return digits, f"QLA_VALUATION_DATE={digits}"

        _path, auto_date = active_ppolc_path(source_dir)
        if auto_date:
            return auto_date, f"active PPOLC {os.path.basename(_path)}"

    if len(digits) == 8:
        return digits, f"QLA_VALUATION_DATE={digits}"

    raise ValueError(
        "QLA_VALUATION_DATE is required as YYYYMMDD and must match the source "
        "package being converted (for example, 20260630 or 20260731)."
    )


def apply_valuation_date_env(
    source_dir: str | Path | None = None,
    *,
    explicit: str | None = None,
    force_ppolc: str = "",
) -> tuple[str, str]:
    """Resolve valuation date, set os.environ['QLA_VALUATION_DATE'], return (date, source)."""
    vd, src = resolve_valuation_date_yyyymmdd(
        source_dir=source_dir,
        explicit=explicit,
        force_ppolc=force_ppolc,
    )
    os.environ["QLA_VALUATION_DATE"] = vd
    return vd, src
