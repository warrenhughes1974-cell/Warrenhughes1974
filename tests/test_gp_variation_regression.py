import csv

from qla_core.quikplan_rate_variation_flags import (
    VARY_FIELD_NAMES,
    apply_default_only_pvo_clear,
    derive_plan_flags,
    scan_emitted_key_csvs,
)
from qla_core.rate_pipeline import collapse_equal_uw_families


GP_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _write_keys(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GP_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _key(plan, gender="0", uwclass="00", band="00"):
    return {
        "PLAN": plan,
        "GENDER": gender,
        "UWCLASS": uwclass,
        "BAND": band,
        "ISSCNTRY": "0000",
        "ISSUEST": "00",
        "EFFDATE": "19000101",
    }


def test_real_gp_key_segmentation_preserves_variation_for_affected_plans(tmp_path):
    rows = []
    for plan in ("1658C1", "1659C2", "1659CR"):
        rows.extend(_key(plan, gender, uw) for gender in ("F", "M") for uw in ("NS", "PR", "SM"))
    rows.extend(_key("1668SP", gender, "PR") for gender in ("F", "M"))
    _write_keys(tmp_path / "QuikPlGp.csv", rows)

    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))

    for plan in ("1658C1", "1659C2", "1659CR"):
        assert updates[plan]["GDVARYGP"] == "Y"
        assert updates[plan]["UWVARYGP"] == "Y"
        # A11h: Band 00 / State 0000|00 alone never enable variation
        assert updates[plan]["BDVARYGP"] == "N"
        assert updates[plan]["STVARYGP"] == "N"
    assert updates["1668SP"]["GDVARYGP"] == "Y"
    assert updates["1668SP"]["UWVARYGP"] == "N"
    assert updates["1668SP"]["BDVARYGP"] == "N"
    assert updates["1668SP"]["STVARYGP"] == "N"


def test_default_only_gp_stub_does_not_enable_variation(tmp_path):
    _write_keys(tmp_path / "QuikPlGp.csv", [_key("121PUA")])

    stats = scan_emitted_key_csvs(str(tmp_path))
    assert stats[("121PUA", "GP")].real_row_count == 0

    row = {"PLAN": "121PUA", "PLANVALOPT": "Y", **{field: "Y" for field in VARY_FIELD_NAMES}}
    cleared, _ = apply_default_only_pvo_clear([row])
    assert cleared[0]["PLANVALOPT"] == "N"
    assert all(cleared[0][field] == "N" for field in VARY_FIELD_NAMES)


def test_cv_tv_control_does_not_change_gp_evidence(tmp_path):
    _write_keys(tmp_path / "QuikPlGp.csv", [
        _key("1659C2", "F", "NS"),
        _key("1659C2", "M", "PR"),
    ])
    _write_keys(tmp_path / "QuikPlCv.csv", [_key("1659C2")])
    _write_keys(tmp_path / "QuikPlTv.csv", [_key("1659C2")])

    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))

    assert updates["1659C2"]["GDVARYGP"] == "Y"
    assert updates["1659C2"]["UWVARYGP"] == "Y"
    assert updates["1659C2"]["GDVARYCV"] == "N"
    assert updates["1659C2"]["UWVARYTV"] == "N"


def test_cv_tv_collapse_is_independent_of_gp():
    def grid(uw_values):
        return {
            ("P", 1, "00", "0", uw, "00", "0000", "00", "19000101"): {
                "RATE": ("1.0",)
            }
            for uw in uw_values
        }

    grids = {
        "QuikCvs": grid(("NS", "PR")),
        "QuikTvs": grid(("NS", "PR")),
        "QuikGps": grid(("NS", "PR")),
    }
    collapsed = collapse_equal_uw_families(grids)

    assert {key[4] for key in collapsed["QuikCvs"]} == {"00"}
    assert {key[4] for key in collapsed["QuikTvs"]} == {"00"}
    assert {key[4] for key in collapsed["QuikGps"]} == {"NS", "PR"}


def test_dv_band_segmentation_sets_only_dv_variation_flags(tmp_path):
    rows = []
    for plan in ("265PUA", "170588", "17085M", "196085", "261PUA", "280PUA"):
        rows.extend(_key(plan, gender="0", uwclass="00", band=band) for band in ("01", "02"))
    rows.append(_key("NO_DV_CONTROL"))
    _write_keys(tmp_path / "QuikPlDv.csv", rows)

    updates = derive_plan_flags(scan_emitted_key_csvs(str(tmp_path)))

    for plan in ("265PUA", "170588", "17085M", "196085", "261PUA", "280PUA"):
        assert updates[plan]["BDVARYDV"] == "Y"
        assert updates[plan]["GDVARYDV"] == "N"
        assert updates[plan]["UWVARYDV"] == "N"
        assert updates[plan]["STVARYDV"] == "N"
        assert all(updates[plan][f"BDVARY{sfx}"] == "N" for sfx in ("GP", "DB", "CV", "TV"))

    assert "NO_DV_CONTROL" not in updates
