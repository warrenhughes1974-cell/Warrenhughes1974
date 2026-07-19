"""Unit tests for conversion-safe Policy Data Governance transforms."""

from qla_core.policy_data_transforms import (
    apply_mbillday_from_issue_date,
    apply_quikclid_phase_for_relation,
    uppercase_alpha_field,
)


def test_mbillday_from_missdt_when_blank():
    val, changed = apply_mbillday_from_issue_date("", "20180315")
    assert changed is True
    assert val == "15"


def test_mbillday_preserves_nonzero():
    val, changed = apply_mbillday_from_issue_date("7", "20180315")
    assert changed is False
    assert val == "7"


def test_mbillday_zero_uses_issue_day():
    val, changed = apply_mbillday_from_issue_date("0", "1999-12-31")
    assert changed is True
    assert val == "31"


def test_quikclid_non_insd_forced_phase_zero():
    val, changed, rule = apply_quikclid_phase_for_relation("1", "OWNR")
    assert val == "0"
    assert changed is True
    assert rule == "DG-QUIKCLID-004"


def test_quikclid_insd_blank_defaults_phase_one():
    val, changed, rule = apply_quikclid_phase_for_relation("", "INSD")
    assert val == "1"
    assert changed is True
    assert rule == "DG-QUIKCLID-005"


def test_quikclid_insd_keeps_valid_phase():
    val, changed, rule = apply_quikclid_phase_for_relation("2", "INSD")
    assert val == "2"
    assert changed is False
    assert rule == "DG-QUIKCLID-005"


def test_uppercase_alpha_field():
    val, changed = uppercase_alpha_field("tx")
    assert val == "TX"
    assert changed is True
    val2, changed2 = uppercase_alpha_field("M")
    assert val2 == "M"
    assert changed2 is False
