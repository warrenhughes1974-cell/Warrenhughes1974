"""Tests for DG-QUIKCLID — Policy Relationship integrity."""

from __future__ import annotations

from datetime import date

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS

_POLICY = "POL001A"
_CLIENT = "C001"
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
        "MPOLICY": _POLICY,
        "MSTATUS": "22",
        "MSTATDATE": _ISSUE,
        "MISSDT": _ISSUE,
        "MPAIDTO": _ISSUE,
        "MBILLTO": _ISSUE,
        "MAPPDATE": _ISSUE,
        "MNFOPT": "0",
        "MBILLFRM": "1",
        "MBILLDAY": 15,
        "MMODE": "12",
        "MISSUEST": "TX",
        "MISSCNTRY": "0000",
        "MISSCLASS": "00",
    }
    row.update(overrides)
    return row


def _valid_client(**overrides):
    row = {
        "MCLIENTID": _CLIENT,
        "MTYPE": "I",
        "MTAXIDTYPE": "S",
        "MLNAME": "Smith",
        "MFNAME": "John",
        "MADDR1": "123 Main St",
        "MLANGUAGE": "E",
        "MSEX": "M",
    }
    row.update(overrides)
    return row


def _valid_clid(**overrides):
    row = {
        "MCLIENTID": _CLIENT,
        "MPOLICY": _POLICY,
        "MRELATION": "OWNR",
        "MPHASE": 0,
    }
    row.update(overrides)
    return row


def _base_tables(**clid_overrides):
    return {
        "QuikClnt": [_valid_client()],
        "QuikMstr": [_valid_mstr()],
        "QuikRidr": [{"MPOLICY": _POLICY, "MPHASE": 1}],
        "QuikClid": [_valid_clid(**clid_overrides)],
    }


def test_missing_client_fails(tmp_path):
    tables = _base_tables()
    tables["QuikClid"] = [_valid_clid(MCLIENTID="MISSING")]
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-001")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not exist in QuikClnt" in f.message for f in result.findings)


def test_valid_client_passes(tmp_path):
    result = _run(_base_tables(), tmp_path, rule_id="DG-QUIKCLID-001")
    assert result.rule_results[0].status == STATUS_PASS


def test_missing_policy_fails(tmp_path):
    tables = _base_tables()
    tables["QuikClid"] = [_valid_clid(MPOLICY="NOPE1234")]
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-002")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not exist in QuikMstr" in f.message for f in result.findings)


def test_valid_policy_passes(tmp_path):
    result = _run(_base_tables(), tmp_path, rule_id="DG-QUIKCLID-002")
    assert result.rule_results[0].status == STATUS_PASS


def test_non_insd_nonzero_phase_fails(tmp_path):
    tables = _base_tables(MRELATION="OWNR", MPHASE=1)
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-004")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("Non-insured relationship" in f.message for f in result.findings)


def test_non_insd_phase_zero_passes(tmp_path):
    result = _run(_base_tables(MRELATION="OWNR", MPHASE=0), tmp_path, rule_id="DG-QUIKCLID-004")
    assert result.rule_results[0].status == STATUS_PASS


def test_insd_missing_rider_fails(tmp_path):
    tables = _base_tables(MRELATION="INSD", MPHASE=2)
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-005")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("no matching rider" in f.message.lower() for f in result.findings)


def test_valid_insd_passes(tmp_path):
    tables = _base_tables(MRELATION="INSD", MPHASE=1)
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-005")
    assert result.rule_results[0].status == STATUS_PASS


def test_invalid_relation_fails(tmp_path):
    tables = _base_tables(MRELATION="BADCODE")
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLID-006")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("unapproved code" in f.message for f in result.findings)


def test_valid_relation_passes(tmp_path):
    result = _run(_base_tables(MRELATION="PAYR"), tmp_path, rule_id="DG-QUIKCLID-006")
    assert result.rule_results[0].status == STATUS_PASS
