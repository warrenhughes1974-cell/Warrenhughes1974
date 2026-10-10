"""Level renewal-period gross premium. Synthetic rows only — no client extracts."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

from qla_core import rate_dbf_schema as S
from qla_core.level_period_premium import (
    DEFAULT_RENEWAL_PERIODS,
    VARGP_LEVEL_PERIOD,
    load_hiage,
    pin_level_period_vargp_frame,
    renewal_periods,
    repo_root,
)
from qla_core.paagerat_pr_loader import transform_paagerat_pr
from qla_core.quikplan_converter import apply_variation_recommendations
from qla_core.quikplan_rate_variation_flags import (
    CODE_ISSUE_AGE_YEAR,
    FactorGridShape,
    apply_variation_codes_from_emitted_rates,
    classify_factor_grid,
)
from qla_core.rate_factor_loader import LoaderConfig, build_factor_grid, grid_to_factor_rows
from qla_core.rate_segment_resolution import SegmentResolver

ROOT = Path(repo_root())
PA_HEADER = ["COVERAGE_ID", "TYPE_CODE", "SEX", "BAND", "UWCLS", "SEQ", "VALUE_INFO", "RECORD_SEQ"]


def _validator():
    path = ROOT / "tools" / "validators" / "validate_tl10_level_premium.py"
    spec = importlib.util.spec_from_file_location("validate_tl10_level_premium", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pa(path: Path, records):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(PA_HEADER)
        for coverage, sex, band, uw, age, value in records:
            writer.writerow([coverage, "PR", sex, band, uw, str(age + 1), f"{float(value):.2f}", "1"])


def _resolver(mapping):
    """segment id -> plan. Parent coverage id is the segment id."""
    return SegmentResolver({seg: seg for seg in mapping}, {}, dict(mapping))


def _run(path, mapping, periods, hiage, monkeypatch, switch=None):
    if switch is None:
        monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    else:
        monkeypatch.setenv("QLA_TL10_LEVEL_PERIOD_PR", switch)
    return list(transform_paagerat_pr(
        str(path),
        _resolver(mapping),
        LoaderConfig(),
        level_periods=periods,
        hiage_by_plan=hiage,
    ))


def _cells(rows, plan):
    out = {}
    for row in rows:
        if row.get("status") != "IN_SCOPE" or row.get("plan") != plan:
            continue
        out.setdefault((row["gender"], row["uwclass"], row["age"]), {})[row["ql_duration"]] = row["value"]
    return out


def _age_rows(coverage, sex, uw, ages, value_of, band="1"):
    return [(coverage, sex, band, uw, age, value_of(age)) for age in ages]


def test_classify_issue_age_and_year_shape_is_2():
    shape = FactorGridShape(real_rows=4, ages={"20", "45"}, duration_slots={0, 9, 10, 40})
    assert classify_factor_grid(shape) == CODE_ISSUE_AGE_YEAR == "2"


def test_config_periods_match_in_code_defaults_and_are_not_merged_away():
    assert renewal_periods({}) == dict(DEFAULT_RENEWAL_PERIODS)
    loaded = renewal_periods()
    assert loaded == dict(DEFAULT_RENEWAL_PERIODS)
    for name in ("rate_loader_config.json", "rate_loader_config.example.json"):
        cfg = json.loads((ROOT / "plan_analysis" / "phase_r5_rate_loader" / name).read_text())
        assert renewal_periods(cfg) == dict(DEFAULT_RENEWAL_PERIODS)
    custom = renewal_periods({"paagerat_pr_level_period": {"TPLN07": 7, "_note": "skip"}})
    assert custom == {"TPLN07": 7}


def test_block_level_and_step_for_each_plans_period(tmp_path, monkeypatch):
    mapping = {"SEG10": "TPLN10", "SEG05": "TPLN05"}
    records = []
    records += _age_rows("SEG10", "M", "P", range(18, 41), lambda age: age)
    records += _age_rows("SEG05", "F", "P", range(10, 31), lambda age: age)
    path = tmp_path / "pa.csv"
    _write_pa(path, records)
    periods = {"TPLN10": 10, "TPLN05": 5}
    hiage = {"TPLN10": 25, "TPLN05": 15}
    rows = _run(path, mapping, periods, hiage, monkeypatch)

    ten = _cells(rows, "TPLN10")[("M", "PR", "18")]
    assert [ten[k] for k in range(0, 10)] == [18] * 10
    assert [ten[k] for k in range(10, 20)] == [28] * 10
    assert [ten[k] for k in range(20, 23)] == [38] * 3
    assert 23 not in ten
    assert ("M", "PR", "26") not in _cells(rows, "TPLN10")

    five = _cells(rows, "TPLN05")[("F", "PR", "10")]
    assert [five[k] for k in range(0, 5)] == [10] * 5
    assert [five[k] for k in range(5, 10)] == [15] * 5
    assert [five[k] for k in range(10, 15)] == [20] * 5
    assert five[20] == 30
    assert max(five) >= 5


def test_period_is_taken_from_the_plan_map(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    _write_pa(path, _age_rows("SEG07", "M", "P", range(10, 31), lambda age: age))
    rows = _run(
        path, {"SEG07": "TPLN07"}, {"TPLN07": 7}, {"TPLN07": 12}, monkeypatch,
    )
    cells = _cells(rows, "TPLN07")[("M", "PR", "10")]
    assert [cells[k] for k in range(0, 7)] == [10] * 7
    assert [cells[k] for k in range(7, 14)] == [17] * 7
    assert [cells[k] for k in range(14, 21)] == [24] * 7
    assert ("M", "PR", "13") not in _cells(rows, "TPLN07")


def test_index_stops_at_99_or_past_the_highest_source_age(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    _write_pa(path, _age_rows("SEG", "M", "P", range(0, 100), lambda age: age))
    rows = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, {"TPLN10": 0}, monkeypatch)
    cells = _cells(rows, "TPLN10")[("M", "PR", "00")]
    assert max(cells) == 99
    assert 100 not in cells
    assert cells[90] == cells[99] == 90


def test_blank_when_the_source_has_no_rate_for_the_lookup_age(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    ages = [age for age in range(20, 41) if age != 30]
    _write_pa(path, _age_rows("SEG", "M", "P", ages, lambda age: age))
    rows = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, {"TPLN10": 40}, monkeypatch)
    cells = _cells(rows, "TPLN10")[("M", "PR", "20")]
    assert [cells[k] for k in range(0, 10)] == [20] * 10
    assert all(k not in cells for k in range(10, 20))
    assert cells[20] == 40


def test_outside_allowlist_matches_the_kill_switch_and_slot_flag_stays_off(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    records = _age_rows("SEG10", "M", "P", range(20, 31), lambda age: age)
    records += _age_rows("SEGX", "F", "P", range(20, 25), lambda age: age + 0.5)
    _write_pa(path, records)
    mapping = {"SEG10": "TPLN10", "SEGX": "TPLNOT"}
    periods = {"TPLN10": 10}
    hiage = {"TPLN10": 22}
    enabled = _run(path, mapping, periods, hiage, monkeypatch)
    disabled = _run(path, mapping, periods, hiage, monkeypatch, switch="0")

    def scoped(rows, plan):
        return [row for row in rows if row.get("status") == "IN_SCOPE" and row.get("plan") == plan]

    assert scoped(enabled, "TPLNOT") == scoped(disabled, "TPLNOT")
    assert scoped(disabled, "TPLNOT")
    assert all(row["attained_age_slot"] for row in scoped(disabled, "TPLNOT"))
    assert scoped(enabled, "TPLN10")
    assert all(row["attained_age_slot"] is False for row in scoped(enabled, "TPLN10"))
    assert {row["age"] for row in scoped(enabled, "TPLN10")} != {"00"}


@pytest.mark.parametrize("switch", ["0", "false", "no", "off"])
def test_kill_switch_restores_the_slot_axis(tmp_path, monkeypatch, switch):
    path = tmp_path / "pa.csv"
    _write_pa(path, _age_rows("SEG", "M", "P", range(20, 25), lambda age: age))
    mapping = {"SEG": "TPLN10"}
    periods = {"TPLN10": 10}
    hiage = {"TPLN10": 22}
    disabled = _run(path, mapping, periods, hiage, monkeypatch, switch=switch)
    untouched = _run(path, mapping, {}, hiage, monkeypatch)
    assert disabled == untouched
    assert {row["age"] for row in disabled if row.get("status") == "IN_SCOPE"} == {"00"}


def test_first_block_uses_band_1_while_the_slot_axis_keeps_the_first_row(tmp_path, monkeypatch):
    """Allow-listed grid takes LifePRO band 1. The kill-switch slot keeps file order."""
    path = tmp_path / "pa.csv"
    records = _age_rows("SEG1", "M", "P", [20, 30], lambda age: 1.25 if age == 20 else 4.5, band="2")
    records += _age_rows("SEG2", "M", "P", [20], lambda age: 9.99, band="1")
    _write_pa(path, records)
    mapping = {"SEG1": "TPLN10", "SEG2": "TPLN10"}
    # Both segments share one parent so they collapse onto one plan.
    resolver = SegmentResolver({"SEG1": "COV", "SEG2": "COV"}, {}, {"COV": "TPLN10"})
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    enabled = list(transform_paagerat_pr(
        str(path), resolver, LoaderConfig(),
        level_periods={"TPLN10": 10}, hiage_by_plan={"TPLN10": 20},
    ))
    monkeypatch.setenv("QLA_TL10_LEVEL_PERIOD_PR", "off")
    disabled = list(transform_paagerat_pr(
        str(path), resolver, LoaderConfig(),
        level_periods={"TPLN10": 10}, hiage_by_plan={"TPLN10": 20},
    ))
    cells = _cells(enabled, "TPLN10")[("M", "PR", "20")]
    assert [cells[k] for k in range(0, 10)] == [9.99] * 10
    grids, _collisions, _caps = build_factor_grid(
        (row for row in disabled if row.get("status") == "IN_SCOPE"), None,
    )
    cntl, col = S.duration_to_cntl_col(20)
    slot = next(
        cells[col][0]
        for key, cells in grids["QuikGps"].items()
        if key[0] == "TPLN10" and key[1] == "00" and key[2] == cntl
    )
    assert slot == 1.25


def test_band_order_in_the_file_does_not_change_the_band_1_rate(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    records = [
        ("SEG", "M", "2", "P", 20, 8.70),
        ("SEG", "M", "3", "P", 20, 7.00),
        ("SEG", "M", "1", "P", 20, 9.00),
        ("SEG", "M", "1", "P", 20, 9.50),
    ]
    records += [("SEG", "M", "1", "P", age, 1.00) for age in range(21, 30)]
    _write_pa(path, records)
    rows = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, {"TPLN10": 20}, monkeypatch)
    cells = _cells(rows, "TPLN10")[("M", "PR", "20")]
    assert [cells[k] for k in range(10)] == [9.00] * 10


def test_missing_band_1_falls_back_to_the_lowest_band(tmp_path, monkeypatch, caplog):
    import logging

    path = tmp_path / "pa.csv"
    _write_pa(path, [
        ("SEG", "F", "3", "S", 30, 3.00),
        ("SEG", "F", "2", "S", 30, 2.00),
    ])
    caplog.set_level(logging.WARNING)
    rows = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, {"TPLN10": 30}, monkeypatch)
    cells = _cells(rows, "TPLN10")[("F", "ST", "30")]
    assert cells[0] == 2.00
    assert "plan TPLN10" in caplog.text
    assert "sex F" in caplog.text
    assert "class ST" in caplog.text
    assert "age 30" in caplog.text


def test_outsider_and_kill_switch_keep_the_first_row(tmp_path, monkeypatch):
    path = tmp_path / "pa.csv"
    records = [
        ("SEGX", "M", "2", "P", 20, 8.70),
        ("SEGX", "M", "1", "P", 20, 9.00),
        ("SEGL", "F", "2", "P", 20, 8.70),
        ("SEGL", "F", "3", "P", 20, 7.00),
        ("SEGL", "F", "1", "P", 20, 9.00),
    ]
    _write_pa(path, records)
    mapping = {"SEGX": "TPLNOT", "SEGL": "TPLN10"}
    periods = {"TPLN10": 10}
    hiage = {"TPLN10": 20}
    enabled = _run(path, mapping, periods, hiage, monkeypatch)
    disabled = _run(path, mapping, periods, hiage, monkeypatch, switch="0")

    def scoped(rows, plan):
        return [row for row in rows if row.get("status") == "IN_SCOPE" and row.get("plan") == plan]

    assert scoped(enabled, "TPLNOT") == scoped(disabled, "TPLNOT")

    def slot_value(rows, plan):
        grids, _collisions, _caps = build_factor_grid(
            (row for row in rows if row.get("status") == "IN_SCOPE" and row.get("plan") == plan),
            None,
        )
        cntl, col = S.duration_to_cntl_col(20)
        return next(
            cells[col][0]
            for key, cells in grids["QuikGps"].items()
            if key[0] == plan and key[1] == "00" and key[2] == cntl
        )

    assert slot_value(disabled, "TPLNOT") == 8.70
    assert slot_value(disabled, "TPLN10") == 8.70
    assert _cells(enabled, "TPLN10")[("F", "PR", "20")][0] == 9.00


def test_hiage_comes_from_staged_quikplan():
    ages = load_hiage(str(ROOT), DEFAULT_RENEWAL_PERIODS)
    assert ages == {"5L0110": 85, "5L0510": 85, "5L075Y": 85}


def test_load_hiage_prefers_staged_over_a_previous_output(tmp_path):
    staged = tmp_path / "plan_governance" / "staged"
    output = tmp_path / "QLA_Migration" / "Output"
    staged.mkdir(parents=True)
    output.mkdir(parents=True)
    header = "PLAN,HIAGE\n"
    (staged / "quikplan_staged.csv").write_text(
        header + "5L0110,85\n5L0510,85\n5L075Y,85\n", encoding="utf-8",
    )
    (output / "quikplan.csv").write_text(
        header + "5L0110,40\n5L0510,40\n5L075Y,40\n", encoding="utf-8",
    )
    assert load_hiage(str(tmp_path), DEFAULT_RENEWAL_PERIODS) == {
        "5L0110": 85, "5L0510": 85, "5L075Y": 85,
    }


def test_vargp_pin_survives_variation_refresh_and_auto_apply(tmp_path, monkeypatch):
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    monkeypatch.setattr(
        "qla_core.level_period_premium.plans_with_quikgps",
        lambda root=None: {"5L0110", "5L0510", "5L075Y"},
    )
    rates = tmp_path / "rates"
    rates.mkdir()
    columns = ["PLAN", "AGE", "CNTL"] + [f"GP{i}" for i in range(10)]
    with (rates / "QuikGps.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for plan in ("5L0110", "1L14SC"):
            row = {"PLAN": plan, "AGE": "00", "CNTL": "02"}
            for index in range(10):
                row[f"GP{index}"] = "1.00"
            writer.writerow(row)
    rows = [
        {"PLAN": "5L0110", "VARGP": "3", "HIAGE": "85"},
        {"PLAN": "1L14SC", "VARGP": "3", "HIAGE": "80"},
    ]
    manifest = {"QuikGps": {"5L0110", "1L14SC"}}
    refreshed, _touched = apply_variation_codes_from_emitted_rates(rows, str(rates), manifest)
    by_plan = {row["PLAN"]: row for row in refreshed}
    assert by_plan["5L0110"]["VARGP"] == "2"
    assert by_plan["5L0110"]["HIAGE"] == "85"
    assert by_plan["1L14SC"]["VARGP"] == "3"
    again, _touched = apply_variation_codes_from_emitted_rates(refreshed, str(rates), manifest)
    assert {row["PLAN"]: row["VARGP"] for row in again}["5L0110"] == "2"

    recommended = apply_variation_recommendations(
        {"PLAN": "5L0110", "VARGP": "4", "VARDB": "0"},
        {"5L0110": {"Recommended_VARGP": "3", "Recommended_VARDB": "0"}},
        True,
    )
    assert recommended["VARGP"] == "2"
    assert recommended["VARDB"] == "0"
    other = apply_variation_recommendations(
        {"PLAN": "1L14SC", "VARGP": "4", "VARDB": "0"},
        {"1L14SC": {"Recommended_VARGP": "3", "Recommended_VARDB": "1"}},
        True,
    )
    assert other["VARGP"] == "3"
    assert other["VARDB"] == "1"

    frame = pin_level_period_vargp_frame(__import__("pandas").DataFrame([
        {"PLAN": "5L0510", "VARGP": "3", "HIAGE": "85"},
        {"PLAN": "5667AT", "VARGP": "3", "HIAGE": "75"},
    ]))
    assert frame.at[0, "VARGP"] == VARGP_LEVEL_PERIOD
    assert frame.at[0, "HIAGE"] == "85"
    assert frame.at[1, "VARGP"] == "3"

    monkeypatch.setenv("QLA_TL10_LEVEL_PERIOD_PR", "off")
    restored, _touched = apply_variation_codes_from_emitted_rates(rows, str(rates), manifest)
    assert {row["PLAN"]: row["VARGP"] for row in restored}["5L0110"] == "3"


def _gold_value(plan, sex, uw, age):
    gold = {
        ("5L0110", "F", "P", 65): 9.00,
        ("5L0110", "F", "P", 75): 27.04,
        ("5L0110", "F", "P", 85): 82.89,
        ("5L0110", "M", "P", 40): 2.38,
        ("5L0110", "M", "P", 50): 4.69,
        ("5L0110", "M", "P", 60): 10.08,
        ("5L0510", "F", "S", 48): 4.56,
        ("5L0510", "F", "S", 58): 9.23,
        ("5L0510", "F", "S", 68): 23.91,
        ("5L0510", "F", "P", 44): 2.26,
        ("5L0510", "F", "P", 54): 4.34,
        ("5L0510", "F", "P", 64): 7.34,
    }
    return gold.get((plan, sex, uw, age), (age % 50) + 0.01)


def _write_factor_csv(path, table_rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(table_rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(table_rows)


def _build_output(root: Path, monkeypatch, switch=None, ages=range(15, 100), hiage=None):
    slices = (
        ("L01", "5L0110", "F", "P"),
        ("L01", "5L0110", "M", "P"),
        ("L05", "5L0510", "M", "P"),
        ("L05", "5L0510", "F", "S"),
        ("L05", "5L0510", "F", "P"),
        ("L07", "5L075Y", "M", "S"),
    )
    records = []
    for coverage, plan, sex, uw in slices:
        for age in ages:
            records.append((coverage, sex, "1", uw, age, _gold_value(plan, sex, uw, age)))
    path = root / "pa.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_pa(path, records)
    mapping = {"L01": "5L0110", "L05": "5L0510", "L07": "5L075Y"}
    if hiage is None:
        hiage = {"5L0110": 85, "5L0510": 85, "5L075Y": 85}
    rows = _run(path, mapping, None, hiage, monkeypatch, switch=switch)
    scoped = [row for row in rows if row.get("status") == "IN_SCOPE"]
    grids, _collisions, _caps = build_factor_grid(scoped, LoaderConfig())
    factor_rows, _fmt = grid_to_factor_rows("QuikGps", grids["QuikGps"], LoaderConfig())
    return factor_rows


def test_validator_accepts_synthetic_grid_and_baseline(tmp_path, monkeypatch):
    output = tmp_path / "Output"
    rates = output / "rates"
    new_rows = _build_output(tmp_path / "new", monkeypatch)
    _write_factor_csv(rates / "QuikGps.csv", new_rows)
    base_rows = _build_output(tmp_path / "old", monkeypatch, switch="0")
    baseline = tmp_path / "baseline"
    _write_factor_csv(baseline / "QuikGps.csv", base_rows)
    extra = b"PLAN,AGE\nOTHR01,00\n"
    (rates / "QuikNps.csv").write_bytes(extra)
    (baseline / "QuikNps.csv").write_bytes(extra)
    other = b"OTHR01,30,00,1.00,,,,,,,,,,F,PR,00,0000,00,19000101\n"
    assert len(other.decode().rstrip("\n").split(",")) == 19
    for folder in (rates, baseline):
        with (folder / "QuikGps.csv").open("ab") as handle:
            handle.write(other)
    with (output / "quikplan.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["PLAN", "VARGP", "HIAGE"])
        for plan in ("5L0110", "5L0510", "5L075Y"):
            writer.writerow([plan, "2", "85"])
        writer.writerow(["5667AT", "3", "75"])

    module = _validator()
    infos: list[str] = []
    assert module.validate(output, baseline, infos=infos) == []
    assert any(item.startswith("INFO 5L075Y") for item in infos)

    broken = output / "rates" / "QuikGps.csv"
    text = broken.read_text(encoding="utf-8").replace("9.00", "9.01", 1)
    broken.write_text(text, encoding="utf-8")
    failures = module.validate(output, baseline)
    assert failures
    assert any(item.startswith("(d)") or item.startswith("(e)") or item.startswith("(b)") for item in failures)


def test_gold_amounts_format_as_the_validator_text():
    expected = {
        9.00: "9.00", 27.04: "27.04", 82.89: "82.89",
        2.38: "2.38", 4.69: "4.69", 10.08: "10.08",
        4.56: "4.56", 9.23: "9.23", 23.91: "23.91",
        2.26: "2.26", 4.34: "4.34", 7.34: "7.34",
        8.96: "8.96", 12.48: "12.48", 18.33: "18.33", 31.49: "31.49",
    }
    for number, text in expected.items():
        got, fits, _reduced = S.format_factor(number)
        assert fits
        assert got == text


def test_shared_slot_segment_fills_both_allow_listed_plans(tmp_path, monkeypatch):
    """Issue #158: one SEQ-1 segment owned by two plans must fill both grids."""
    monkeypatch.delenv("QLA_PR_SEGMENT_SLOT_OWNERSHIP", raising=False)
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    path = tmp_path / "pa.csv"
    _write_pa(path, _age_rows("SEG", "M", "P", range(20, 41), lambda age: float(age)))
    resolver = SegmentResolver(
        {},
        {},
        {"COV10": "TPLNA", "COV05": "TPLNB"},
        slot_owners={(1, "SEG"): ["COV10", "COV05"]},
    )
    rows = list(transform_paagerat_pr(
        str(path), resolver, LoaderConfig(),
        level_periods={"TPLNA": 10, "TPLNB": 10},
        hiage_by_plan={"TPLNA": 25, "TPLNB": 25},
    ))
    left = _cells(rows, "TPLNA")
    right = _cells(rows, "TPLNB")
    assert left == right
    assert {age for _gender, _uw, age in left} == {f"{n:02d}" for n in range(20, 26)}
    issue20 = left[("M", "PR", "20")]
    assert [issue20[k] for k in range(10)] == [20.0] * 10
    assert [issue20[k] for k in range(10, 20)] == [30.0] * 10
    counts = {}
    for row in rows:
        if row.get("status") == "IN_SCOPE":
            counts[row["plan"]] = counts.get(row["plan"], 0) + 1
            assert row["age_capped"] is False
            assert row["original_age"] == row["age"]
    assert counts["TPLNA"] == counts["TPLNB"] > 0


