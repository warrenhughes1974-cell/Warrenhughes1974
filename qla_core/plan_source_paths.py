"""Canonical plan/rate source paths — single resolver with legacy fallbacks."""
import os

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "plan_analysis", "source_data")
_LEGACY = os.path.join(_ROOT, "docs", "plan_conversion_reference")


def _first(*candidates):
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return candidates[0] if candidates else ""


def rate_table_extract():
    return _first(
        os.path.join(_SRC, "rates", "Rate_Table_Extract_20260427.csv"),
        os.path.join(_LEGACY, "Rate_Table_Extract_20260427.csv"),
    )


def paagerat_extract():
    return _first(
        os.path.join(_SRC, "rates", "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"),
        os.path.join(_LEGACY, "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"),
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


def paagerat_rate_paths():
    """Minimal path bundle for PAAGERAT PR / VARGP=3 plan resolution."""
    return {
        "paagerat_pr_extract": paagerat_extract(),
        "pcovrsgt_csv": pcovrsgt_csv(),
        "pcovr_csv": pcovr_csv(),
        "plan_form_crosswalk": policy_form_crosswalk(),
    }


def reference_dbf_dir():
    d = os.path.join(_SRC, "reference_dbf")
    if os.path.isdir(d):
        return d
    return _LEGACY if os.path.isdir(_LEGACY) else d
