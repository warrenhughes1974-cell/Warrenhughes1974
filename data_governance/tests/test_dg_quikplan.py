"""Tests for DG-QUIKPLAN — Plan Setup integrity."""

from __future__ import annotations

import csv
import os
from datetime import date, timedelta

import pytest

from data_governance.catalog.registry import reset_registry_for_tests
from data_governance.data_access.normalization import add_calendar_months
from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS, STATUS_WARN
from data_governance.reporting.simplified_reports import (
    TYPE_DATA_PROBLEM,
    TYPE_WARNING,
    build_attention_rows,
    write_items_needing_attention_csv,
    write_what_was_checked_html,
)

FIXED_TS = "2026-07-18 12:00:00"
CONFIG_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "plan_classification.csv")
)


def _patch_run_id(monkeypatch):
    monkeypatch.setattr(
        "data_governance.execution.runner.new_run_id",
        lambda now=None: ("DG-TEST-QUIKPLAN", FIXED_TS),
    )


def _run(tables, tmp_path, *, item=None, rule_id=None):
    reset_registry_for_tests()
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        governance_item_id=item,
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _valid_plan(**overrides):
    row = {
        "PLAN": "123456",
        "PAR": "0",
        "BASIS": "",
        "LOANINTX": "A",
        "DEPINT": 5.0,
        "LOAGE": 0,
        "HIAGE": 99,
        "RENEW": "N",
        "PAYYRS": 10,
        "PAYAGE": 0,
        "INSYRS": 20,
        "INSAGE": 0,
        "SEMI": 0,
        "QTRL": 0,
        "MTHD": 0,
        "MTHB": 0,
        "INITVAL": 1000,
        "COMMID": "",
        "MAXUNIT": 10,
        "MINUNIT": 1,
        "RRULE": "B",
        "AUTONFO": "0",
        "DEFICIENCY": "N",
        "BACTIVE": True,
        "PLANVALOPT": False,
        "MLAPSE": 0,
        "MNAICLOB": "NAPLAN",
        "VARGP": "4",
        "VARDB": "4",
        "PLANTYPE": "",
        "HCOMMIP": False,
        "HRIGPKEY": False,
    }
    row.update(overrides)
    return row


def _base_tables(**overrides):
    tables = {
        "QuikPlan": [_valid_plan()],
        "QuikComm": [{"COMMID": "C001"}],
        "QuikComp": [{"MCOMP": "A"}],
    }
    tables.update(overrides)
    return tables


def _write_classification(tmp_path, rows):
    path = tmp_path / "plan_classification.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["PLAN", "IS_MYGA", "IS_UL", "IS_SINGLE_PREMIUM", "INITVAL_EXCEPTION"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def test_plan_code_rules(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    good = _base_tables()
    assert _run(good, tmp_path, rule_id="DG-QUIKPLAN-001").rule_results[0].status == STATUS_PASS
    assert _run(good, tmp_path, rule_id="DG-QUIKPLAN-002").rule_results[0].status == STATUS_PASS

    for plan, rid in (("12345", "DG-QUIKPLAN-001"), ("1234567", "DG-QUIKPLAN-001")):
        bad = _base_tables(QuikPlan=[_valid_plan(PLAN=plan)])
        assert _run(bad, tmp_path, rule_id=rid).rule_results[0].status == STATUS_FAIL

    blank = _base_tables(QuikPlan=[_valid_plan(PLAN="")])
    assert _run(blank, tmp_path, rule_id="DG-QUIKPLAN-001").rule_results[0].status == STATUS_FAIL
    null = _base_tables(QuikPlan=[_valid_plan(PLAN=None)])
    assert _run(null, tmp_path, rule_id="DG-QUIKPLAN-001").rule_results[0].status == STATUS_FAIL

    for bad_plan in ("ABC 12", "ABC-12", "ABC_12"):
        t = _base_tables(QuikPlan=[_valid_plan(PLAN=bad_plan.ljust(6)[:6] if len(bad_plan) >= 6 else bad_plan)])
        if len(bad_plan) == 6:
            assert _run(t, tmp_path, rule_id="DG-QUIKPLAN-002").rule_results[0].status == STATUS_FAIL

    for suffix in ("PA", "XP", "XF", "XS", "pa"):
        t = _base_tables(QuikPlan=[_valid_plan(PLAN=f"1234{suffix[-2:].upper()}")])
        assert _run(t, tmp_path, rule_id="DG-QUIKPLAN-003").rule_results[0].status == STATUS_FAIL