def test_expanded_cell_is_not_reported_as_age_capped():
    from qla_core.level_period_premium import _cell_row

    out = _cell_row(
        {
            "age": "99", "cntl": "09", "col": 9, "ql_duration": 99,
            "attained_age_slot": True, "value": 8.0, "raw_value": "8.00",
            "age_capped": True, "original_age": "101", "plan": "TPLN10",
        },
        29, 0,
    )
    assert out["age"] == "29"
    assert out["age_capped"] is False
    assert out["original_age"] == "29"
    assert out["attained_age_slot"] is False


def test_hiage_missing_or_below_lowest_uses_highest_source_age(tmp_path, monkeypatch, caplog):
    import logging

    path = tmp_path / "pa.csv"
    _write_pa(path, _age_rows("SEG", "M", "P", range(30, 51), lambda age: age))
    caplog.set_level(logging.WARNING)
    for hiage in ({"TPLN10": 0}, {"TPLN10": 10}, {}):
        caplog.clear()
        rows = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, hiage, monkeypatch)
        cells = _cells(rows, "TPLN10")
        assert ("M", "PR", "30") in cells
        assert ("M", "PR", "50") in cells
        assert "TPLN10" in caplog.text
    capped = _run(path, {"SEG": "TPLN10"}, {"TPLN10": 10}, {"TPLN10": 40}, monkeypatch)
    assert ("M", "PR", "40") in _cells(capped, "TPLN10")
    assert ("M", "PR", "50") not in _cells(capped, "TPLN10")


