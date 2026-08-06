"""Client ID formatting: numeric → zero decimals → trim → left-pad to 12."""

from qla_core.normalize_utils import (
    CLIENT_ID_TARGET_FIELDS,
    QLADMIN_MCLIENTID_WIDTH,
    format_qladmin_mclientid,
)


def test_width_is_12():
    assert QLADMIN_MCLIENTID_WIDTH == 12


def test_format_numeric_string_zero_decimals_pad_12():
    assert format_qladmin_mclientid("12481") == "       12481"
    assert len(format_qladmin_mclientid("12481")) == 12
    assert format_qladmin_mclientid("590304.0") == "      590304"
    assert format_qladmin_mclientid(590304.0) == "      590304"
    assert format_qladmin_mclientid(12481) == "       12481"


def test_trim_before_pad():
    assert format_qladmin_mclientid("  696192  ") == "      696192"
    assert format_qladmin_mclientid("\t44746\n") == "       44746"


def test_blank_stays_blank():
    assert format_qladmin_mclientid("") == ""
    assert format_qladmin_mclientid(None) == ""


def test_mbenfid_is_client_id_target_field():
    assert "MBENFID" in CLIENT_ID_TARGET_FIELDS
    assert "MCLIENTID" in CLIENT_ID_TARGET_FIELDS
    assert "MPRIMID" in CLIENT_ID_TARGET_FIELDS


def test_append_style_rjust_to_dbf_c12():
    """DBF templates use C(12); Append Tool pads to field length after strip."""
    core = format_qladmin_mclientid("12481").strip()
    packed = core.rjust(12, " ")
    assert packed == "       12481"
    assert len(packed) == 12
