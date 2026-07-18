"""Tests for DG-QUIKACTG-001 — unique QuikActg MCOMP + MPLAN."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKACTG-001",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_one_company_one_plan_passes(tmp_path):
    result = _run({"QuikActg": [{"MCOMP": "A", "MPLAN": "1000"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_one_company_multiple_plans_passes(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "2000"},
            {"MCOMP": "A", "MPLAN": "3000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 3


def test_different_companies_same_plan_pass(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "B", "MPLAN": "1000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_exact_duplicate_fails(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "1000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("contains 2 records" in f.message for f in result.findings)


def test_three_duplicates_count_3(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "1000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert all(f.duplicate_count == "3" for f in result.findings if f.duplicate_count)
    assert result.rule_results[0].summary_metrics["duplicate_combinations"] == 1
    assert result.rule_results[0].summary_metrics["records_involved_in_duplicates"] == 3


def test_plan_not_globally_unique(tmp_path):
    # Same plan under A and B is valid — proves plan is not globally unique
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "B", "MPLAN": "1000"},
            {"MCOMP": "C", "MPLAN": "1000"},
        ]
    }
    assert _run(tables, tmp_path).rule_results[0].status == STATUS_PASS


def test_company_not_unique_by_itself(tmp_path):
    # Company A with three plans — company alone is not required unique
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "2000"},
            {"MCOMP": "A", "MPLAN": "3000"},
        ]
    }
    assert _run(tables, tmp_path).rule_results[0].status == STATUS_PASS


def test_leading_zeros_preserved_as_distinct(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "001000"},
            {"MCOMP": "A", "MPLAN": "1000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 2


def test_trailing_padding_removed(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A ", "MPLAN": "1000  "},
            {"MCOMP": "A", "MPLAN": "2000"},
        ]
    }
    assert _run(tables, tmp_path).rule_results[0].status == STATUS_PASS


def test_blank_company_fails(tmp_path):
    result = _run({"QuikActg": [{"MCOMP": "", "MPLAN": "1000"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a company code" in f.message for f in result.findings)


def test_null_company_fails(tmp_path):
    result = _run({"QuikActg": [{"MCOMP": None, "MPLAN": "1000"}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert result.rule_results[0].summary_metrics["null_company_codes"] == 1


def test_blank_plan_fails(tmp_path):
    result = _run({"QuikActg": [{"MCOMP": "A", "MPLAN": ""}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a plan code" in f.message for f in result.findings)


def test_null_plan_fails(tmp_path):
    result = _run({"QuikActg": [{"MCOMP": "A", "MPLAN": None}]}, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert result.rule_results[0].summary_metrics["null_account_numbers"] == 1


def test_internal_characters_preserved(tmp_path):
    tables = {
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "10-00"},
            {"MCOMP": "A", "MPLAN": "1000"},
        ]
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_source_rows_not_modified(tmp_path):
    row = {"MCOMP": "A", "MPLAN": "1000"}
    tables = {"QuikActg": [row]}
    _run(tables, tmp_path)
    assert row == {"MCOMP": "A", "MPLAN": "1000"}