def test_empty_period_map_is_honored_and_bad_entries_warn(caplog):
    import logging

    assert renewal_periods({"paagerat_pr_level_period": {}}) == {}
    caplog.set_level(logging.WARNING)
    got = renewal_periods({
        "paagerat_pr_level_period": {"TPLN": "ten", "TPLN5": 5, "ZERO": 0, "_note": "skip"},
    })
    assert got == {"TPLN5": 5}
    assert "ten" in caplog.text
    assert "ZERO" in caplog.text
    assert renewal_periods({"paagerat_pr_level_period": "nope"}) == {}


def test_renewal_periods_cache_skips_repeat_config_reads(monkeypatch):
    import qla_core.level_period_premium as LPP

    LPP._DEFAULT_PERIODS = None
    calls = {"n": 0}
    real = LPP.load_pipeline_config

    def counting(root=None):
        calls["n"] += 1
        return real(root)

    monkeypatch.setattr(LPP, "load_pipeline_config", counting)
    try:
        assert LPP.renewal_periods() == dict(DEFAULT_RENEWAL_PERIODS)
        assert calls["n"] == 1
        LPP.pin_level_period_vargp_row({"PLAN": "5L0110", "VARGP": "4"})
        LPP.pin_level_period_vargp_row({"PLAN": "5L0510", "VARGP": "4"})
        assert calls["n"] == 1
    finally:
        LPP._DEFAULT_PERIODS = None


