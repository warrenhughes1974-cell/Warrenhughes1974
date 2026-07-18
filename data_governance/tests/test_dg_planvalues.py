"""Tests for DG-PLANVALUES — Plan Value Reference Integrity."""

from __future__ import annotations

from datetime import date

from data_governance.catalog.registry import reset_registry_for_tests
from data_governance.data_access.normalization import add_calendar_months
from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.plan_value_integrity.us_states import (
    APPROVED_US_STATE_ABBREVIATIONS,
)

FIXED_TS = "2026-07-18 12:00:00"


def _patch_run_id(monkeypatch):
    monkeypatch.setattr(
        "data_governance.execution.runner.new_run_id",
        lambda now=None: ("DG-TEST-PLANVALUES", FIXED_TS),
    )


def _run(tables, tmp_path, *, item=None, rule_id=None):
    reset_registry_for_tests()
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        governance_item_id=item,
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _base_refs():
    return {
        "QuikQxs": [{"MORT": "80"}, {"MORT": "81"}],
        "QuikPlan": [{"PLAN": "ABC123"}, {"PLAN": "PLAN01"}],
        "QuikPlGd": [{"PLAN": "ABC123", "GDCODE": "M"}],
        "QuikPlUw": [{"PLAN": "ABC123", "UWCODE": "05"}],
        "QuikPlBd": [{"PLAN": "ABC123", "BDCODE": "03"}],
    }


def _pv_row(**overrides):
    row = {
        "PLAN": "ABC123",
        "GENDER": "0",
        "UWCLASS": "00",
        "BAND": "00",
        "ISSUEST": "00",
        "EFFDATE": date(2020, 1, 1),
        "MORT": "80",
        "ETIMORT": "81",
    }
    row.update(overrides)
    return row


def test_mort_pass_fail_blank_null_ambiguous_padding(tmp_path):
    tables = {
        **_base_refs(),
        "QuikPlCv": [_pv_row(MORT="80  ")],
        "QuikPlTv": [_pv_row(MORT="80")],
        "QuikPlGp": [_pv_row()],
    }
    assert _run(tables, tmp_path, rule_id="DG-PLANVALUES-001").rule_results[0].status == STATUS_PASS

    bad = {**_base_refs(), "QuikPlCv": [_pv_row(MORT="ZZ")]}
    assert _run(bad, tmp_path, rule_id="DG-PLANVALUES-001").rule_results[0].status == STATUS_FAIL

    assert (
        _run({**_base_refs(), "QuikPlCv": [_pv_row(MORT="")]}, tmp_path, rule_id="DG-PLANVALUES-001")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run({**_base_refs(), "QuikPlCv": [_pv_row(MORT=None)]}, tmp_path, rule_id="DG-PLANVALUES-001")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )

    amb = {
        **_base_refs(),
        "QuikQxs": [{"MORT": "80"}, {"MORT": "80"}],
        "QuikPlCv": [_pv_row(MORT="80")],
    }
    amb_r = _run(amb, tmp_path, rule_id="DG-PLANVALUES-001")
    assert amb_r.rule_results[0].status == STATUS_FAIL
    assert amb_r.findings[0].failure_category == "AMBIGUOUS_REFERENCE"


