"""Tests for DG-QUIKCLNT — Client Setup integrity."""

from __future__ import annotations

from datetime import date

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS

_DOB = date(1980, 1, 1)


def _run(tables, tmp_path, *, rule_id):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _valid_client(**overrides):
    row = {
        "MCLIENTID": "C001",
        "MTYPE": "I",
        "MTAXIDTYPE": "S",
        "MLNAME": "Smith",
        "MFNAME": "John",
        "MADDR1": "123 Main St",
        "MCITY": "Austin",
        "MSTATE": "TX",
        "MZIP": "78701",
        "MDOB": _DOB,
        "MSEX": "M",
        "MLANGUAGE": "E",
    }
    row.update(overrides)
    return row


def _clnt_tables(*rows, **extra):
    tables = {"QuikClnt": list(rows) if rows else [_valid_client()]}
    tables.update(extra)
    return tables


def test_unique_client_passes(tmp_path):
    tables = _clnt_tables(
        _valid_client(MCLIENTID="C001"),
        _valid_client(MCLIENTID="C002", MLNAME="Jones"),
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLNT-001")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_duplicate_client_fails(tmp_path):
    tables = _clnt_tables(
        _valid_client(MCLIENTID="C001"),
        _valid_client(MCLIENTID="C001", MFNAME="Jane"),
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKCLNT-001")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("must be unique" in f.message for f in result.findings)


def test_blank_client_id_fails(tmp_path):
    result = _run(
        _clnt_tables(_valid_client(MCLIENTID="")),
        tmp_path,
        rule_id="DG-QUIKCLNT-001",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank client ID" in f.message for f in result.findings)


def test_blank_type_fails_until_conversion(tmp_path):
    result = _run(
        _clnt_tables(_valid_client(MTYPE="")),
        tmp_path,
        rule_id="DG-QUIKCLNT-002",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank MTYPE" in f.message for f in result.findings)


def test_type_individual_passes(tmp_path):
    result = _run(_clnt_tables(), tmp_path, rule_id="DG-QUIKCLNT-002")
    assert result.rule_results[0].status == STATUS_PASS


def test_last_name_required_for_individual(tmp_path):
    result = _run(
        _clnt_tables(_valid_client(MLNAME="")),
        tmp_path,
        rule_id="DG-QUIKCLNT-004",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank last name" in f.message for f in result.findings)


def test_last_name_present_passes(tmp_path):
    result = _run(_clnt_tables(), tmp_path, rule_id="DG-QUIKCLNT-004")
    assert result.rule_results[0].status == STATUS_PASS


def test_sex_m_passes(tmp_path):
    result = _run(_clnt_tables(_valid_client(MSEX="M")), tmp_path, rule_id="DG-QUIKCLNT-007")
    assert result.rule_results[0].status == STATUS_PASS


def test_sex_f_passes(tmp_path):
    result = _run(_clnt_tables(_valid_client(MSEX="f")), tmp_path, rule_id="DG-QUIKCLNT-007")
    assert result.rule_results[0].status == STATUS_PASS


def test_sex_invalid_fails(tmp_path):
    result = _run(
        _clnt_tables(_valid_client(MSEX="X")),
        tmp_path,
        rule_id="DG-QUIKCLNT-007",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("invalid sex code" in f.message for f in result.findings)


def test_language_blank_fails(tmp_path):
    result = _run(
        _clnt_tables(_valid_client(MLANGUAGE="")),
        tmp_path,
        rule_id="DG-QUIKCLNT-008",
    )
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("blank MLANGUAGE" in f.message for f in result.findings)


def test_language_english_passes(tmp_path):
    result = _run(_clnt_tables(), tmp_path, rule_id="DG-QUIKCLNT-008")
    assert result.rule_results[0].status == STATUS_PASS
