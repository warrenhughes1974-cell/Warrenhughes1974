"""Tests for DG-QUIKMSTR-027 through 032 — cross-table policy/coverage status consistency.

Issue #108 track G. Each rule gets a clean case and a violating case, so a regression in
either direction is caught. Rules 029 and 031 are Advisory: they emit WARN findings and the
rule result stays PASS, which is what lets them surface questions without failing a run.
"""

from __future__ import annotations

from datetime import date

from data_governance.execution.runner import run_data_governance
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS, STATUS_WARN

_PAID_TO = date(2012, 10, 1)


def _run(tables, tmp_path, *, rule_id):
    return run_data_governance(
        data_dir=str(tmp_path),
        output_dir=str(tmp_path / "out"),
        rule_id=rule_id,
        write_reports=False,
        preloaded_tables=tables,
    )


def _mstr(**overrides):
    row = {
        "MPOLICY": "POL001A",
        "MSTATUS": "22",
        "MPAIDTO": _PAID_TO,
        "MNFOPT": "0",
    }
    row.update(overrides)
    return row


def _ridr(**overrides):
    """A phase-1 row that satisfies the Issue #108 nonforfeiture field contract."""
    row = {
        "MPOLICY": "POL001A",
        "MPHASE": "1",
        "MPLAN": "221END",
        "MPHSTAT": "22",
        "MAGE": "51",
        "MPAYUP": _PAID_TO,
        "MPREM": "0",
        "MSAVEAGE": "",
        "MSAVEUNIT": "",
        "MSAVEVPU": "",
        "MSAVEPREM": "",
        "MSAVESTAT": "",
    }
    row.update(overrides)
    return row


def _tables(mstr_rows, ridr_rows):
    return {"QuikMstr": list(mstr_rows), "QuikRidr": list(ridr_rows)}


# --- 027 terminated policy must not have in-force coverage -------------------------------

