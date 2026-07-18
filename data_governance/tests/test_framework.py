"""Framework-level tests for QLAdmin Data Governance."""

from __future__ import annotations

import os

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import OVERALL_FAIL, STATUS_ERROR, STATUS_FAIL, STATUS_PASS


def test_one_rule_runs_independently(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKCOMP-001",
        write_reports=False,
        preloaded_tables=clean_company_tables,
    )
    assert result.rules_executed == ["DG-QUIKCOMP-001"]
    assert result.rule_results[0].status == STATUS_PASS


def test_one_governance_item_runs_independently(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        governance_item_id="DG-QUIKCOMP",
        write_reports=False,
        preloaded_tables=clean_company_tables,
    )
    assert result.rules_executed == [
        "DG-QUIKCOMP-001",
        "DG-QUIKCOMP-002",
        "DG-QUIKCOMP-003",
    ]
    assert result.overall_status == "PASS"


def test_all_registered_rules_run_together(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=clean_company_tables,
    )
    assert len(result.rules_executed) == 29
    assert "DG-QUIKMSTR-001" in result.rules_executed
    assert "DG-QUIKACTG-001" in result.rules_executed
    assert "DG-QUIKACTG-002" in result.rules_executed
    assert "DG-QUIKLIST-001" in result.rules_executed
    assert "DG-QUIKLIST-009" in result.rules_executed
    assert "DG-QUIKDATE-001" in result.rules_executed
    assert "DG-QUIKDATE-006" in result.rules_executed
    assert "DG-PLANVALUES-001" in result.rules_executed
    assert "DG-PLANVALUES-008" in result.rules_executed
    assert all(r.status == STATUS_PASS for r in result.rule_results)


def test_one_rule_failure_does_not_stop_others(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],  # 001 fails
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A1", "MCOMP": "A"}],  # 002 fails (dup)
        "QuikMstr": [{"MPOLICY": "123456789A"}],  # 003 fails (dup); length OK for 001 mstr
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    assert len(result.rule_results) == 29
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-001"].status == STATUS_FAIL
    assert by_id["DG-QUIKCOMP-002"].status == STATUS_FAIL
    assert by_id["DG-QUIKCOMP-003"].status == STATUS_FAIL
    assert by_id["DG-QUIKMSTR-001"].status == STATUS_PASS
    # QuikActg / QuikList / QuikDate / plan-value tables not preloaded → ERROR without stopping others
    assert by_id["DG-QUIKACTG-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKACTG-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKDATE-001"].status == STATUS_ERROR
    assert by_id["DG-PLANVALUES-001"].status == STATUS_ERROR
    assert by_id["DG-PLANVALUES-008"].status == STATUS_ERROR
    assert by_id["DG-QUIKDATE-006"].status == STATUS_ERROR
    assert result.overall_status == OVERALL_FAIL


def test_processing_errors_distinguished_from_data_failures(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-001"].status == STATUS_PASS
    assert by_id["DG-QUIKCOMP-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKCOMP-002"].error_count >= 1
    assert by_id["DG-QUIKCOMP-003"].status == STATUS_PASS
    assert by_id["DG-QUIKMSTR-001"].status == STATUS_PASS
    assert by_id["DG-QUIKACTG-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKACTG-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-001"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKDATE-001"].status == STATUS_ERROR
    assert any(f.status == STATUS_ERROR for f in result.findings)


def test_reports_and_csv_generated_consistently(tmp_path, clean_company_tables):
    out = tmp_path / "reports"
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(out),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    assert os.path.isfile(result.results_csv_path)
    assert os.path.isfile(result.findings_csv_path)
    assert os.path.isfile(result.summary_csv_path)
    assert os.path.isfile(result.report_md_path)
    assert os.path.isfile(result.validation_guide_path)
    assert os.path.isfile(result.validation_manifest_path)
    assert os.path.isfile(result.run_log_path)
    assert result.run_id in result.output_dir
    assert os.path.basename(result.results_csv_path) == "data_governance_results.csv"
    assert os.path.basename(result.findings_csv_path) == "data_governance_findings.csv"
    assert os.path.basename(result.summary_csv_path) == "data_governance_summary.csv"
    assert os.path.basename(result.report_md_path) == "data_governance_report.md"
    assert os.path.basename(result.validation_guide_path) == (
        "data_governance_validation_guide.md"
    )
    with open(result.results_csv_path, encoding="utf-8-sig") as fh:
        results_text = fh.read()
    assert "OVERALL" in results_text
    assert "Unique QuikComp Company Code" in results_text

    with open(result.report_md_path, encoding="utf-8") as fh:
        text = fh.read()
    assert "QLAdmin Data Governance Executive Summary" in text
    assert "QLAdmin Data Governance — Results (Plain Language)" in text
    assert "Bottom line" in text
    assert "Unique QuikComp Company Code" in text
    assert "Data region (full path)" in text
    assert "Data Conformance Accuracy" in text


def test_no_pass_detail_rows_for_clean_records(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=clean_company_tables,
    )
    assert result.passed_count > 0
    assert result.findings == []
