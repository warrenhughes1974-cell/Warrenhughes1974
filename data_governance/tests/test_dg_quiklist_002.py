"""Tests for DG-QUIKLIST-002 — QuikList company must exist in QuikComp."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.company_code_integrity.company_code_index import (
    build_company_code_index,
)


def _run(tables, tmp_path, rule_id="DG-QUIKLIST-002"):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def test_existing_company_code_passes(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [{"MGROUP": "12345678", "MCOMP": "A"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_missing_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [{"MGROUP": "12345678", "MCOMP": "X"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not exist in QuikComp" in f.message for f in result.findings)


def test_blank_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [{"MGROUP": "12345678", "MCOMP": ""}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a company code" in f.message for f in result.findings)


def test_null_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [{"MGROUP": "12345678", "MCOMP": None}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not contain a company code" in f.message for f in result.findings)


def test_duplicate_quikcomp_reference_reported(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "A"}],
        "QuikList": [{"MGROUP": "12345678", "MCOMP": "A"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_FAIL
    finding = result.findings[0]
    assert "multiple records for company code 'A'" in finding.message
    assert finding.reference_match_count == "2"


def test_reuses_shared_quikcomp_index(tmp_path):
    # Same index builder used by Item 1 / accounting
    index = build_company_code_index([{"MCOMP": "A"}, {"MCOMP": "B"}])
    assert index.exists_once("A")
    tables = {
        "QuikComp": [{"MCOMP": "A"}, {"MCOMP": "B"}],
        "QuikList": [{"MGROUP": "1", "MCOMP": "B"}],
    }
    result = _run(tables, tmp_path)
    assert result.rule_results[0].status == STATUS_PASS


def test_missing_quikcomp_errors_only_002(tmp_path):
    tables = {
        "QuikList": [
            {
                "MGROUP": "12345678",
                "MCOMP": "A",
                "MBILLNAME": "Name",
                "MSORT": "N",
                "MLAPSEL": 0,
                "MLAPSEH": 0,
                "MSTATUS": "A",
                "MBILLDAY": 0,
                "MBILLMODE": 0,
            }
        ]
    }
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        governance_item_id="DG-QUIKLIST",
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKLIST-002"].status == STATUS_ERROR
    assert by_id["DG-QUIKLIST-001"].status == STATUS_PASS
    assert by_id["DG-QUIKLIST-003"].status == STATUS_PASS
    assert by_id["DG-QUIKLIST-004"].status == STATUS_PASS
