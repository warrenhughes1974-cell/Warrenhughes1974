"""Tests for Executive Summary, Data Conformance Accuracy, and validation guide."""

from __future__ import annotations

import json
import os

from data_governance.execution.runner import run_data_governance
from data_governance.models.findings import GovernanceRunResult, RuleExecutionResult
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_NOT_RUN, STATUS_PASS
from data_governance.reporting.accuracy import (
    ACCURACY_MEANING,
    ACCURACY_UNAVAILABLE_RECONCILE,
    ACCURACY_UNAVAILABLE_ZERO,
    RECONCILE_WARNING,
    calculate_conformance_accuracy,
)
from data_governance.reporting.executive_summary import build_executive_summary_lines
from data_governance.reporting.report_writer import attach_conformance_metrics


def test_accuracy_15198_of_15213():
    acc = calculate_conformance_accuracy(
        records_reviewed=15213, looked_fine=15198, problems_found=15
    )
    assert acc.reconciles
    assert abs(acc.percent_raw - 99.9014001183) < 1e-9
    assert acc.percent_display == "99.90%"
    # Stored raw retains greater precision than display
    assert len(f"{acc.percent_raw}") > len("99.90")


def test_accuracy_100_percent():
    acc = calculate_conformance_accuracy(
        records_reviewed=100, looked_fine=100, problems_found=0
    )
    assert acc.percent_display == "100.00%"
    assert acc.percent_raw == 100.0


def test_accuracy_zero_percent():
    acc = calculate_conformance_accuracy(
        records_reviewed=100, looked_fine=0, problems_found=100
    )
    assert acc.percent_display == "0.00%"
    assert acc.percent_raw == 0.0


def test_accuracy_zero_reviewed():
    acc = calculate_conformance_accuracy(
        records_reviewed=0, looked_fine=0, problems_found=0
    )
    assert acc.percent_raw is None
    assert acc.percent_display == ACCURACY_UNAVAILABLE_ZERO


def test_accuracy_non_reconciling():
    acc = calculate_conformance_accuracy(
        records_reviewed=10, looked_fine=7, problems_found=2
    )
    assert acc.percent_raw is None
    assert acc.percent_display == ACCURACY_UNAVAILABLE_RECONCILE
    assert acc.warning == RECONCILE_WARNING


def test_accuracy_warnings_excluded_from_percentage():
    acc = calculate_conformance_accuracy(
        records_reviewed=100, looked_fine=90, problems_found=5, warnings_found=5
    )
    assert acc.reconciles
    assert abs(acc.percent_raw - (90 / 95 * 100.0)) < 1e-9
    assert acc.percent_display == "94.74%"


def test_error_not_run_do_not_create_false_problem_counts(tmp_path):
    # Missing QuikAgts/QuikActg/QuikList → ERROR with 0 evaluated problems
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikMstr": [{"MPOLICY": "123456789A"}],
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=tables,
    )
    # ERROR rules contribute 0 records_evaluated / failed_count
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKCOMP-002"].records_evaluated == 0
    assert by_id["DG-QUIKCOMP-002"].failed_count == 0
    assert result.records_evaluated == (
        result.passed_count + result.failed_count + result.warn_count
    )
    assert result.data_conformance_accuracy_display.endswith("%")


