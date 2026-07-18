"""Tests for DG-QUIKACTG-002 — QuikActg company must exist in QuikComp."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path, rule_id="DG-QUIKACTG-002"):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def test_company_exists_once_passes(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "1000"}],
    }
    assert _run(tables, tmp_path).rule_results[0].status == STATUS_PASS


def test_multiple_plans_same_valid_company_pass(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "2000"},
            {"MCOMP": "A", "MPLAN": "3000"},
        ],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS
    assert result.rule_results[0].passed_count == 3


def test_missing_company_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": "X", "MPLAN": "1000"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not exist in QuikComp" in f.message for f in result.findings)


def test_blank_company_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": "  ", "MPLAN": "1000"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a company code" in f.message for f in result.findings)


def test_null_company_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": None, "MPLAN": "1000"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].summary_metrics["null_company_references"] == 1


def test_duplicated_quikcomp_reported(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "1000"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("multiple records for company code" in f.message for f in result.findings)


def test_company_normalization_consistent_with_item1(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [{"MCOMP": " A ", "MPLAN": "1000"}],
    }
    assert _run(tables, tmp_path).rule_results[0].status == STATUS_PASS


def test_missing_quikcomp_affects_only_reference_rule(tmp_path):
    tables = {"QuikActg": [{"MCOMP": "A", "MPLAN": "1000"}]}
    r001 = _run(tables, tmp_path, rule_id="DG-QUIKACTG-001")
    r002 = _run(tables, tmp_path, rule_id="DG-QUIKACTG-002")
    assert r001.rule_results[0].status == STATUS_PASS
    assert r002.rule_results[0].status == STATUS_ERROR


def test_missing_quikactg_affects_only_accounting_rules(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKACTG-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKACTG-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKDATE-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKCOMP-001"].status == STATUS_PASS
    assert by_id["DG-QUIKMSTR-001"].status == STATUS_PASS


def test_one_failed_does_not_stop_remaining(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikActg": [
            {"MCOMP": "X", "MPLAN": "1000"},
            {"MCOMP": "A", "MPLAN": "2000"},
            {"MCOMP": "", "MPLAN": "3000"},
            {"MCOMP": "A", "MPLAN": "4000"},
        ],
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.records_evaluated == 4
    assert rule.passed_count == 2
    assert rule.failed_count == 2
