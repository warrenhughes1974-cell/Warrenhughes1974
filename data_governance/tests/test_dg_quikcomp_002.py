"""Tests for DG-QUIKCOMP-002 — Agent Company Code Must Exist."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKCOMP-002",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_agent_company_code_exists_passes(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "B"}],
        "QuikAgts": [
            {"MAGENT": "10001", "MAGTNAME": "Agent One", "MCOMP": "A"},
        ],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_missing_agent_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [
            {"MAGENT": "12345", "MAGTNAME": "Missing Co", "MCOMP": "Z"},
        ],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "Agent '12345' uses company code 'Z', but 'Z' does not exist in QuikComp."
        in f.message
        for f in result.findings
    )


def test_blank_agent_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [
            {"MAGENT": "12345", "MAGTNAME": "No Code", "MCOMP": ""},
        ],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "Agent '12345' does not have a company code." in f.message
        for f in result.findings
    )


def test_duplicate_quikcomp_reference_reported(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],
        "QuikAgts": [
            {"MAGENT": "12345", "MAGTNAME": "Dup Ref", "MCOMP": "A"},
        ],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "Agent '12345' references company code 'A', but QuikComp contains duplicate"
        in f.message
        for f in result.findings
    )


def test_multiple_agents_one_valid_company_code_pass(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [
            {"MAGENT": "1", "MAGTNAME": "One", "MCOMP": "A"},
            {"MAGENT": "2", "MAGTNAME": "Two", "MCOMP": "A"},
            {"MAGENT": "3", "MAGTNAME": "Three", "MCOMP": "A"},
        ],
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.status == STATUS_PASS
    assert rule.passed_count == 3
    assert rule.failed_count == 0
