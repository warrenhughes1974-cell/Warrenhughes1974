"""Tests for DG-QUIKLIST-003 — billing name required."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKLIST-003",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_populated_billing_name_passes(tmp_path):
    result = _run({"QuikList": [{"MGROUP": "1", "MBILLNAME": "Acme"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_blank_billing_name_fails(tmp_path):
    result = _run({"QuikList": [{"MGROUP": "12345678", "MBILLNAME": ""}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a group billing name" in f.message for f in result.findings)


def test_whitespace_only_billing_name_fails(tmp_path):
    result = _run({"QuikList": [{"MGROUP": "12345678", "MBILLNAME": "   "}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL


def test_null_billing_name_fails(tmp_path):
    result = _run({"QuikList": [{"MGROUP": "12345678", "MBILLNAME": None}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL


def test_duplicate_billing_names_allowed(tmp_path):
    tables = {
        "QuikList": [
            {"MGROUP": "1", "MBILLNAME": "Same Name"},
            {"MGROUP": "2", "MBILLNAME": "Same Name"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 2
