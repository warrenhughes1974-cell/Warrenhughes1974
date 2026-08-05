"""Focused tests for durable QuikTvs TV0 blank fill."""

from __future__ import annotations

import csv
from pathlib import Path

from qla_core.quiktvs_tv0_fill import (
    apply_quiktvs_tv0_blank_fill,
    load_true_single_premium_plans,
    quiktvs_tv0_zero_text,
)


def _sample_row(plan: str, tv0: str = "", tv1: str = "1.23") -> dict:
    return {
        "PLAN": plan,
        "AGE": "30",
        "CNTL": "00",
        "TV0": tv0,
        "TV1": tv1,
        "TV2": "",
        "GENDER": "F",
        "UWCLASS": "00",
        "BAND": "00",
        "ISSCNTRY": "0000",
        "ISSUEST": "00",
        "EFFDATE": "19000101",
    }


def test_blank_non_sp_tv0_fills_to_zero_convention():
    factor_rows = {"QuikTvs": [_sample_row("1658C1", tv0="")]}
    stats = apply_quiktvs_tv0_blank_fill(factor_rows, single_premium_plans=set())
    row = factor_rows["QuikTvs"][0]
    assert row["TV0"] == quiktvs_tv0_zero_text()
    assert stats["filled"] == 1
    assert stats["preserved_sp_blank"] == 0


def test_nonblank_tv0_preserved():
    factor_rows = {"QuikTvs": [_sample_row("1658C1", tv0=".88")]}
    stats = apply_quiktvs_tv0_blank_fill(factor_rows, single_premium_plans=set())
    row = factor_rows["QuikTvs"][0]
    assert row["TV0"] == ".88"
    assert stats["preserved_nonblank"] == 1
    assert stats["filled"] == 0


def test_true_sp_blank_tv0_preserved():
    sp_plans = {"1L17SP", "10L171", "117JPO"}
    factor_rows = {
        "QuikTvs": [
            _sample_row("1L17SP", tv0=""),
            _sample_row("10L171", tv0=""),
            _sample_row("117JPO", tv0=""),
            _sample_row("1658C1", tv0=""),
        ]
    }
    stats = apply_quiktvs_tv0_blank_fill(factor_rows, single_premium_plans=sp_plans)
    assert factor_rows["QuikTvs"][0]["TV0"] == ""
    assert factor_rows["QuikTvs"][1]["TV0"] == ""
    assert factor_rows["QuikTvs"][2]["TV0"] == ""
    assert factor_rows["QuikTvs"][3]["TV0"] == quiktvs_tv0_zero_text()
    assert stats["preserved_sp_blank"] == 3
    assert stats["filled"] == 1


def test_no_duration_column_shift():
    factor_rows = {"QuikTvs": [_sample_row("1SALMI", tv0="", tv1="438.0")]}
    apply_quiktvs_tv0_blank_fill(factor_rows, single_premium_plans=set())
    row = factor_rows["QuikTvs"][0]
    assert row["TV0"] == quiktvs_tv0_zero_text()
    assert row["TV1"] == "438.0"
    assert row["TV2"] == ""


def test_load_true_single_premium_from_quikplan_payyrs_and_desc(tmp_path: Path):
    qp = tmp_path / "quikplan.csv"
    with qp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["PLAN", "PAYYRS", "DESCR1"],
        )
        w.writeheader()
        w.writerow({"PLAN": "117JPO", "PAYYRS": "1", "DESCR1": "SINGLE PREMIUM WHOLE LIFE"})
        w.writerow({"PLAN": "1658C1", "PAYYRS": "1", "DESCR1": "ISWL BASE PLAN"})
        w.writerow({"PLAN": "1SALMI", "PAYYRS": "99", "DESCR1": "SINGLE PREMIUM WHOLE LIFE"})
    plans = load_true_single_premium_plans(str(tmp_path), quikplan_path=str(qp), config={})
    assert "117JPO" in plans
    assert "1658C1" not in plans
    assert "1SALMI" not in plans
