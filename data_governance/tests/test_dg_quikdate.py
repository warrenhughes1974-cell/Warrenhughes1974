"""Tests for DG-QUIKDATE — QuikDate Processing Date Integrity."""

from __future__ import annotations

from datetime import date, timedelta

from data_governance.data_access.normalization import prior_month_end
from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS


FIXED_TS = "2026-07-18 10:00:00"
FIXED_PME = date(2026, 6, 30)


def _patch_run_id(monkeypatch):
    monkeypatch.setattr(
        "data_governance.execution.runner.new_run_id",
        lambda now=None: ("DG-TEST-QUIKDATE", FIXED_TS),
    )


def _row(**overrides):
    base = {
        "PACBILL": FIXED_PME,
        "DIRBILL": FIXED_PME,
        "REINBILL": FIXED_PME,
        "ACHFILEID": 0,
        "ACHFILEID2": "A",
        "ESC_DATE": None,
    }
    base.update(overrides)
    return {"QuikDate": [base]}


def _run(tables, tmp_path, rule_id=None, item=None):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        governance_item_id=item,
        write_reports=False,
        preloaded_tables=tables,
    )


def test_prior_month_end_calculation():
    assert prior_month_end(date(2026, 7, 18)) == date(2026, 6, 30)
    assert prior_month_end(date(2026, 3, 1)) == date(2026, 2, 28)
    assert prior_month_end(date(2024, 3, 1)) == date(2024, 2, 29)
    assert prior_month_end(date(2027, 1, 10)) == date(2026, 12, 31)


