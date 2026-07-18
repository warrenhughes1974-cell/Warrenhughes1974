"""Tests for DG-QUIKMSTR-001 — Policy Number Length."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKMSTR-001",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_4_character_policy_passes(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "1234"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_8_character_policy_passes(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "12345678"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_9_character_policy_passes(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "123456789"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_10_character_policy_passes(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "1234567890"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_11_character_policy_passes(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "12345678901"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_3_character_policy_fails(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "123"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "contains 3 characters" in f.message and "between 4 and 11" in f.message
        for f in result.findings
    )


def test_12_character_policy_fails(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "123456789012"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("contains 12 characters" in f.message for f in result.findings)


def test_blank_policy_fails(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": ""}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank policy number" in f.message for f in result.findings)


def test_null_policy_fails(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": None}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("null policy number" in f.message for f in result.findings)
    assert result.rule_results[0].summary_metrics.get("null_policy_numbers") == 1


def test_leading_padding_removed(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "   123456789"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_trailing_padding_removed(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "1234567890  "}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_internal_spaces_retained_in_length(tmp_path):
    # 8 chars + 1 space + 1 char = 10 after trim of ends only → pass
    # "1234567 89" = 10 characters
    result = _run({"QuikMstr": [{"MPOLICY": "1234567 89"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS

    # "1 2" = 3 characters including internal space → fail
    result2 = _run({"QuikMstr": [{"MPOLICY": "1 2"}]}, tmp_path)
    assert result2.rule_results[0].status == STATUS_FAIL
    finding = result2.findings[0]
    assert finding.policy_number_length == "3"
    assert finding.normalized_policy_number == "1 2"


def test_original_policy_not_changed(tmp_path):
    original_row = {"MPOLICY": "  AB  "}
    tables = {"QuikMstr": [original_row]}
    result = _run(tables, tmp_path)
    assert original_row["MPOLICY"] == "  AB  "
    assert result.findings
    assert result.findings[0].original_policy_number == "  AB  "
    assert result.findings[0].normalized_policy_number == "AB"


def test_complete_policy_and_length_in_finding(tmp_path):
    result = _run({"QuikMstr": [{"MPOLICY": "ABCDEFGHIJKL"}]}, tmp_path)
    finding = result.findings[0]
    assert finding.normalized_policy_number == "ABCDEFGHIJKL"
    assert "ABCDEFGHIJKL" in finding.message
    assert finding.policy_number_length == "12"
    assert finding.min_permitted_length == "4"
    assert finding.max_permitted_length == "11"


def test_one_invalid_does_not_stop_remaining(tmp_path):
    tables = {
        "QuikMstr": [
            {"MPOLICY": "123"},  # bad short
            {"MPOLICY": "1234"},  # good 4
            {"MPOLICY": "123456789012"},  # bad long
            {"MPOLICY": "12345678901"},  # good 11
        ]
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.records_evaluated == 4
    assert rule.passed_count == 2
    assert rule.failed_count == 2
    assert rule.summary_metrics["records_shorter_than_4"] == 1
    assert rule.summary_metrics["records_longer_than_11"] == 1
