"""Tests for DG-QUIKLIST-004 through 009 — default-value rules."""

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.group_billing_integrity.dg_quiklist_006_mlapseh_default import (
    MLAPSEH_FIELD,
)


def _run(tables, tmp_path, rule_id):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _base(**overrides):
    row = {
        "MGROUP": "12345678",
        "MCOMP": "A",
        "MBILLNAME": "Acme",
        "MSORT": "N",
        "MLAPSEL": 0,
        "MLAPSEH": 0,
        "MSTATUS": "A",
        "MBILLDAY": 0,
        "MBILLMODE": 0,
    }
    row.update(overrides)
    return {"QuikList": [row]}


def test_msort_n_passes(tmp_path):
    assert _run(_base(MSORT="N"), tmp_path, "DG-QUIKLIST-004").rule_results[0].status == STATUS_PASS


def test_msort_lowercase_n_passes(tmp_path):
    assert _run(_base(MSORT="n"), tmp_path, "DG-QUIKLIST-004").rule_results[0].status == STATUS_PASS


def test_msort_blank_null_other_fail(tmp_path):
    assert _run(_base(MSORT=""), tmp_path, "DG-QUIKLIST-004").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MSORT=None), tmp_path, "DG-QUIKLIST-004").rule_results[0].status == STATUS_FAIL
    result = _run(_base(MSORT="X"), tmp_path, "DG-QUIKLIST-004")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MSORT='X'" in result.findings[0].message
    assert "required governance value is 'N'" in result.findings[0].message


def test_mlapsel_zero_passes(tmp_path):
    for value in (0, 0.0, "0", "000"):
        assert (
            _run(_base(MLAPSEL=value), tmp_path, "DG-QUIKLIST-005").rule_results[0].status
            == STATUS_PASS
        )


def test_mlapsel_nonzero_and_null_blank_fail(tmp_path):
    result = _run(_base(MLAPSEL=30), tmp_path, "DG-QUIKLIST-005")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MLAPSEL='30'" in result.findings[0].message
    assert _run(_base(MLAPSEL=None), tmp_path, "DG-QUIKLIST-005").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MLAPSEL=""), tmp_path, "DG-QUIKLIST-005").rule_results[0].status == STATUS_FAIL


def test_mlapseh_zero_passes(tmp_path):
    assert _run(_base(MLAPSEH=0), tmp_path, "DG-QUIKLIST-006").rule_results[0].status == STATUS_PASS


def test_mlapseh_nonzero_and_null_blank_fail(tmp_path):
    result = _run(_base(MLAPSEH=30), tmp_path, "DG-QUIKLIST-006")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MLAPSEH='30'" in result.findings[0].message
    assert _run(_base(MLAPSEH=None), tmp_path, "DG-QUIKLIST-006").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MLAPSEH=""), tmp_path, "DG-QUIKLIST-006").rule_results[0].status == STATUS_FAIL


def test_mlapseh_field_name_not_mlaspeh():
    assert MLAPSEH_FIELD == "MLAPSEH"
    assert MLAPSEH_FIELD != "MLASPEH"
    # Implementation must read MLAPSEH, never the misspelled MLASPEH
    from data_governance.rules.group_billing_integrity import dg_quiklist_006_mlapseh_default as mod

    assert mod.MLAPSEH_FIELD == "MLAPSEH"


def test_mstatus_a_passes(tmp_path):
    assert _run(_base(MSTATUS="A"), tmp_path, "DG-QUIKLIST-007").rule_results[0].status == STATUS_PASS
    assert _run(_base(MSTATUS="a"), tmp_path, "DG-QUIKLIST-007").rule_results[0].status == STATUS_PASS


def test_mstatus_i_blank_null_fail(tmp_path):
    result = _run(_base(MSTATUS="I"), tmp_path, "DG-QUIKLIST-007")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MSTATUS='I'" in result.findings[0].message
    assert _run(_base(MSTATUS=""), tmp_path, "DG-QUIKLIST-007").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MSTATUS=None), tmp_path, "DG-QUIKLIST-007").rule_results[0].status == STATUS_FAIL


def test_mbillday_zero_passes(tmp_path):
    assert _run(_base(MBILLDAY=0), tmp_path, "DG-QUIKLIST-008").rule_results[0].status == STATUS_PASS


def test_mbillday_nonzero_blank_null_fail(tmp_path):
    result = _run(_base(MBILLDAY=15), tmp_path, "DG-QUIKLIST-008")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MBILLDAY='15'" in result.findings[0].message
    assert _run(_base(MBILLDAY=""), tmp_path, "DG-QUIKLIST-008").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MBILLDAY=None), tmp_path, "DG-QUIKLIST-008").rule_results[0].status == STATUS_FAIL


def test_mbillmode_zero_passes(tmp_path):
    assert _run(_base(MBILLMODE=0), tmp_path, "DG-QUIKLIST-009").rule_results[0].status == STATUS_PASS


def test_mbillmode_nonzero_blank_null_fail(tmp_path):
    result = _run(_base(MBILLMODE=12), tmp_path, "DG-QUIKLIST-009")
    assert result.rule_results[0].status == STATUS_FAIL
    assert "MBILLMODE='12'" in result.findings[0].message
    assert _run(_base(MBILLMODE=""), tmp_path, "DG-QUIKLIST-009").rule_results[0].status == STATUS_FAIL
    assert _run(_base(MBILLMODE=None), tmp_path, "DG-QUIKLIST-009").rule_results[0].status == STATUS_FAIL


def test_one_failed_quiklist_rule_does_not_stop_others(tmp_path):
    tables = {
        "QuikComp": [{"MCOMP": "A"}],
        "QuikList": [
            {
                "MGROUP": "12345678",
                "MCOMP": "A",
                "MBILLNAME": "Acme",
                "MSORT": "X",  # 004 fails
                "MLAPSEL": 0,
                "MLAPSEH": 0,
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
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKLIST-004"].status == STATUS_FAIL
    assert by_id["DG-QUIKLIST-001"].status == STATUS_PASS
    assert by_id["DG-QUIKLIST-005"].status == STATUS_PASS
    assert by_id["DG-QUIKLIST-009"].status == STATUS_PASS


def test_missing_quiklist_affects_only_quiklist_item(tmp_path, clean_company_tables):
    tables = dict(clean_company_tables)
    del tables["QuikList"]
    result = run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        write_reports=False,
        preloaded_tables=tables,
    )
    by_id = {r.rule_id: r for r in result.rule_results}
    assert by_id["DG-QUIKCOMP-001"].status == STATUS_PASS
    assert by_id["DG-QUIKMSTR-001"].status == STATUS_PASS
    assert by_id["DG-QUIKACTG-001"].status == STATUS_PASS
    assert by_id["DG-QUIKDATE-001"].status == STATUS_PASS
    for rid in (
        "DG-QUIKLIST-001",
        "DG-QUIKLIST-002",
        "DG-QUIKLIST-003",
        "DG-QUIKLIST-009",
    ):
        assert by_id[rid].status == STATUS_ERROR
