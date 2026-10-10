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


def test_first_block_matches_the_slot_axis_winner(tmp_path, monkeypatch):
    """Sibling PAAGERAT rows: the factor grid keeps the first row, not band priority."""
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
    assert [cells[k] for k in range(0, 10)] == [1.25] * 10
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


def test_hiage_from_staged_quikplan_when_output_is_absent():
    output = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
    ages = load_hiage(str(ROOT), DEFAULT_RENEWAL_PERIODS)
    if output.is_file():
        assert set(DEFAULT_RENEWAL_PERIODS) <= set(ages)
    else:
        assert ages == {"5L0110": 85, "5L0510": 85, "5L075Y": 85}


def test_vargp_pin_survives_variation_refresh_and_auto_apply(tmp_path, monkeypatch):
    monkeypatch.delenv("QLA_TL10_LEVEL_PERIOD_PR", raising=False)
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
        ("5L075Y", "M", "S", 54): 8.51,
        ("5L075Y", "M", "S", 59): 11.86,
        ("5L075Y", "M", "S", 64): 17.41,
    }
    return gold.get((plan, sex, uw, age), (age % 50) + 0.01)


def _write_factor_csv(path, table_rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(table_rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(table_rows)


def _build_output(root: Path, monkeypatch, switch=None):
    slices = (
        ("L01", "5L0110", "F", "P"),
        ("L01", "5L0110", "M", "P"),
        ("L05", "5L0510", "M", "P"),
        ("L07", "5L075Y", "M", "S"),
    )
    records = []
    for coverage, plan, sex, uw in slices:
        for age in range(15, 100):
            records.append((coverage, sex, "1", uw, age, _gold_value(plan, sex, uw, age)))
    path = root / "pa.csv"
    _write_pa(path, records)
    mapping = {"L01": "5L0110", "L05": "5L0510", "L07": "5L075Y"}
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
    other = b"OTHR01,30,00,1.00,,,,,,,,F,PR,00,0000,00,19000101\n"
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
    assert module.validate(output, baseline) == []

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
        8.51: "8.51", 11.86: "11.86", 17.41: "17.41",
    }
    for number, text in expected.items():
        got, fits, _reduced = S.format_factor(number)
        assert fits
        assert got == text
