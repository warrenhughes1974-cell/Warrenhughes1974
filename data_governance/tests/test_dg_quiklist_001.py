"""Tests for DG-QUIKLIST-001 — unique QuikList group number."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKLIST-001",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_unique_group_numbers_pass(tmp_path):
    tables = {"QuikList": [{"MGROUP": "12345678"}, {"MGROUP": "87654321"}]}
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_duplicate_group_numbers_fail(tmp_path):
    tables = {"QuikList": [{"MGROUP": "12345678"}, {"MGROUP": "12345678"}]}
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("contains 2 records for group number '12345678'" in f.message for f in result.findings)
    assert result.rule_results[0].summary_metrics["duplicate_group_numbers"] == 1
    assert result.rule_results[0].summary_metrics["records_involved_in_duplicates"] == 2


def test_blank_mgroup_fails(tmp_path):
    result = _run({"QuikList": [{"MGROUP": ""}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank group number" in f.message for f in result.findings)


def test_null_mgroup_fails(tmp_path):
    result = _run({"QuikList": [{"MGROUP": None}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("null group number" in f.message for f in result.findings)


def test_leading_zeros_preserved(tmp_path):
    tables = {"QuikList": [{"MGROUP": "00123456"}, {"MGROUP": "123456"}]}
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].summary_metrics["distinct_group_numbers"] == 2


def test_dbf_padding_removed(tmp_path):
    tables = {"QuikList": [{"MGROUP": "  12345678  "}]}
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_mgroup_not_converted_to_number(tmp_path):
    # String leading-zero groups must stay distinct from numeric-looking peers
    tables = {
        "QuikList": [
            {"MGROUP": "00001234"},
            {"MGROUP": "1234"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 2
