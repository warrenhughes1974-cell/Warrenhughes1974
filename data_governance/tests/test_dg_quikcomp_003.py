"""Tests for DG-QUIKCOMP-003 — Policy Company Code Must Exist."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKCOMP-003",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_policy_ending_valid_company_code_passes(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_policy_ending_missing_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789X"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "Policy '123456789X' has company code 'X', but 'X' does not exist in QuikComp."
        in f.message
        for f in result.findings
    )


def test_blank_policy_number_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": ""}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("could not be derived from policy number" in f.message for f in result.findings)


def test_padded_policy_number_handled(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A   "}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 1


def test_duplicate_quikcomp_reference_reported(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any(
        "Policy '123456789A' references company code 'A', but QuikComp contains duplicate"
        in f.message
        for f in result.findings
    )


def test_full_policy_number_retained_in_finding(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "ABCDEFGHIJ"}],
    }
    result = _run(tables, tmp_path)
    assert result.findings
    finding = result.findings[0]
    assert finding.policy_number == "ABCDEFGHIJ"
    assert finding.company_code == "J"
    assert "ABCDEFGHIJ" in finding.message
