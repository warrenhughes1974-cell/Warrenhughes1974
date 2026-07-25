"""Canonical plan/rate source paths — single resolver with legacy fallbacks.

Rate extracts (PAAGE / PAAGERAT / PDAGE): discover all dated files under
QLA_Migration/Source and merge oldest→newest so filename YYYYMMDD wins on
duplicate keys (see qla_core.dated_extract_merge).
"""
import os

from qla_core.dated_extract_merge import ensure_merged_family

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "plan_analysis", "source_data")
_QLA_SOURCE = os.path.join(_ROOT, "QLA_Migration", "Source")
_STAGING = os.path.join(_ROOT, "QLA_Migration", "Staging")
_LEGACY = os.path.join(_ROOT, "docs", "plan_conversion_reference")

# Last merge summaries (for pipeline logging / diagnostics)
_LAST_MERGE: dict[str, dict] = {}


def _first(*candidates):
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return candidates[0] if candidates else ""


def last_merge_summaries() -> dict[str, dict]:
    return dict(_LAST_MERGE)


def rate_table_extract():
    """Prefer client Source secondary Rate_Table (Issue #48), then dated twins."""
    return _first(
        os.path.join(_QLA_SOURCE, "Rate_Table_Extract_Txt.txt"),
        os.path.join(_SRC, "rates", "Rate_Table_Extract_20260427.csv"),
        os.path.join(_LEGACY, "Rate_Table_Extract_20260427.csv"),
    )


def _merged_family(family: str, legacy_fallbacks: list[str], log=None) -> str:
    path, summary = ensure_merged_family(
        _QLA_SOURCE,
        _STAGING,
        family,
        extra_paths=legacy_fallbacks,
        log=log,
    )
    _LAST_MERGE[family.upper()] = summary
    if path:
        return path
    return _first(*legacy_fallbacks)


def paage_extract(log=None):
    """PAAGE attained-age header extract — all dated Source files, newest filename wins."""
    return _merged_family(
        "PAAGE",
        [
            os.path.join(_QLA_SOURCE, "PAAGE_AttainedAge_Rates_Extract_20260714.csv"),
            os.path.join(_QLA_SOURCE, "PAAGE_AttainedAge_Rates_Extract_20260713.csv"),
            os.path.join(_QLA_SOURCE, "PAAGE_AttainedAge_Rates_Extract_20260630.csv"),
        ],
        log=log,
    )


def paagerat_extract(log=None):
    """PAAGERAT attained-age values — all dated Source files, newest filename wins."""
    return _merged_family(
        "PAAGERAT",
        [
            os.path.join(_SRC, "rates", "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"),
            os.path.join(_LEGACY, "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"),
        ],
        log=log,
    )


def pdage_extract(log=None):
    """PDAGE age/duration — all dated Source files, newest filename wins."""
    return _merged_family(
        "PDAGE",
        [
            os.path.join(_QLA_SOURCE, "PDAGE_AgeDuration_Rates_Extract_20260530.csv"),
        ],
        log=log,
    )


def policy_form_crosswalk():
    return _first(
        os.path.join(_SRC, "crosswalk", "Policy Form Crosswalk 5.22.26.xlsx"),
        os.path.join(_LEGACY, "Policy Form Crosswalk 5.22.26.xlsx"),
    )


def pcovr_csv():
    return _first(
        os.path.join(_SRC, "coverage", "PCOVR.csv"),
        os.path.join(_ROOT, "QLA_Migration", "Source", "PCOVR.csv"),
    )


def pcovrsgt_csv():
    return _first(
        os.path.join(_SRC, "coverage", "PCOVRSGT.csv"),
        os.path.join(_LEGACY, "PCOVRSGT.csv"),
    )


def paagerat_rate_paths(log=None):
    """Minimal path bundle for PAAGERAT PR / VARGP=3 plan resolution (+ PAAGE)."""
    return {
        "paagerat_pr_extract": paagerat_extract(log=log),
        "paage_extract": paage_extract(log=log),
        "pdage_extract": pdage_extract(log=log),
        "pcovrsgt_csv": pcovrsgt_csv(),
        "pcovr_csv": pcovr_csv(),
        "plan_form_crosswalk": policy_form_crosswalk(),
    }


def reference_dbf_dir():
    d = os.path.join(_SRC, "reference_dbf")
    if os.path.isdir(d):
        return d
    return _LEGACY if os.path.isdir(_LEGACY) else d