def test_pac_bill_exact_prior_month_end_passes(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    result = _run(_row(PACBILL=FIXED_PME), tmp_path, rule_id="DG-QUIKDATE-001")
    assert result.rule_results[0].status == STATUS_PASS


def test_pac_bill_one_day_early_fails(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    result = _run(_row(PACBILL=date(2026, 6, 29)), tmp_path, rule_id="DG-QUIKDATE-001")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "2026-06-29" in result.findings[0].message
    assert "2026-06-30" in result.findings[0].message


def test_pac_bill_one_day_late_and_current_month_end_fail(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    late = _run(_row(PACBILL=date(2026, 7, 1)), tmp_path, rule_id="DG-QUIKDATE-001")
    assert late.rule_results[0].status == STATUS_FAIL
    cur = _run(_row(PACBILL=date(2026, 7, 31)), tmp_path, rule_id="DG-QUIKDATE-001")
    assert cur.rule_results[0].status == STATUS_FAIL


def test_pac_bill_blank_null_invalid_fail(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_row(PACBILL=""), tmp_path, rule_id="DG-QUIKDATE-001").rule_results[0].status == STATUS_FAIL
    assert _run(_row(PACBILL=None), tmp_path, rule_id="DG-QUIKDATE-001").rule_results[0].status == STATUS_FAIL
    bad = _run(_row(PACBILL="not-a-date"), tmp_path, rule_id="DG-QUIKDATE-001")
    assert bad.rule_results[0].status == STATUS_FAIL
    assert "unreadable" in bad.findings[0].message.lower() or "invalid" in bad.findings[0].message.lower()


def test_direct_and_reinsurance_bill_rules(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_row(DIRBILL=FIXED_PME), tmp_path, rule_id="DG-QUIKDATE-002").rule_results[0].status == STATUS_PASS
    fail_d = _run(_row(DIRBILL=date(2026, 5, 31)), tmp_path, rule_id="DG-QUIKDATE-002")
    assert fail_d.rule_results[0].status == STATUS_FAIL
    assert "Direct Bill" in fail_d.findings[0].message

    assert _run(_row(REINBILL=FIXED_PME), tmp_path, rule_id="DG-QUIKDATE-003").rule_results[0].status == STATUS_PASS
    fail_r = _run(_row(REINBILL=date(2026, 7, 1)), tmp_path, rule_id="DG-QUIKDATE-003")
    assert fail_r.rule_results[0].status == STATUS_FAIL
    assert "Reinsurance Bill" in fail_r.findings[0].message


def test_achfileid_zero_and_failures(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_row(ACHFILEID=0), tmp_path, rule_id="DG-QUIKDATE-004").rule_results[0].status == STATUS_PASS
    assert _run(_row(ACHFILEID=4), tmp_path, rule_id="DG-QUIKDATE-004").rule_results[0].status == STATUS_FAIL
    assert _run(_row(ACHFILEID=""), tmp_path, rule_id="DG-QUIKDATE-004").rule_results[0].status == STATUS_FAIL
    assert _run(_row(ACHFILEID=None), tmp_path, rule_id="DG-QUIKDATE-004").rule_results[0].status == STATUS_FAIL


def test_achfileid2_a_and_failures(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_row(ACHFILEID2="A"), tmp_path, rule_id="DG-QUIKDATE-005").rule_results[0].status == STATUS_PASS
    assert _run(_row(ACHFILEID2="a"), tmp_path, rule_id="DG-QUIKDATE-005").rule_results[0].status == STATUS_PASS
    bad = _run(_row(ACHFILEID2="B"), tmp_path, rule_id="DG-QUIKDATE-005")
    assert bad.rule_results[0].status == STATUS_FAIL
    assert "ACHFILEID2 contains 'B'" in bad.findings[0].message
    assert _run(_row(ACHFILEID2=""), tmp_path, rule_id="DG-QUIKDATE-005").rule_results[0].status == STATUS_FAIL
    assert _run(_row(ACHFILEID2=None), tmp_path, rule_id="DG-QUIKDATE-005").rule_results[0].status == STATUS_FAIL


def test_escdate_blank_and_populated(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_row(ESC_DATE=None), tmp_path, rule_id="DG-QUIKDATE-006").rule_results[0].status == STATUS_PASS
    assert _run(_row(ESC_DATE=""), tmp_path, rule_id="DG-QUIKDATE-006").rule_results[0].status == STATUS_PASS
    bad = _run(_row(ESC_DATE=FIXED_PME), tmp_path, rule_id="DG-QUIKDATE-006")
    assert bad.rule_results[0].status == STATUS_FAIL
    assert "2026-06-30" in bad.findings[0].message
    assert bad.findings[0].source_field == "ESC_DATE"
    invalid = _run(_row(ESC_DATE="xx"), tmp_path, rule_id="DG-QUIKDATE-006")
    assert invalid.rule_results[0].status == STATUS_FAIL


def test_one_failed_rule_does_not_stop_others(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    tables = _row(PACBILL=date(2026, 6, 29))  # 001 fails; others pass
    result = _run(tables, tmp_path, item="DG-QUIKDATE")
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKDATE-001"].status == STATUS_FAIL
    assert by_id["DG-QUIKDATE-002"].status == STATUS_PASS
    assert by_id["DG-QUIKDATE-006"].status == STATUS_PASS
    assert len(result.rules_executed) == 6


def test_missing_quikdate_affects_only_quikdate(tmp_path, clean_company_tables):
    tables = dict(clean_company_tables)
    del tables["QuikDate"]
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-001"].status == STATUS_PASS
    assert by_id["DG-QUIKLIST-001"].status == STATUS_PASS
    assert by_id["DG-QUIKDATE-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKDATE-006"].status == STATUS_ERROR


def test_achfileid_fields_are_separate():
    from data_governance.config.settings import (
        QUIKDATE_ACHFILEID2_FIELD,
        QUIKDATE_ACHFILEID_FIELD,
    )

    assert QUIKDATE_ACHFILEID_FIELD == "ACHFILEID"
    assert QUIKDATE_ACHFILEID2_FIELD == "ACHFILEID2"
    assert QUIKDATE_ACHFILEID_FIELD != QUIKDATE_ACHFILEID2_FIELD
