"""Tests for simplified business-facing governance reports."""

from __future__ import annotations

import csv
import os
from datetime import date

from data_governance.execution.runner import run_data_governance
from data_governance.reporting.simplified_reports import (
    TYPE_COULD_NOT,
    TYPE_DATA_PROBLEM,
    TYPE_INFORMATION,
    build_attention_rows,
    build_business_summary,
)


def _run(tables, tmp_path, **kwargs):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=True,
        preloaded_tables=tables,
        **kwargs,
    )


def test_user_facing_files_and_internal_layout(tmp_path, clean_company_tables):
    result = _run(clean_company_tables, tmp_path)
    assert os.path.isfile(result.what_was_checked_path)
    assert os.path.isfile(result.items_needing_attention_path)
    assert os.path.basename(result.what_was_checked_path) == "1_What_Was_Checked.html"
    assert os.path.basename(result.items_needing_attention_path) == (
        "2_Items_Needing_Attention.csv"
    )
    root_names = set(os.listdir(result.output_dir))
    assert "1_What_Was_Checked.html" in root_names
    assert "2_Items_Needing_Attention.csv" in root_names
    assert "internal" in root_names
    # Technical CSVs are not at run root
    assert "data_governance_results.csv" not in root_names
    assert "data_governance_findings.csv" not in root_names
    assert os.path.isfile(result.results_csv_path)
    assert "internal" in result.results_csv_path.replace("\\", "/")


def test_html_executive_summary_and_areas(tmp_path, clean_company_tables):
    result = _run(clean_company_tables, tmp_path)
    html = open(result.what_was_checked_path, encoding="utf-8").read()
    assert "Data Governance Review" in html
    assert "Executive Summary" in html
    assert "Percentage Passed" in html
    assert "Records Checked" in html
    assert "Records Passed" in html
    assert "Problems Found" in html
    assert "Checks That Could Not Be Completed" in html
    assert "What We Checked" in html
    assert "Company Setup" in html
    assert "Group Billing" in html
    assert "Plan Values" in html
    assert "Policy Master" in html
    assert "Client Setup" in html
    assert "Policy Relationships" in html
    assert "All Active Governance Checks" in html
    # No pass-per-record dump
    assert "source_record_id" not in html
    assert "Traceback" not in html
    summary = build_business_summary(result)
    assert summary.records_checked == (
        summary.records_passed + summary.problems_found + summary.warnings_found
    )
    assert summary.overall_result == "Passed"
    assert summary.percentage_passed_display.endswith("%")


def test_clean_items_csv_information_row(tmp_path, clean_company_tables):
    result = _run(clean_company_tables, tmp_path)
    with open(result.items_needing_attention_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    assert rows[0]["Type"] == TYPE_INFORMATION
    assert "No data problems" in rows[0]["Problem"]
    assert set(rows[0].keys()) >= {
        "Area",
        "Table",
        "Record",
        "Problem",
        "Current Value",
        "Required Value",
        "Type",
        "Reference",
    }


def test_data_problems_plain_english(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [
            {
                "MGROUP": "GRP1",
                "MCOMP": "G",
                "MBILLNAME": "Acme",
                "MSORT": "P",
                "MLAPSEL": 0,
                "MLAPSEH": 0,
                "MSTATUS": "A",
                "MBILLDAY": 0,
                "MBILLMODE": 0,
            }
        ],
    }
    result = _run(tables, tmp_path, governance_item_id="DG-QUIKLIST")
    html = open(result.what_was_checked_path, encoding="utf-8").read()
    assert "Some Items Need Attention" in html or "Needs Attention" in html
    assert "Group Billing Only" in html or "Group Billing" in html
    rows = build_attention_rows(result)
    data_rows = [r for r in rows if r.type == TYPE_DATA_PROBLEM]
    assert data_rows
    assert any("Company code G was not found" in r.problem for r in data_rows)
    assert any("billing sort" in r.problem.lower() for r in data_rows)
    assert all(r.reference.startswith("DG-") for r in data_rows)
    assert not any("MISSING_REFERENCE" in r.problem for r in data_rows)
    assert not any("Traceback" in r.problem for r in data_rows)


def test_incomplete_review_wording_and_coverage(tmp_path):
    issue = date(2020, 6, 15)
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAgts": [{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "A"}],
        "QuikMstr": [
            {
                "MPOLICY": "123456789A",
                "MSTATUS": "22",
                "MSTATDATE": issue,
                "MISSDT": issue,
                "MPAIDTO": issue,
                "MBILLTO": issue,
                "MAPPDATE": issue,
                "MNFOPT": "0",
                "MBILLFRM": "1",
                "MBILLDAY": 15,
                "MMODE": "12",
                "MISSUEST": "TX",
                "MBENPID": "",
                "MBENCID": "",
                "MISSCNTRY": "0000",
                "MISSCLASS": "00",
            }
        ],
        "QuikClnt": [
            {
                "MCLIENTID": "C001",
                "MTYPE": "I",
                "MTAXIDTYPE": "S",
                "MLNAME": "Smith",
                "MFNAME": "John",
                "MADDR1": "1 Main",
                "MSEX": "M",
                "MLANGUAGE": "E",
                "MDOB": date(1980, 1, 1),
            }
        ],
        "QuikRidr": [{"MPOLICY": "123456789A", "MPHASE": 1}],
        "QuikClid": [
            {
                "MCLIENTID": "C001",
                "MPOLICY": "123456789A",
                "MRELATION": "INSD",
                "MPHASE": 1,
            }
        ],
        "QuikActg": [{"MCOMP": "A", "MPLAN": "P1"}],
        # QuikList / QuikDate / plan values missing → incomplete
    }
    result = _run(tables, tmp_path)
    summary = build_business_summary(result)
    assert summary.problems_found == 0
    assert summary.checks_incomplete > 0
    assert summary.overall_result == "Incomplete Review"
    assert summary.validation_coverage_incomplete
    html = open(result.what_was_checked_path, encoding="utf-8").read()
    assert "Incomplete Review" in html
    assert "Validation Coverage" in html
    assert "100.00%" in html or summary.percentage_passed_display == "100.00%"


