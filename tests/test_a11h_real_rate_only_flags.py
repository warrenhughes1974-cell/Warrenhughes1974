"""Issue A11h — real-rate-only Band/State/DV/DB variation flags."""
from __future__ import annotations

import csv

from qla_core.quikplan_rate_variation_flags import (
    VARY_FIELD_NAMES,
    apply_factor_table_pvo_enablement,
    apply_family_factor_presence_gate,
    derive_plan_flags,
    scan_emitted_key_csvs,
)


GP_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _write_keys(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GP_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _key(plan, gender="0", uwclass="00", band="00", isscntry="0000", issuest="00"):
    return {
        "PLAN": plan,
        "GENDER": gender,
        "UWCLASS": uwclass,
        "BAND": band,
        "ISSCNTRY": isscntry,
        "ISSUEST": issuest,
        "EFFDATE": "19000101",
    }


def _blank_row(plan: str) -> dict:
    return {"PLAN": plan, "PLANVALOPT": "N", **{f: "N" for f in VARY_FIELD_NAMES}}


def test_band_00_alone_does_not_enable_bdvary(tmp_path):
    rows = [
        _key("1658C1", gender, uw)
        for gender in ("F", "M")
        for uw in ("NS", "PR", "SM")
    ]
    _write_keys(tmp_path / "QuikPlGp.csv", rows)
    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))
    assert updates["1658C1"]["GDVARYGP"] == "Y"
    assert updates["1658C1"]["UWVARYGP"] == "Y"
    assert updates["1658C1"]["BDVARYGP"] == "N"
    assert updates["1658C1"]["STVARYGP"] == "N"


def test_multi_band_enables_bdvary(tmp_path):
    rows = [_key("P1", "M", "NS", band) for band in ("01", "02")]
    _write_keys(tmp_path / "QuikPlGp.csv", rows)
    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))
    assert updates["P1"]["BDVARYGP"] == "Y"
    assert updates["P1"]["STVARYGP"] == "N"


def test_multi_state_enables_stvary(tmp_path):
    rows = [
        _key("P1", "M", "NS", issuest="01"),
        _key("P1", "M", "NS", issuest="02"),
    ]
    _write_keys(tmp_path / "QuikPlGp.csv", rows)
    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))
    assert updates["P1"]["STVARYGP"] == "Y"
    assert updates["P1"]["BDVARYGP"] == "N"


def test_issue96_does_not_force_band_or_gender(tmp_path):
    rates = tmp_path / "rates"
    rates.mkdir()
    with (rates / "QuikCvs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["PLAN", "AGE", "CV0"])
        w.writeheader()
        w.writerow({"PLAN": "P1", "AGE": "00", "CV0": "1.00"})
    row = _blank_row("P1")
    out, touched = apply_factor_table_pvo_enablement([row], str(rates))
    assert out[0]["PLANVALOPT"] == "N"
    assert out[0]["GDVARYCV"] == "N"
    assert out[0]["BDVARYCV"] == "N"
    assert touched == {}


def test_no_quikdvs_clears_dv_flags(tmp_path):
    rates = tmp_path / "rates"
    rates.mkdir()
    with (rates / "QuikGps.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["PLAN", "AGE", "GP0"])
        w.writeheader()
        w.writerow({"PLAN": "1658C1", "AGE": "00", "GP0": "1.00"})
    row = {
        "PLAN": "1658C1",
        "PLANVALOPT": "Y",
        **{f: "Y" for f in VARY_FIELD_NAMES},
    }
    out, touched = apply_family_factor_presence_gate([row], str(rates))
    for dim in ("GDVARY", "UWVARY", "BDVARY", "STVARY"):
        assert out[0][f"{dim}DV"] == "N"
        assert out[0][f"{dim}DB"] == "N"
    assert out[0]["GDVARYGP"] == "Y"  # GP factors present — leave until Band/State rules
    assert "1658C1" in touched


def test_1658c1_like_keys_plus_factor_gate(tmp_path):
    """Keys may show F/M DV/DB, but empty QuikDvs/QuikDbs must clear those families."""
    rates = tmp_path / "rates"
    rates.mkdir()
    for name, rows in (
        ("QuikPlGp.csv", [
            _key("1658C1", g, u) for g in ("F", "M") for u in ("NS", "PR", "SM")
        ]),
        ("QuikPlDb.csv", [_key("1658C1", "F", "NS"), _key("1658C1", "M", "NS")]),
        ("QuikPlDv.csv", [_key("1658C1", "F", "NS"), _key("1658C1", "M", "NS")]),
    ):
        _write_keys(rates / name, rows)
    with (rates / "QuikGps.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["PLAN", "AGE", "GP0"])
        w.writeheader()
        w.writerow({"PLAN": "1658C1", "AGE": "00", "GP0": "1.00"})
    for empty in ("QuikDbs.csv", "QuikDvs.csv", "QuikCvs.csv", "QuikTvs.csv"):
        with (rates / empty).open("w", newline="", encoding="utf-8") as fh:
            fh.write("PLAN,AGE\n")

    updates = derive_plan_flags(scan_emitted_key_csvs(str(rates)))
    row = {
        "PLAN": "1658C1",
        "PLANVALOPT": updates["1658C1"]["PLANVALOPT"],
        **{f: updates["1658C1"].get(f, "N") for f in VARY_FIELD_NAMES},
    }
    out, _ = apply_family_factor_presence_gate([row], str(rates))
    assert out[0]["GDVARYGP"] == "Y"
    assert out[0]["UWVARYGP"] == "Y"
    assert out[0]["BDVARYGP"] == "N"
    assert out[0]["STVARYGP"] == "N"
    for sfx in ("DB", "DV", "CV", "TV"):
        for dim in ("GDVARY", "UWVARY", "BDVARY", "STVARY"):
            assert out[0][f"{dim}{sfx}"] == "N"
    assert out[0]["PLANVALOPT"] == "Y"