def test_027_terminated_policy_all_coverage_terminated_passes(tmp_path):
    tables = _tables([_mstr(MSTATUS="53")], [_ridr(MPHSTAT="53")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-027")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_027_terminated_policy_with_in_force_coverage_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="53")], [_ridr(MPHSTAT="22")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-027")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("still in force" in f.message for f in result.findings)


def test_027_status_50_counts_as_terminated(tmp_path):
    tables = _tables([_mstr(MSTATUS="50")], [_ridr(MPHSTAT="22")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-027")
    assert result.rule_results[0].status == STATUS_FAIL


def test_027_active_policy_is_out_of_scope(tmp_path):
    tables = _tables([_mstr(MSTATUS="22")], [_ridr(MPHSTAT="22")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-027")
    assert result.rule_results[0].records_evaluated == 0


# --- 028 NFO phase-1 status must match policy status -------------------------------------

def test_028_matching_phase1_status_passes(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-028")
    assert result.rule_results[0].status == STATUS_PASS


def test_028_mismatched_phase1_status_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="22")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-028")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("phase 1 coverage carries status 22" in f.message for f in result.findings)


def test_028_missing_phase1_row_is_reported(tmp_path):
    tables = _tables([_mstr(MSTATUS="44")], [_ridr(MPHASE="2", MPLAN="1708PA")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-028")
    assert result.rule_results[0].status == STATUS_ERROR
    assert any("no phase 1 coverage row" in f.message for f in result.findings)


# --- 029 NFO later-phase coverages (Advisory) --------------------------------------------

def test_029_terminated_later_phase_passes(tmp_path):
    tables = _tables(
        [_mstr(MSTATUS="45")],
        [_ridr(MPHSTAT="45"), _ridr(MPHASE="2", MPLAN="967ADB", MPHSTAT="54")],
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-029")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_029_in_force_later_phase_warns_without_failing(tmp_path):
    tables = _tables(
        [_mstr(MSTATUS="45")],
        [_ridr(MPHSTAT="45"), _ridr(MPHASE="2", MPLAN="967ADB", MPHSTAT="22")],
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-029")
    rule_result = result.rule_results[0]
    assert rule_result.status == STATUS_PASS
    assert rule_result.warn_count == 1
    assert all(f.status == STATUS_WARN for f in result.findings)


def test_029_zero_unit_base_plans_are_excluded(tmp_path):
    """1SALMI holds the whole face amount, so an in-force phase 2 is expected (#108E)."""
    tables = _tables(
        [_mstr(MSTATUS="45")],
        [_ridr(MPLAN="1SALML", MPHSTAT="45"), _ridr(MPHASE="2", MPLAN="1SALMI", MPHSTAT="22")],
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-029")
    assert result.findings == []
    assert result.rule_results[0].summary_metrics["zero_unit_base_rows_excluded"] == 1


# --- 030 active policy must have in-force coverage ---------------------------------------

def test_030_active_policy_with_in_force_coverage_passes(tmp_path):
    tables = _tables([_mstr(MSTATUS="22")], [_ridr(MPHSTAT="22")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-030")
    assert result.rule_results[0].status == STATUS_PASS


def test_030_active_policy_with_all_coverage_terminated_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="22")], [_ridr(MPHSTAT="54")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-030")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("all 1 coverages are terminated" in f.message for f in result.findings)


def test_030_active_policy_with_no_coverage_rows_is_reported(tmp_path):
    tables = _tables([_mstr(MSTATUS="22")], [_ridr(MPOLICY="OTHER01")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-030")
    assert result.rule_results[0].status == STATUS_ERROR
    assert any("no coverage rows at all" in f.message for f in result.findings)


def test_030_nfo_policy_is_out_of_scope(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-030")
    assert result.rule_results[0].records_evaluated == 0


# --- 031 NFO election vs status (Advisory) -----------------------------------------------

def test_031_matching_election_passes(tmp_path):
    tables = _tables([_mstr(MSTATUS="45", MNFOPT="3")], [_ridr(MPHSTAT="45")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-031")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_031_contradicting_election_warns(tmp_path):
    tables = _tables([_mstr(MSTATUS="45", MNFOPT="2")], [_ridr(MPHSTAT="45")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-031")
    assert result.rule_results[0].warn_count == 1
    assert any("carries election 2" in f.message for f in result.findings)


def test_031_missing_election_is_described_as_missing(tmp_path):
    tables = _tables([_mstr(MSTATUS="44", MNFOPT="0")], [_ridr(MPHSTAT="44")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-031")
    assert any("no election recorded" in f.message for f in result.findings)


# --- 032 NFO field completeness ----------------------------------------------------------

def test_032_complete_nfo_policy_passes(tmp_path):
    tables = _tables([_mstr(MSTATUS="44")], [_ridr(MPHSTAT="44")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_PASS
    assert result.findings == []


def test_032_payup_not_matching_paidto_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45", MPAYUP=date(2020, 1, 1))])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("does not match the policy paid-to date" in f.message for f in result.findings)


def test_032_blank_age_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45", MAGE="00")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("age is blank or zero" in f.message for f in result.findings)


def test_032_populated_save_field_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45", MSAVESTAT="45")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("populated save fields" in f.message for f in result.findings)


def test_032_eti_with_nonzero_premium_fails(tmp_path):
    tables = _tables([_mstr(MSTATUS="44")], [_ridr(MPHSTAT="44", MPREM="12.50")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("premium is 12.50" in f.message for f in result.findings)


def test_032_rpu_keeps_its_premium(tmp_path):
    """The specification zeroes MPREM on ETI only; RPU retains it (Issue #108C)."""
    tables = _tables([_mstr(MSTATUS="45")], [_ridr(MPHSTAT="45", MPREM="12.50")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_PASS


def test_032_pua_not_terminated_fails(tmp_path):
    tables = _tables(
        [_mstr(MSTATUS="45")],
        [_ridr(MPHSTAT="45"), _ridr(MPHASE="2", MPLAN="221EPA", MPHSTAT="41")],
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_FAIL
    assert any("paid-up addition" in f.message for f in result.findings)


def test_032_terminated_pua_passes(tmp_path):
    tables = _tables(
        [_mstr(MSTATUS="45")],
        [_ridr(MPHSTAT="45"), _ridr(MPHASE="2", MPLAN="221EPA", MPHSTAT="54")],
    )
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].status == STATUS_PASS


def test_032_non_nfo_policy_is_out_of_scope(tmp_path):
    tables = _tables([_mstr(MSTATUS="22")], [_ridr(MSAVESTAT="22", MAGE="00")])
    result = _run(tables, tmp_path, rule_id="DG-QUIKMSTR-032")
    assert result.rule_results[0].records_evaluated == 0
