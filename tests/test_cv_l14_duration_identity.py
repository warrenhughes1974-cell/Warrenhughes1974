"""Issue L14 — CV duration placement (revised 2026-08-13).

The L14 identity freeze was retired with Warren's approval after Eric's
'Rates of Identified Issues - 8.13.26' workbook proved LifePRO places L14
M/54 CV on native years 3..46 while the extract labels them 2..45. L14 now
flows through the PDAGE native-first remap like every other coverage:
ql_duration = source_duration + native_first - extract_first_nonzero.
"""
from qla_core.rate_factor_loader import (
    CV_IDENTITY_DURATION_COVERAGES,
    cv_remap_ql_duration,
)


def test_l14_identity_freeze_retired():
    assert "L14" not in CV_IDENTITY_DURATION_COVERAGES


def test_l14_f69_native_first_2_stays_identity():
    # F/69: PDAGE native first year 2 == extract fnz 2 -> shift self-cancels.
    assert cv_remap_ql_duration(2, "F", 69, 2, coverage_id="L14", native_first=2) == 2
    assert cv_remap_ql_duration(31, "F", 69, 2, coverage_id="L14", native_first=2) == 31
    assert cv_remap_ql_duration(32, "F", 69, 2, coverage_id="L14", native_first=2) is None


def test_l14_m54_native_first_3_shifts_plus_one():
    # M/54: PDAGE native first year 3, extract fnz 2 -> +1 (Eric: 538.30 at Dur 24).
    assert cv_remap_ql_duration(2, "M", 54, 2, coverage_id="L14", native_first=3) == 3
    assert cv_remap_ql_duration(23, "M", 54, 2, coverage_id="L14", native_first=3) == 24
    assert cv_remap_ql_duration(45, "M", 54, 2, coverage_id="L14", native_first=3) == 46
    assert cv_remap_ql_duration(46, "M", 54, 2, coverage_id="L14", native_first=3) is None


def test_l14_f45_native_first_3_shifts_plus_one():
    assert cv_remap_ql_duration(2, "F", 45, 2, coverage_id="L14", native_first=3) == 3
    assert cv_remap_ql_duration(54, "F", 45, 2, coverage_id="L14", native_first=3) == 55


def test_gl85_remap_unchanged_without_coverage():
    assert cv_remap_ql_duration(2, "M", 14, 2) == 3
    assert cv_remap_ql_duration(85, "M", 14, 2) == 86


def test_gl85_coverage_native_first_offset():
    assert cv_remap_ql_duration(2, "M", 14, 2, coverage_id="670 GL85-8", native_first=3) == 3
