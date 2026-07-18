"""Tests for DG-QUIKCOMP-001 — Unique QuikComp Company Code."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS


def _run(tables, tmp_path):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id="DG-QUIKCOMP-001",
        write_reports=False,
        preloaded_tables=tables,
    )


def test_unique_company_codes_pass(tmp_path):
    tables = {
        "QuikComp": [
            {"MCOMP": "A"},
            {"MCOMP": "B"},
        ]
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.status == STATUS_PASS
    assert rule.failed_count == 0
    assert rule.passed_count == 2
    assert result.findings == []


def test_duplicate_company_codes_fail(tmp_path):
    tables = {
        "QuikComp": [
            {"MCOMP": "A"},
            {"MCOMP": "A"},
            {"MCOMP": "B"},
        ]
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.status == STATUS_FAIL
    messages = [f.message for f in result.findings]
    assert any("Duplicate company code 'A' exists 2 times" in m for m in messages)
    assert all(f.duplicate_count == "2" for f in result.findings if f.company_code == "A")


def test_blank_company_code_fails(tmp_path):
    tables = {
        "QuikComp": [
            {"MCOMP": "A"},
            {"MCOMP": "   "},
            {"MCOMP": None},
        ]
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.status == STATUS_FAIL
    blank_msgs = [f.message for f in result.findings if "blank company code" in f.message]
    assert len(blank_msgs) == 2


def test_dbf_padded_values_normalized(tmp_path):
    tables = {
        "QuikComp": [
            {"MCOMP": "A "},
            {"MCOMP": " A"},
        ]
    }
    result = _run(tables, tmp_path)
    rule = result.rule_results[0]
    assert rule.status == STATUS_FAIL
    assert any(f.company_code == "A" and f.duplicate_count == "2" for f in result.findings)