def test_vargp_pin_leaves_not_on_file_when_quikgps_is_absent(monkeypatch):
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    monkeypatch.setattr(
        "qla_core.level_period_premium.plans_with_quikgps",
        lambda root=None: set(),
    )
    recommended = apply_variation_recommendations(
        {"PLAN": "5L0110", "VARGP": "4", "VARDB": "0"},
        {"5L0110": {"Recommended_VARGP": "3", "Recommended_VARDB": "0"}},
        True,
    )
    assert recommended["VARGP"] == "3"
    assert recommended["VARDB"] == "0"
    untouched = apply_variation_recommendations(
        {"PLAN": "5L0110", "VARGP": "4", "VARDB": "0"},
        None,
        False,
    )
    assert untouched["VARGP"] == "4"
    frame = pin_level_period_vargp_frame(__import__("pandas").DataFrame([
        {"PLAN": "5L0510", "VARGP": "4", "HIAGE": "85"},
    ]))
    assert frame.at[0, "VARGP"] == "4"
    assert frame.at[0, "HIAGE"] == "85"


def _write_quikplan(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["PLAN", "VARGP", "HIAGE"])
        for plan in ("5L0110", "5L0510", "5L075Y"):
            writer.writerow([plan, "2", "85"])


def test_validator_warns_when_source_ends_below_hiage_plus_period(tmp_path, monkeypatch):
    output = tmp_path / "Output"
    rows = _build_output(tmp_path / "short", monkeypatch, ages=range(15, 91))
    _write_factor_csv(output / "rates" / "QuikGps.csv", rows)
    _write_quikplan(output / "quikplan.csv")
    module = _validator()
    warnings = []
    assert module.validate(output, warnings=warnings) == []
    text = "\n".join(warnings)
    assert "issue age 81" in text
    assert "issue age 85" in text
    assert "issue age 80" not in text

    seg = ("M", "PR", "00", "", "", "")
    periods = {"5L0110": 10, "5L0510": 10, "5L075Y": 5}
    slices = {}
    for plan, period in periods.items():
        slices[(plan, seg, 20)] = {0: "1.00", 1: "1.00"}
        slices[(plan, seg, 20 + period)] = {i: "9.00" for i in range(period + 1)}
    failures = []
    warned = []
    module._check_blocks(slices, periods, failures, warned)
    assert failures
    assert all(item.startswith("(c)") for item in failures)
    assert warned == []