def test_par_basis_loanintx(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    for par in ("0", "1"):
        assert (
            _run(_base_tables(QuikPlan=[_valid_plan(PAR=par)]), tmp_path, rule_id="DG-QUIKPLAN-004")
            .rule_results[0]
            .status
            == STATUS_PASS
        )
    assert (
        _run(_base_tables(QuikPlan=[_valid_plan(PAR="2")]), tmp_path, rule_id="DG-QUIKPLAN-004")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )

    a_plan = _base_tables(QuikPlan=[_valid_plan(PLAN="A12345", BASIS="QUAL")])
    assert _run(a_plan, tmp_path, rule_id="DG-QUIKPLAN-005").rule_results[0].status == STATUS_PASS
    assert (
        _run(
            _base_tables(QuikPlan=[_valid_plan(PLAN="A12345", BASIS="nonq")]),
            tmp_path,
            rule_id="DG-QUIKPLAN-005",
        )
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run(
            _base_tables(QuikPlan=[_valid_plan(BASIS="QUAL")]),
            tmp_path,
            rule_id="DG-QUIKPLAN-005",
        )
        .rule_results[0]
        .status
        == STATUS_FAIL
    )
    assert (
        _run(
            _base_tables(QuikPlan=[_valid_plan(PLAN="A12345", BASIS="")]),
            tmp_path,
            rule_id="DG-QUIKPLAN-005",
        )
        .rule_results[0]
        .status
        == STATUS_FAIL
    )

    for opt in ("A", "R"):
        assert (
            _run(_base_tables(QuikPlan=[_valid_plan(LOANINTX=opt)]), tmp_path, rule_id="DG-QUIKPLAN-006")
            .rule_results[0]
            .status
            == STATUS_PASS
        )
    assert (
        _run(_base_tables(QuikPlan=[_valid_plan(LOANINTX="X")]), tmp_path, rule_id="DG-QUIKPLAN-006")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )


def test_myga_classification_incomplete(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    missing_cfg = tmp_path / "empty.csv"
    missing_cfg.write_text("PLAN,IS_MYGA,IS_UL,IS_SINGLE_PREMIUM\n", encoding="utf-8")
    monkeypatch.setattr(
        "data_governance.rules.plan_setup_integrity.plan_classification._CONFIG_PATH",
        str(missing_cfg),
    )
    r = _run(_base_tables(), tmp_path, rule_id="DG-QUIKPLAN-007")
    assert r.rule_results[0].status == STATUS_ERROR
    assert len(r.findings) == 1


def test_ages_renew_payment_insurance(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert (
        _run(_base_tables(), tmp_path, rule_id="DG-QUIKPLAN-008").rule_results[0].status == STATUS_PASS
    )
    # DG-R-007: non-zero LOAGE is valid when LOAGE < HIAGE (real min issue age)
    nonzero_ok = _base_tables(QuikPlan=[_valid_plan(LOAGE=15, HIAGE=55)])
    assert _run(nonzero_ok, tmp_path, rule_id="DG-QUIKPLAN-008").rule_results[0].status == STATUS_PASS
    eq_age = _base_tables(QuikPlan=[_valid_plan(LOAGE=0, HIAGE=0)])
    assert _run(eq_age, tmp_path, rule_id="DG-QUIKPLAN-008").rule_results[0].status == STATUS_FAIL
    inverted = _base_tables(QuikPlan=[_valid_plan(LOAGE=55, HIAGE=15)])
    assert _run(inverted, tmp_path, rule_id="DG-QUIKPLAN-008").rule_results[0].status == STATUS_FAIL

    five_plan = _base_tables(QuikPlan=[_valid_plan(PLAN="512345", RENEW="Y")])
    assert _run(five_plan, tmp_path, rule_id="DG-QUIKPLAN-009").rule_results[0].status == STATUS_PASS
    bad_renew = _base_tables(QuikPlan=[_valid_plan(RENEW="Y")])
    assert _run(bad_renew, tmp_path, rule_id="DG-QUIKPLAN-009").rule_results[0].status == STATUS_FAIL

    both_zero = _base_tables(QuikPlan=[_valid_plan(PAYYRS=0, PAYAGE=0)])
    assert _run(both_zero, tmp_path, rule_id="DG-QUIKPLAN-010").rule_results[0].status == STATUS_FAIL
    five_zero = _base_tables(QuikPlan=[_valid_plan(PLAN="512345", PAYYRS=0, PAYAGE=0)])
    assert _run(five_zero, tmp_path, rule_id="DG-QUIKPLAN-010").rule_results[0].status == STATUS_PASS

    ins_zero = _base_tables(QuikPlan=[_valid_plan(INSYRS=0, INSAGE=0)])
    assert _run(ins_zero, tmp_path, rule_id="DG-QUIKPLAN-011").rule_results[0].status == STATUS_FAIL

    assert (
        _run(_base_tables(QuikPlan=[_valid_plan(PAYAGE=125)]), tmp_path, rule_id="DG-QUIKPLAN-013")
        .rule_results[0]
        .status
        == STATUS_PASS
    )
    assert (
        _run(_base_tables(QuikPlan=[_valid_plan(PAYAGE=126)]), tmp_path, rule_id="DG-QUIKPLAN-013")
        .rule_results[0]
        .status
        == STATUS_FAIL
    )


def test_initval_warn_and_commid(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    warn = _run(_base_tables(QuikPlan=[_valid_plan(INITVAL=500)]), tmp_path, rule_id="DG-QUIKPLAN-015")
    assert warn.rule_results[0].status == STATUS_PASS
    assert warn.rule_results[0].warn_count == 1
    assert warn.findings[0].status == STATUS_WARN

    blank_comm = _run(_base_tables(), tmp_path, rule_id="DG-QUIKPLAN-016")
    assert blank_comm.rule_results[0].status == STATUS_PASS
    miss = _run(
        _base_tables(QuikPlan=[_valid_plan(COMMID="ZZZZ")]),
        tmp_path,
        rule_id="DG-QUIKPLAN-016",
    )
    assert miss.rule_results[0].status == STATUS_FAIL

    no_comm = _base_tables()
    no_comm.pop("QuikComm", None)
    no_comm_r = _run(no_comm, tmp_path, rule_id="DG-QUIKPLAN-016")
    assert no_comm_r.rule_results[0].status == STATUS_ERROR
    assert len(no_comm_r.findings) == 1


def test_defaults_and_deficiency(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    assert _run(_base_tables(), tmp_path, rule_id="DG-QUIKPLAN-017").rule_results[0].status == STATUS_PASS
    below = _base_tables(QuikPlan=[_valid_plan(MAXUNIT=1, MINUNIT=5)])
    assert _run(below, tmp_path, rule_id="DG-QUIKPLAN-017").rule_results[0].status == STATUS_FAIL

    for rid in ("DG-QUIKPLAN-018", "DG-QUIKPLAN-019", "DG-QUIKPLAN-023", "DG-QUIKPLAN-024"):
        assert _run(_base_tables(), tmp_path, rule_id=rid).rule_results[0].status == STATUS_PASS

    alpha = _base_tables(QuikPlan=[_valid_plan(PLAN="P12345", DEFICIENCY="N")])
    assert _run(alpha, tmp_path, rule_id="DG-QUIKPLAN-020").rule_results[0].status == STATUS_PASS
    bad_def = _base_tables(QuikPlan=[_valid_plan(PLAN="P12345", DEFICIENCY="Y")])
    assert _run(bad_def, tmp_path, rule_id="DG-QUIKPLAN-020").rule_results[0].status == STATUS_FAIL
    skip = _base_tables(QuikPlan=[_valid_plan(PLAN="212345", DEFICIENCY="Y")])
    assert _run(skip, tmp_path, rule_id="DG-QUIKPLAN-020").rule_results[0].records_evaluated == 0


def test_annuity_supporting_tables_aing_or_ainf(tmp_path, monkeypatch):
    """DG-R-012 / DG-QUIKPLAN-028: QuikAing or QuikAinf satisfies the pair."""
    _patch_run_id(monkeypatch)
    base = {
        "QuikPlan": [_valid_plan(PLAN="A12345")],
        "QuikComm": [{"COMMID": "C001"}],
        "QuikComp": [{"MCOMP": "A"}],
        "QuikAint": [{"MPLAN": "A12345"}],
        "QuikAexp": [{"MPLAN": "A12345"}],
        "QuikAing": [],
        "QuikAinf": [],
    }
    # Neither Aing nor Ainf → WARN
    neither = _run(base, tmp_path, rule_id="DG-QUIKPLAN-028")
    assert neither.rule_results[0].warn_count >= 1

    # Aing only (empty Ainf) → no Aing/Ainf warning
    aing_only = dict(base)
    aing_only["QuikAing"] = [{"MPLAN": "A12345"}]
    ok_aing = _run(aing_only, tmp_path, rule_id="DG-QUIKPLAN-028")
    assert ok_aing.rule_results[0].status == STATUS_PASS
    assert ok_aing.rule_results[0].warn_count == 0

    # Ainf only (empty Aing) → same
    ainf_only = dict(base)
    ainf_only["QuikAinf"] = [{"MPLAN": "A12345"}]
    ok_ainf = _run(ainf_only, tmp_path, rule_id="DG-QUIKPLAN-028")
    assert ok_ainf.rule_results[0].status == STATUS_PASS
    assert ok_ainf.rule_results[0].warn_count == 0


def test_death_benefit_supporting_tables_vardb(tmp_path, monkeypatch):
    """DG-R-010 / DG-QUIKPLAN-026: tables required only for VARDB 1/2/3."""
    _patch_run_id(monkeypatch)
    # Level (0) and not-on-file (4): no QuikDbs/QuikPlDb needed
    for vd in ("0", "4"):
        level = _base_tables(QuikPlan=[_valid_plan(VARDB=vd)])
        r = _run(level, tmp_path, rule_id="DG-QUIKPLAN-026")
        assert r.rule_results[0].status == STATUS_PASS
        assert r.rule_results[0].records_evaluated == 0

    # Varying with empty supporting tables → FAIL (plan not found)
    missing = _base_tables(
        QuikPlan=[_valid_plan(VARDB="1")],
        QuikDbs=[],
        QuikPlDb=[],
    )
    fail = _run(missing, tmp_path, rule_id="DG-QUIKPLAN-026")
    assert fail.rule_results[0].status == STATUS_FAIL

    # Varying with both tables → PASS
    ok = _base_tables(
        QuikPlan=[_valid_plan(VARDB="2")],
        QuikDbs=[{"PLAN": "123456"}],
        QuikPlDb=[{"PLAN": "123456"}],
    )
    assert _run(ok, tmp_path, rule_id="DG-QUIKPLAN-026").rule_results[0].status == STATUS_PASS


def test_logical_meds_and_cross_tables(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    # DG-QUIKPLAN-022 retired (DG-R-006): PLANVALOPT not constrained by BACTIVE

    meds = _base_tables(QuikPlan=[_valid_plan(PLANTYPE="MEDS", HCOMMIP=True, HRIGPKEY=True)])
    assert _run(meds, tmp_path, rule_id="DG-QUIKPLAN-030").rule_results[0].status == STATUS_PASS
    bad_meds = _base_tables(QuikPlan=[_valid_plan(PLANTYPE="MEDS", HCOMMIP=False, HRIGPKEY=True)])
    assert _run(bad_meds, tmp_path, rule_id="DG-QUIKPLAN-030").rule_results[0].status == STATUS_FAIL

    orphan = _base_tables(QuikPlCv=[{"PLAN": "ORPHAN", "EFFDATE": date(2020, 1, 1)}])
    fail31 = _run(orphan, tmp_path, rule_id="DG-QUIKPLAN-031")
    assert fail31.rule_results[0].status == STATUS_FAIL

    bad_co = _base_tables(QuikAgts=[{"MAGENT": "1", "MAGTNAME": "A", "MCOMP": "Z"}])
    assert _run(bad_co, tmp_path, rule_id="DG-QUIKPLAN-032").rule_results[0].status == STATUS_FAIL


def test_date_warning_and_reporting(tmp_path, monkeypatch):
    _patch_run_id(monkeypatch)
    run_date = date(2026, 7, 18)
    max_d = add_calendar_months(run_date, 12)
    early = _base_tables(QuikPlCv=[{"PLAN": "123456", "EFFDATE": date(1899, 12, 31)}])
    w = _run(early, tmp_path, rule_id="DG-QUIKPLAN-033")
    assert w.rule_results[0].status == STATUS_PASS
    assert w.rule_results[0].warn_count == 1

    late = _base_tables(
        QuikPlCv=[{"PLAN": "123456", "EFFDATE": max_d + timedelta(days=1)}]
    )
    w2 = _run(late, tmp_path, rule_id="DG-QUIKPLAN-033")
    assert w2.rule_results[0].warn_count >= 1

    result = _run(_base_tables(QuikPlan=[_valid_plan(INITVAL=750)]), tmp_path, item="DG-QUIKPLAN")
    result.write_reports = True
    write_what_was_checked_html(result, str(tmp_path / "report.html"))
    rows = write_items_needing_attention_csv(result, str(tmp_path / "attention.csv"))
    assert any(r.type == TYPE_WARNING for r in rows)
    assert not any(r.type == TYPE_DATA_PROBLEM and "passed" in r.problem.lower() for r in rows)