def test_executive_summary_at_beginning(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    text = open(result.report_md_path, encoding="utf-8").read()
    assert text.startswith("# QLAdmin Data Governance Executive Summary")
    assert "Overall Result" in text
    assert "Rules Passed" in text
    assert "Rules Failed" in text
    assert "Total Records Reviewed" in text
    assert "Problems Found" in text
    assert "Data Conformance Accuracy" in text
    assert ACCURACY_MEANING in text
    assert "Top Issues" in text
    # Detail report follows executive summary
    assert text.index("Executive Summary") < text.index(
        "QLAdmin Data Governance — Results (Plain Language)"
    )


def test_executive_summary_includes_top_issues_on_fail(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [
            {
                "MGROUP": "1",
                "MCOMP": "X",
                "MBILLNAME": "N",
                "MSORT": "X",
                "MLAPSEL": 1,
                "MLAPSEH": 1,
                "MSTATUS": "A",
                "MBILLDAY": 0,
                "MBILLMODE": 0,
            }
        ],
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        governance_item_id="DG-QUIKLIST",
        write_reports=True,
        preloaded_tables=tables,
    )
    text = open(result.report_md_path, encoding="utf-8").read()
    assert "Top Issues" in text
    assert "1." in text


def test_validation_companion_created(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    assert os.path.isfile(result.validation_guide_path)
    assert os.path.basename(result.validation_guide_path) == (
        "data_governance_validation_guide.md"
    )
    guide = open(result.validation_guide_path, encoding="utf-8").read()
    assert "QLAdmin Data Governance Validation Guide" in guide
    assert "DG-QUIKCOMP-001" in guide
    assert "DG-QUIKLIST-001" in guide
    assert "What This Governance Run Does Not Prove" in guide
    assert "did not change any source data" in guide.lower() or "not change any source" in guide
    assert "Source files modified | No" in guide or "Source files modified | **No**" in guide or (
        "Source files modified | No" in guide.replace("**", "")
    )
    # Every executed rule appears
    for rule_id in result.rules_executed:
        assert rule_id in guide
    # Unregistered fake rule must not appear
    assert "DG-FAKE-999" not in guide
    # Metadata includes guide path
    run_json = os.path.join(result.output_dir, "internal", "data_governance_run.json")
    meta = json.load(open(run_json, encoding="utf-8"))
    assert meta["validation_guide_path"] == result.validation_guide_path
    assert meta["Validation_Guide_File"] == "data_governance_validation_guide.md"
    assert meta.get("what_was_checked_path") == result.what_was_checked_path


def test_validation_guide_explains_error_rules(tmp_path):
    tables = {"QuikComp": [{"MCOMP": "A"}]}
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=tables,
    )
    guide = open(result.validation_guide_path, encoding="utf-8").read()
    assert "Rules Not Executed or Not Completed" in guide
    assert "DG-QUIKLIST-001" in guide
    assert "ERROR" in guide


def test_validation_manifest_json(tmp_path, clean_company_tables):
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    assert os.path.isfile(result.validation_manifest_path)
    manifest = json.load(open(result.validation_manifest_path, encoding="utf-8"))
    assert manifest["run_id"] == result.run_id
    assert len(manifest["rules_executed"]) == len(result.rules_executed)
    statuses = {e["rule_id"]: e["execution_status"] for e in manifest["rules_executed"]}
    assert statuses["DG-QUIKCOMP-001"] == STATUS_PASS
    assert set(statuses) == set(result.rules_executed)
    # Partial run lists unselected catalog rules separately
    result2 = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out2"),
        rule_id="DG-QUIKCOMP-001",
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    m2 = json.load(open(result2.validation_manifest_path, encoding="utf-8"))
    assert len(m2["rules_executed"]) == 1
    assert m2["rules_executed"][0]["rule_id"] == "DG-QUIKCOMP-001"
    assert any(e["rule_id"] == "DG-QUIKLIST-001" for e in m2["rules_not_selected"])
    assert all(e["execution_status"] == STATUS_NOT_RUN for e in m2["rules_not_selected"])


def test_results_csv_overall_has_accuracy_fields(tmp_path, clean_company_tables):
    import csv

    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    with open(result.results_csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    overall = rows[0]
    assert overall["Row_Type"] == "OVERALL"
    assert overall["Data_Conformance_Accuracy_Display"].endswith("%")
    assert overall["Validation_Guide_File"] == "data_governance_validation_guide.md"
    assert overall["Rules_Executed"] == str(len(result.rules_executed))
    # CHECK rows leave overall percent blank (no misleading per-row overall %)
    check = next(r for r in rows if r["Row_Type"] == "CHECK")
    assert check["Data_Conformance_Accuracy_Display"] == ""


def test_summary_csv_has_overall_row(tmp_path, clean_company_tables):
    import csv

    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=clean_company_tables,
    )
    with open(result.summary_csv_path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["rule_id"] == "OVERALL"
    assert rows[0]["Data_Conformance_Accuracy_Display"].endswith("%")


def test_non_reconciling_accuracy_in_report():
    result = GovernanceRunResult(
        run_id="DG-TEST",
        run_timestamp="2026-07-18 10:00:00",
        data_dir="X:\\data",
        output_dir="X:\\out",
        overall_status="FAIL",
        records_evaluated=10,
        passed_count=7,
        failed_count=2,
        rule_results=[
            RuleExecutionResult(
                governance_item_id="DG-QUIKCOMP",
                rule_id="DG-QUIKCOMP-001",
                rule_name="t",
                business_name="b",
                severity="Critical",
                status=STATUS_FAIL,
                records_evaluated=10,
                passed_count=7,
                failed_count=2,
            )
        ],
    )
    accuracy = attach_conformance_metrics(result)
    lines = build_executive_summary_lines(result, accuracy)
    text = "\n".join(lines)
    assert ACCURACY_UNAVAILABLE_RECONCILE in text
    assert RECONCILE_WARNING in text
    assert result.data_conformance_accuracy_percent is None
