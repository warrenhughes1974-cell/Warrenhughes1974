"""Tests for valuation date / source package alignment."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from qla_core.valuation_date import (
    apply_valuation_date_env,
    parse_ppolc_valuation_date,
    resolve_valuation_date_yyyymmdd,
    select_ppolc_path,
)


def test_parse_ppolc_valuation_date():
    assert parse_ppolc_valuation_date("PPOLC_PolicyMaster_Extract_20260630.csv") == "20260630"
    assert parse_ppolc_valuation_date("PPOLC_PolicyMaster_Extract_20260102.csv") == "20260102"
    assert parse_ppolc_valuation_date("quikmstr.csv") == ""


def test_select_ppolc_path_matches_valuation(tmp_path: Path):
    src = tmp_path / "Source"
    src.mkdir()
    ppolc = src / "PPOLC_PolicyMaster_Extract_20260630.csv"
    ppolc.write_text("POLICY_NUMBER\n", encoding="utf-8")

    path = select_ppolc_path(src, "20260630")
    assert path == str(ppolc)

    with pytest.raises(ValueError, match="No PPOLC policy extract matches"):
        select_ppolc_path(src, "20260731")


def test_resolve_from_active_ppolc_when_env_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    src = tmp_path / "Source"
    src.mkdir()
    (src / "PPOLC_PolicyMaster_Extract_20260731.csv").write_text("POLICY_NUMBER\n", encoding="utf-8")
    monkeypatch.delenv("QLA_VALUATION_DATE", raising=False)

    vd, label = resolve_valuation_date_yyyymmdd(source_dir=src)
    assert vd == "20260731"
    assert "20260731" in label


def test_apply_valuation_date_env_sets_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    src = tmp_path / "Source"
    src.mkdir()
    (src / "PPOLC_PolicyMaster_Extract_20260630.csv").write_text("POLICY_NUMBER\n", encoding="utf-8")
    monkeypatch.delenv("QLA_VALUATION_DATE", raising=False)

    vd, _src = apply_valuation_date_env(src)
    assert vd == "20260630"
    assert os.environ["QLA_VALUATION_DATE"] == "20260630"