def test_etimort_and_plan_rules(tmp_path):
    refs = _base_refs()
    assert (
        _run({**refs, "QuikPlCv": [_pv_row(ETIMORT="81")]}, tmp_path, rule_id="DG-PLANVALUES-002")
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    fail_e = _run(
        {**refs, "QuikPlCv": [_pv_row(ETIMORT="XX")]}, tmp_path, rule_id="DG-PLANVALUES-002"
    )
    assert fail_e.rule_results[0].status == STATUS_FAIL
    assert "ETI mortality" in fail_e.findings[0].message

    tables = {
        **refs,
        "QuikPlan": [{"PLAN": "001234"}],
        "QuikPlGp": [_pv_row(PLAN="001234")],
    }
    assert _run(tables, tmp_path, rule_id="DG-PLANVALUES-003").rule_results[0].status == STATUS_PASS

    miss = {**refs, "QuikPlGp": [_pv_row(PLAN="NOSUCH")]}
    assert _run(miss, tmp_path, rule_id="DG-PLANVALUES-003").rule_results[0].status == STATUS_FAIL
    assert (
        _run({**refs, "QuikPlGp": [_pv_row(PLAN="")]}, tmp_path, rule_id="DG-PLANVALUES-003")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )


def test_gender_uwclass_band(tmp_path):
    refs = _base_refs()
    tables = {
        **refs,
        "QuikPlDb": [_pv_row(GENDER="0", UWCLASS="00", BAND="00")],
    }
    for rid in ("DG-PLANVALUES-004", "DG-PLANVALUES-005", "DG-PLANVALUES-006"):
        assert _run(tables, tmp_path, rule_id=rid).rule_results[0].status == STATUS_PASS

    valid = {
        **refs,
        "QuikPlDb": [_pv_row(GENDER="M", UWCLASS="05", BAND="03")],
    }
    for rid in ("DG-PLANVALUES-004", "DG-PLANVALUES-005", "DG-PLANVALUES-006"):
        assert _run(valid, tmp_path, rule_id=rid).rule_results[0].status == STATUS_PASS

    assert (
        _run({**refs, "QuikPlDb": [_pv_row(GENDER="3")]}, tmp_path, rule_id="DG-PLANVALUES-004")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run({**refs, "QuikPlCv": [_pv_row(UWCLASS="99")]}, tmp_path, rule_id="DG-PLANVALUES-005")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run({**refs, "QuikPlDv": [_pv_row(BAND="99")]}, tmp_path, rule_id="DG-PLANVALUES-006")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )

    z = {**refs, "QuikPlCv": [_pv_row(UWCLASS="00", BAND="00")]}
    assert _run(z, tmp_path, rule_id="DG-PLANVALUES-005").rule_results[0].status == STATUS_PASS
    assert _run(z, tmp_path, rule_id="DG-PLANVALUES-006").rule_results[0].status == STATUS_PASS

    no_gd = {
        "QuikPlan": [{"PLAN": "ABC123"}],
        "QuikPlDb": [_pv_row(GENDER="0"), _pv_row(GENDER="M")],
    }
    r = _run(no_gd, tmp_path, rule_id="DG-PLANVALUES-004")
    assert r.rule_results[0].status == STATUS_ERROR
    cats = {f.failure_category for f in r.findings}
    assert "MISSING_REFERENCE" not in cats
    assert "REFERENCE_TABLE_UNAVAILABLE" in cats


def test_issuest_states(tmp_path):
    refs = _base_refs()
    assert (
        _run({**refs, "QuikPlGp": [_pv_row(ISSUEST="00")]}, tmp_path, rule_id="DG-PLANVALUES-007")
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    assert (
        _run({**refs, "QuikPlGp": [_pv_row(ISSUEST="tx")]}, tmp_path, rule_id="DG-PLANVALUES-007")
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    assert (
        _run({**refs, "QuikPlGp": [_pv_row(ISSUEST="DC")]}, tmp_path, rule_id="DG-PLANVALUES-007")
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    for bad in ("ZZ", "X", "TEX", "PR", "GU", "", None):
        status = (
            _run({**refs, "QuikPlGp": [_pv_row(ISSUEST=bad)]}, tmp_path, rule_id="DG-PLANVALUES-007")
            .rule_results[0]
            .status
        )
        assert status == STATUS_FAIL, bad

    assert "AL" in APPROVED_US_STATE_ABBREVIATIONS
    assert "PR" not in APPROVED_US_STATE_ABBREVIATIONS
    assert len(APPROVED_US_STATE_ABBREVIATIONS) == 51


def test_effdate_bounds_and_calendar_months(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert add_calendar_months(date(2024, 2, 29), 12) == date(2025, 2, 28)
    assert add_calendar_months(date(2026, 7, 18), 12) == date(2027, 7, 18)

    refs = _base_refs()
    max_ok = date(2027, 7, 18)
    assert (
        _run(
            {**refs, "QuikPlCv": [_pv_row(EFFDATE=date(1900, 1, 1))]},
            tmp_path,
            rule_id="DG-PLANVALUES-008",
        )
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    assert (
        _run(
            {**refs, "QuikPlCv": [_pv_row(EFFDATE=max_ok)]},
            tmp_path,
            rule_id="DG-PLANVALUES-008",
        )
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    early = _run(
        {**refs, "QuikPlCv": [_pv_row(EFFDATE=date(1899, 12, 31))]},
        tmp_path,
        rule_id="DG-PLANVALUES-008",
    )
    assert early.rule_results[0].status == STATUS_FAIL
    assert early.findings[0].failure_category == "DATE_BEFORE_MINIMUM"

    late = _run(
        {**refs, "QuikPlCv": [_pv_row(EFFDATE=date(2027, 7, 19))]},
        tmp_path,
        rule_id="DG-PLANVALUES-008",
    )
    assert late.rule_results[0].status == STATUS_FAIL
    assert late.findings[0].failure_category == "DATE_AFTER_MAXIMUM"
    assert late.rule_results[0].summary_metrics["max_allowed_date"] == "2027-07-18"

    assert (
        _run(
            {**refs, "QuikPlCv": [_pv_row(EFFDATE="")]},
            tmp_path,
            rule_id="DG-PLANVALUES-008",
        )
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run(
            {**refs, "QuikPlCv": [_pv_row(EFFDATE="not-a-date")]},
            tmp_path,
            rule_id="DG-PLANVALUES-008",
        )
        .rule_results[0]
        .status
        == STATUS_FAIL
    )


def test_five_sources_independent_and_findings_not_merged(tmp_path):
    refs = _base_refs()
    tables = {
        **refs,
        "QuikPlCv": [_pv_row(PLAN="NOSUCH")],
        "QuikPlTv": [_pv_row(PLAN="NOSUCH")],
        "QuikPlGp": [_pv_row(PLAN="ABC123")],
        "QuikPlDb": [_pv_row(PLAN="ABC123")],
        "QuikPlDv": [_pv_row(PLAN="ABC123")],
    }
    r = _run(tables, tmp_path, rule_id="DG-PLANVALUES-003")
    assert r.rule_results[0].status == STATUS_FAIL
    assert r.rule_results[0].failed_count == 2
    sources = {f.source_table for f in r.findings}
    assert sources == {"QuikPlCv", "QuikPlTv"}

    partial = {
        **refs,
        "QuikPlCv": [_pv_row()],
        "QuikPlGp": [_pv_row()],
    }
    r2 = _run(partial, tmp_path, rule_id="DG-PLANVALUES-003")
    assert r2.rule_results[0].status == STATUS_PASS
    assert r2.rule_results[0].records_evaluated == 2


def test_missing_quikqxs_only_affects_mort_rules(tmp_path):
    tables = {
        "QuikPlan": [{"PLAN": "ABC123"}],
        "QuikPlGd": [{"PLAN": "ABC123", "GDCODE": "M"}],
        "QuikPlUw": [{"PLAN": "ABC123", "UWCODE": "05"}],
        "QuikPlBd": [{"PLAN": "ABC123", "BDCODE": "03"}],
        "QuikPlCv": [_pv_row()],
        "QuikPlTv": [_pv_row()],
        "QuikPlGp": [_pv_row()],
        "QuikPlDb": [_pv_row()],
        "QuikPlDv": [_pv_row()],
    }
    r = _run(tables, tmp_path, item="DG-PLANVALUES")
    by_id = {x.rule_id: x for x in r.rule_results}
    assert by_id["DG-PLANVALUES-001"].status == STATUS_ERROR
    assert by_id["DG-PLANVALUES-002"].status == STATUS_ERROR
    assert by_id["DG-PLANVALUES-003"].status == STATUS_PASS
    assert by_id["DG-PLANVALUES-007"].status == STATUS_PASS
    assert by_id["DG-PLANVALUES-008"].status == STATUS_PASS


def test_item_and_full_suite_with_fixtures(tmp_path, clean_company_tables):
    r = _run(clean_company_tables, tmp_path, item="DG-PLANVALUES")
    assert len(r.rules_executed) == 8
    assert all(x.status == STATUS_PASS for x in r.rule_results)
    assert r.source_files_modified is False
