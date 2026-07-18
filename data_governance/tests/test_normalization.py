"""Tests for DBF character normalization helpers."""

from decimal import Decimal

from datetime import date

from data_governance.data_access.normalization import (
    decode_dbf_date,
    decode_numeric_zero,
    derive_policy_company_code,
    normalize_character_casefold,
    normalize_dbf_character,
    prior_month_end,
)


def test_normalize_trims_padding():
    assert normalize_dbf_character("A ") == "A"
    assert normalize_dbf_character(" B") == "B"
    assert normalize_dbf_character("  X  ") == "X"


def test_normalize_nulls_to_blank():
    assert normalize_dbf_character(None) == ""
    assert normalize_dbf_character("") == ""
    assert normalize_dbf_character("nan") == ""


def test_normalize_preserves_case():
    assert normalize_dbf_character("a") == "a"
    assert normalize_dbf_character("A") == "A"


def test_derive_policy_company_code():
    assert derive_policy_company_code("123456789A") == "A"
    assert derive_policy_company_code("123456789A  ") == "A"
    assert derive_policy_company_code(None) is None
    assert derive_policy_company_code("") is None
    assert derive_policy_company_code("   ") is None


def test_normalize_character_casefold():
    assert normalize_character_casefold("n") == ("N", "n", False)
    assert normalize_character_casefold(" a ") == ("A", " a ", False)
    assert normalize_character_casefold(None) == (None, "", True)
    assert normalize_character_casefold("   ") == ("", "   ", False)


def test_decode_numeric_zero():
    assert decode_numeric_zero(0).is_zero
    assert decode_numeric_zero(0.0).is_zero
    assert decode_numeric_zero("0").is_zero
    assert decode_numeric_zero("000").is_zero
    assert decode_numeric_zero(Decimal("0")).is_zero
    assert decode_numeric_zero(None).is_null
    assert decode_numeric_zero("").is_blank
    assert decode_numeric_zero("   ").is_blank
    assert not decode_numeric_zero(30).is_zero
    assert decode_numeric_zero("ABC").is_unreadable


def test_prior_month_end_and_date_decode():
    assert prior_month_end(date(2026, 7, 18)) == date(2026, 6, 30)
    assert decode_dbf_date(date(2026, 6, 30)).date_value == date(2026, 6, 30)
    assert decode_dbf_date(None).is_blank
    assert decode_dbf_date("").is_blank
    assert decode_dbf_date("not-a-date").is_unreadable