def test_problems_plus_incomplete_wording(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],  # data problem
        "QuikMstr": [{"MPOLICY": "123456789A"}],
        # other tables missing
    }
    result = _run(tables, tmp_path)
    summary = build_business_summary(result)
    assert summary.problems_found > 0
    assert summary.checks_incomplete > 0
    assert summary.overall_result == "Items Need Attention and Review Is Incomplete"
    html = open(result.what_was_checked_path, encoding="utf-8").read()
    assert "Items Need Attention and Review Is Incomplete" in html


def test_missing_reference_collapses_to_one_incomplete_row(tmp_path):
    tables = {
        "QuikPlan": [{"PLAN": "ABC123"}],
        "QuikPlCv": [
            {
                "PLAN": "ABC123",
                "GENDER": "0",
                "UWCLASS": "00",
                "BAND": "00",
                "ISSUEST": "00",
                "EFFDATE": date(2020, 1, 1),
                "MORT": "80",
                "ETIMORT": "81",
            }
            for _ in range(5)
        ],
        # QuikQxs missing
    }
    result = _run(tables, tmp_path, rule_id="DG-PLANVALUES-001")
    rows = [r for r in build_attention_rows(result) if r.type == TYPE_COULD_NOT]
    assert len(rows) == 1
    assert "Mortality" in rows[0].problem or "mortality" in rows[0].problem.lower()
    assert "could not" in rows[0].problem.lower()


def test_single_rule_scope_label(tmp_path, clean_company_tables):
    result = _run(clean_company_tables, tmp_path, rule_id="DG-PLANVALUES-001")
    html = open(result.what_was_checked_path, encoding="utf-8").read()
    assert "Only" in html
    assert result.review_scope == "rule"


def test_blank_displays_as_blank_in_csv(tmp_path):
    tables = {
        "QuikList": [
            {
                "MGROUP": "G1",
                "MCOMP": "A",
                "MBILLNAME": "",
                "MSORT": "N",
                "MLAPSEL": 0,
                "MLAPSEH": 0,
                "MSTATUS": "A",
                "MBILLDAY": 0,
                "MBILLMODE": 0,
            }
        ],
        "QuikComp": [{"MCOMP": "A"}],
    }
    result = _run(tables, tmp_path, rule_id="DG-QUIKLIST-003")
    with open(result.items_needing_attention_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    data = [r for r in rows if r["Type"] == TYPE_DATA_PROBLEM]
    assert data
    # Empty current value cell is acceptable (Blank written as empty string in CSV)
    assert data[0]["Current Value"] in ("", "Blank")


def test_source_not_modified_flag(tmp_path, clean_company_tables):
    result = _run(clean_company_tables, tmp_path)
    assert result.source_files_modified is False
    assert result.source_opened_read_only is True