def test_rate_pipeline_keeps_level_plans_out_of_the_slot_set(tmp_path, monkeypatch):
    import qla_core.plan_source_paths as PSP
    from qla_core.rate_pipeline import run

    root = tmp_path / "repo"
    root.mkdir()
    records = [
        (cov, "M", "1", uw, age, float(age))
        for cov, uw in (("L01", "P"), ("L05", "P"), ("L07", "S"), ("ART", "P"))
        for age in (40, 50, 60)
    ]
    _write_pa(root / "pa.csv", records)
    (root / "pcovrsgt.csv").write_text(
        "SEGT_ID,COVERAGE_ID,SEGT_FLAG,SEQ\n"
        "L01,L01,Y,1\nL05,L05,Y,1\nL07,L07,Y,1\nART,ART,Y,1\n",
        encoding="utf-8",
    )
    (root / "pcovr.csv").write_text(
        "COVERAGE_ID,DESCRIPTION\nL01,L01\nL05,L05\nL07,L07\nART,ART\n",
        encoding="utf-8",
    )
    (root / "rt.csv").write_text(
        "COVERAGE_ID,TYPE_CODE,AGE,SEX,BAND,UNDERWRITING_CLASS,DURATION,VALUE\n",
        encoding="utf-8",
    )
    cfg = {
        "source_rate_extract": str(root / "rt.csv"),
        "plan_form_crosswalk": str(root / "missing.xlsx"),
        "pcovrsgt_csv": str(root / "pcovrsgt.csv"),
        "pcovr_csv": str(root / "pcovr.csv"),
        "paagerat_pr_extract": str(root / "pa.csv"),
        "issue40_cv_inheritance": {"enabled": False},
        "issue42_pdage_missfill": {"enabled": False},
        "non_cv_rate_inheritance": {"enabled": False},
        "shared_rate_candidates": {"enabled": False},
        "psubsseg_substitution": {"enabled": False},
        "paagerat_pr_level_period": {"5L0110": 10, "5L0510": 10, "5L075Y": 5},
    }
    cfg_path = root / "rate_loader_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    cov2plan = {"L01": "5L0110", "L05": "5L0510", "L07": "5L075Y", "ART": "5667AT"}
    monkeypatch.setattr(
        "qla_core.rate_pipeline.L.load_plan_crosswalk",
        lambda path: (dict(cov2plan), {}),
    )
    monkeypatch.setattr(PSP, "paage_extract", lambda log=None: "")
    monkeypatch.setattr(PSP, "paagerat_extract", lambda log=None: "")
    monkeypatch.setattr(PSP, "pdage_extract", lambda log=None: "")
    monkeypatch.setattr(PSP, "rate_table_extract", lambda: "")
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
    monkeypatch.delenv("QLA_PR_SEGMENT_SLOT_OWNERSHIP", raising=False)

    res = run(str(cfg_path), str(root))
    slot = set(res.attained_age_slot_plans.get("QuikGps", ()))
    assert "5667AT" in slot
    assert not ({"5L0110", "5L0510", "5L075Y"} & slot)
    ages = {key[1] for key in res.grids["QuikGps"] if key[0] == "5L0110"}
    assert "40" in ages
    assert "00" not in ages

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("level-period lookup ran while the kill switch was off")

    monkeypatch.setenv("QLA_TL10_LEVEL_PERIOD_PR", "0")
    monkeypatch.setattr("qla_core.rate_pipeline.LPP.renewal_periods", _forbidden)
    monkeypatch.setattr("qla_core.rate_pipeline.LPP.load_hiage", _forbidden)
    off = run(str(cfg_path), str(root))
    off_slot = set(off.attained_age_slot_plans.get("QuikGps", ()))
    assert {"5L0110", "5L0510", "5L075Y", "5667AT"} <= off_slot
