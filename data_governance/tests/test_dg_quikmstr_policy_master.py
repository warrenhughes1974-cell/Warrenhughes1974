"""Tests for DG-QUIKMSTR Policy Master integrity (001 unique/length and 002–026)."""

from __future__ import annotations

from datetime import date, timedelta

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS

_ISSUE = date(2020, 6, 15)


def _run(tables, tmp_path, *, rule_id):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _valid_mstr(**overrides):
    row = {
        "MPOLICY": "POL001A",
        "MSTATUS": "22",
        "MSTATDATE": _ISSUE,
        "MISSDT": _ISSUE,
        "MPAIDTO": _ISSUE,
        "MBILLTO": _ISSUE,
        "MAPPDATE": _ISSUE,
        "MNFOPT": "0",
        "MDIVOPT": "BAD",
        "MBILLFRM": "1",
        "MBILLDAY": 15,
        "MBANKNO": "",
        "MMODE": "12",
        "MISSUEST": "TX",
        "MGROUP": "",
        "MPRIMID": "",
        "MOWNRID": "",
        "MASGNID": "",
        "MPAYRID": "",
        "MOWNCID": "",
        "MBENPID": "",
        "MBENCID": "",
        "MISSCNTRY": "0000",
        "MRESSTATE": "INVALID",
        "MISSCLASS": "00",
    }
    row.update(overrides)
    return row


def _mstr_tables(*rows, **extra):
    tables = {"QuikMstr": list(rows) if rows else [_valid_mstr()]}
    tables.update(extra)
    return tables


def test_unique_policy_passes(tmp_path):
    tables = _mstr_tables(
        _valid_mstr(MPOLICY="POL001A"),
        _valid_mstr(MPOLICY="POL002A"),
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-001")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_duplicate_policy_fails(tmp_path):
    tables = _mstr_tables(
        _valid_mstr(MPOLICY="POL001A"),
        _valid_mstr(MPOLICY="POL001A"),
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-001")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("must be unique" in f.message for f in result.findings)


def test_blank_policy_fails_unique_length(tmp_path):
    result = _run(_mstr_tables(_valid_mstr(MPOLICY="")), tmp_path, rule_id="DG-QUIKMSTR-001")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank policy number" in f.message for f in result.findings)


def test_status_valid_passes(tmp_path):
    result = _run(_mstr_tables(), tmp_path, rule_id="DG-QUIKMSTR-002")
    assert result.rule_results[0].status == STATUS_PASS


def test_status_blank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MSTATUS="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-002",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank policy status" in f.message for f in result.findings)


def test_status_invalid_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MSTATUS="99")),
        tmp_path,
        rule_id="DG-QUIKMSTR-002",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("unapproved status" in f.message for f in result.findings)


def test_issue_date_valid_passes(tmp_path):
    result = _run(_mstr_tables(), tmp_path, rule_id="DG-QUIKMSTR-004")
    assert result.rule_results[0].status == STATUS_PASS


def test_issue_date_blank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MISSDT="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-004",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank MISSDT" in f.message for f in result.findings)


def test_paid_to_before_issue_fails(tmp_path):
    earlier = _ISSUE - timedelta(days=30)
    result = _run(
        _mstr_tables(_valid_mstr(MPAIDTO=earlier)),
        tmp_path,
        rule_id="DG-QUIKMSTR-005",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("wrong order" in f.message for f in result.findings)


def test_mnfopt_zero_passes(tmp_path):
    result = _run(_mstr_tables(), tmp_path, rule_id="DG-QUIKMSTR-008")
    assert result.rule_results[0].status == STATUS_PASS


def test_mnfopt_blank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MNFOPT="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-008",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank MNFOPT" in f.message for f in result.findings)


def test_billday_blank_with_valid_issue_passes(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MBILLDAY="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-011",
    )
    assert result.rule_results[0].status == STATUS_PASS


def test_bank_draft_without_bank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MBILLFRM="2", MBANKNO="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-012",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("bank draft" in f.message.lower() for f in result.findings)


def test_issue_state_blank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MISSUEST="")),
        tmp_path,
        rule_id="DG-QUIKMSTR-014",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank issue state" in f.message for f in result.findings)


def test_beneficiary_id_nonblank_fails(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MBENPID="BEN001")),
        tmp_path,
        rule_id="DG-QUIKMSTR-021",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("MBENPID" in f.message for f in result.findings)


def test_dividend_option_deferred_passes(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MDIVOPT="INVALID")),
        tmp_path,
        rule_id="DG-QUIKMSTR-009",
    )
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_residence_state_deferred_passes(tmp_path):
    result = _run(
        _mstr_tables(_valid_mstr(MRESSTATE="ZZ")),
        tmp_path,
        rule_id="DG-QUIKMSTR-025",
    )
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []
