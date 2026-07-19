"""DG-R-003: quikdate_converter emit uses shared prior_month_end."""
from datetime import date
from pathlib import Path

from data_governance.data_access.normalization import prior_month_end
from qla_core.quikdate_converter import (
    QUIKDATE_SCHEMA,
    build_quikdate_governance_row,
    emit_quikdate_csv,
    format_qla_date,
)


def test_build_row_prior_month_end_july_2026():
    row = build_quikdate_governance_row(date(2026, 7, 18))
    expected = format_qla_date(prior_month_end(date(2026, 7, 18)))
    assert expected == "20260630"
    assert row["PACBILL"] == expected
    assert row["DIRBILL"] == expected
    assert row["REINBILL"] == expected
    assert row["ACHFILEID"] == 0
    assert row["ACHFILEID2"] == "A"
    assert row["ESC_DATE"] == ""
    assert list(row.keys()) == QUIKDATE_SCHEMA


def test_emit_quikdate_csv(tmp_path: Path):
    info = emit_quikdate_csv(str(tmp_path), conversion_run_date=date(2026, 3, 1))
    assert info["prior_month_end"] == "2026-02-28"
    out = Path(info["path"])
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "PACBILL" in text
    assert "20260228" in text
