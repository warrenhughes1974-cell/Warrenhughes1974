from qla_core.rate_pipeline import (
    _rewrite_collapsed_family_keys,
    collapse_equal_uw_families,
)
from qla_core.rate_key_setup import build_key_rows
from qla_core import rate_dbf_schema as S
from qla_core.rate_emit import _finalize_equal_cv_tv_keys


def _grid(table, uw, values):
    return (
        ("P001", "30", "00", "F", uw, "00", "0000", "00", "19000101"),
        {i: (value, str(value), i) for i, value in enumerate(values)},
    )


def test_cv_and_tv_collapse_independently_and_preserve_gp():
    grids = {
        "QuikCvs": dict([_grid("QuikCvs", uw, (1.0, 2.0)) for uw in ("00", "NS")]),
        "QuikTvs": dict([_grid("QuikTvs", uw, (3.0, 4.0)) for uw in ("00", "NS")]),
        "QuikGps": dict([_grid("QuikGps", uw, (9.0, 9.5)) for uw in ("00", "NS")]),
    }

    collapsed, targets = collapse_equal_uw_families(grids, return_targets=True)
    assert set(k[4] for k in collapsed["QuikCvs"]) == {"00"}
    assert set(k[4] for k in collapsed["QuikTvs"]) == {"00"}
    assert set(k[4] for k in collapsed["QuikGps"]) == {"00", "NS"}
    assert targets["QuikCvs"] == {("P001", "19000101")}
    assert targets["QuikTvs"] == {("P001", "19000101")}

    key_rows = {
        "QuikPlCv": [
            {"PLAN": "P001", "GENDER": "F", "UWCLASS": uw,
             "BAND": "00", "ISSCNTRY": "0000", "ISSUEST": "00",
             "EFFDATE": "19000101"}
            for uw in ("00", "NS")
        ],
        "QuikPlTv": [
            {"PLAN": "P001", "GENDER": "F", "UWCLASS": uw,
             "BAND": "00", "ISSCNTRY": "0000", "ISSUEST": "00",
             "EFFDATE": "19000101"}
            for uw in ("00", "NS")
        ],
    }
    _rewrite_collapsed_family_keys(key_rows, targets)
    assert len(key_rows["QuikPlCv"]) == 1
    assert len(key_rows["QuikPlTv"]) == 1
    assert key_rows["QuikPlCv"][0]["UWCLASS"] == "00"
    assert key_rows["QuikPlTv"][0]["UWCLASS"] == "00"


def test_non_equal_grid_and_missing_cell_do_not_collapse():
    grids = {
        "QuikCvs": dict([
            _grid("QuikCvs", "00", (1.0, 2.0)),
            _grid("QuikCvs", "NS", (1.0, 2.1)),
        ]),
        "QuikTvs": dict([
            _grid("QuikTvs", "00", (3.0,)),
            _grid("QuikTvs", "NS", (3.0, 4.0)),
        ]),
    }
    collapsed = collapse_equal_uw_families(grids)
    assert set(k[4] for k in collapsed["QuikCvs"]) == {"00", "NS"}
    assert set(k[4] for k in collapsed["QuikTvs"]) == {"00", "NS"}


def test_v05_affected_tv_patterns_collapse_and_derive_matching_keys():
    affected = {
        "5CDT10": ("F", ("PR", "SM", "ST")),
        "7SDT10": ("M", ("PR", "SM", "ST")),
        "543CTR": ("M", ("PR", "SM")),
        "542STR": ("M", ("PR", "SM")),
    }
    grids = {"QuikTvs": {}}
    for plan, (gender, uwclasses) in affected.items():
        for uwclass in uwclasses:
            key = (plan, "30", "00", gender, uwclass, "00", "0000", "00", "19000101")
            grids["QuikTvs"][key] = {0: (3.0, "3.0", 1), 1: (4.0, "4.0", 2)}

    collapsed, targets = collapse_equal_uw_families(grids, return_targets=True)
    assert targets["QuikTvs"] == {
        (plan, "19000101") for plan in affected
    }
    assert {key[4] for key in collapsed["QuikTvs"]} == {"00"}

    key_table, key_rows, _ = build_key_rows("QuikTvs", collapsed["QuikTvs"])
    assert key_table == "QuikPlTv"
    factor_segments = {
        (key[0], key[3], key[4], key[5], key[6], key[7], key[8])
        for key in collapsed["QuikTvs"]
    }
    key_segments = {
        (row["PLAN"], row["GENDER"], row["UWCLASS"], row["BAND"],
         row["ISSCNTRY"], row["ISSUEST"], row["EFFDATE"])
        for row in key_rows
    }
    assert factor_segments == key_segments


def test_v05_non_equal_tv_control_retains_matching_uw_keys():
    grids = {
        "QuikTvs": {
            _grid("QuikTvs", "PR", (3.0, 4.0))[0]:
                _grid("QuikTvs", "PR", (3.0, 4.0))[1],
            _grid("QuikTvs", "SM", (3.0, 4.1))[0]:
                _grid("QuikTvs", "SM", (3.0, 4.1))[1],
        }
    }
    collapsed = collapse_equal_uw_families(grids)
    assert {key[4] for key in collapsed["QuikTvs"]} == {"PR", "SM"}


def _emitted_factor(plan, uw, values, family):
    return {
        "PLAN": plan, "AGE": "30", "CNTL": "00", "GENDER": "F",
        "UWCLASS": uw, "BAND": "00", "ISSCNTRY": "0000",
        "ISSUEST": "00", "EFFDATE": "19000101",
        f"{family}0": values[0], f"{family}1": values[1],
    }


def _full_factor(plan, uw, values, family):
    row = {field: "" for field, *_ in S.factor_table_fields(f"Quik{family.title()}s")}
    row.update(_emitted_factor(plan, uw, values, family))
    for i, value in enumerate(values):
        row[f"{family}{i}"] = f".{int(value):02d}"
    return row


def _full_key(plan, uw, key_table):
    row = {field: "" for field, *_ in S.key_table_fields(key_table)}
    row.update({
        "PLAN": plan, "GENDER": "F", "UWCLASS": uw, "BAND": "00",
        "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101",
    })
    return row


def test_final_emit_boundary_collapses_cv_tv_independently():
    factors = {
        "QuikCvs": [
            _emitted_factor("578STR", uw, (1.0, 2.0), "CV")
            for uw in ("00", "PR", "SM")
        ],
        "QuikTvs": [
            _emitted_factor("1658C1", uw, (3.0, 4.0), "TV")
            for uw in ("00", "PR", "SM")
        ],
        "QuikGps": [
            _emitted_factor("578STR", uw, (9.0, 9.5), "GP")
            for uw in ("PR", "SM")
        ],
    }
    keys = {
        "QuikPlCv": [
            {"PLAN": "578STR", "GENDER": "F", "UWCLASS": uw, "BAND": "00",
             "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101"}
            for uw in ("00", "PR", "SM")
        ],
        "QuikPlTv": [
            {"PLAN": "1658C1", "GENDER": "F", "UWCLASS": uw, "BAND": "00",
             "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101"}
            for uw in ("00", "PR", "SM")
        ],
    }

    targets = _finalize_equal_cv_tv_keys(factors, keys)

    assert targets == {
        "QuikCvs": {("578STR", "19000101")},
        "QuikTvs": {("1658C1", "19000101")},
    }
    assert {r["UWCLASS"] for r in factors["QuikCvs"]} == {"00"}
    assert {r["UWCLASS"] for r in factors["QuikTvs"]} == {"00"}
    assert {r["UWCLASS"] for r in factors["QuikGps"]} == {"PR", "SM"}
    assert {r["UWCLASS"] for r in keys["QuikPlCv"]} == {"00"}
    assert {r["UWCLASS"] for r in keys["QuikPlTv"]} == {"00"}


def test_final_emit_boundary_keeps_non_equal_or_missing_grids():
    factors = {
        "QuikCvs": [
            _emitted_factor("1659C2", "PR", (1.0, 2.0), "CV"),
            _emitted_factor("1659C2", "SM", (1.0, 2.1), "CV"),
        ],
        "QuikTvs": [
            _emitted_factor("1659C2", "PR", (3.0, 4.0), "TV"),
        ],
    }
    keys = {
        "QuikPlCv": [
            {"PLAN": "1659C2", "GENDER": "F", "UWCLASS": uw, "BAND": "00",
             "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101"}
            for uw in ("PR", "SM")
        ],
        "QuikPlTv": [],
    }

    assert _finalize_equal_cv_tv_keys(factors, keys) == {}
    assert {r["UWCLASS"] for r in keys["QuikPlCv"]} == {"PR", "SM"}


def test_shared_tv_key_table_preserves_non_equal_np_uw_keys():
    factors = {
        "QuikTvs": [
            _emitted_factor("5CDT10", uw, (3.0, 4.0), "TV")
            for uw in ("00", "PR", "SM")
        ],
        "QuikNps": [
            _emitted_factor("5CDT10", uw, values, "NP")
            for uw, values in (("PR", (5.0, 6.0)), ("SM", (5.0, 6.1)))
        ],
    }
    keys = {
        "QuikPlTv": [
            _full_key("5CDT10", uw, "QuikPlTv")
            for uw in ("00", "PR", "SM")
        ],
    }

    targets = _finalize_equal_cv_tv_keys(factors, keys)

    assert targets == {"QuikTvs": {("5CDT10", "19000101")}}
    assert {r["UWCLASS"] for r in factors["QuikTvs"]} == {"00"}
    assert {r["UWCLASS"] for r in factors["QuikNps"]} == {"PR", "SM"}
    assert {r["UWCLASS"] for r in keys["QuikPlTv"]} == {"00", "PR", "SM"}


def test_final_emit_boundary_does_not_drop_unrelated_plan_family():
    factors = {
        "QuikCvs": [
            _emitted_factor("1658C1", uw, (1.0, 2.0), "CV")
            for uw in ("00", "PR", "SM")
        ] + [
            _emitted_factor("1659C2", uw, values, "CV")
            for uw, values in (("PR", (1.0, 2.0)), ("SM", (1.0, 2.1)))
        ],
    }
    keys = {
        "QuikPlCv": [
            {"PLAN": plan, "GENDER": "F", "UWCLASS": uw, "BAND": "00",
             "ISSCNTRY": "0000", "ISSUEST": "00", "EFFDATE": "19000101"}
            for plan, uws in (
                ("1658C1", ("00", "PR", "SM")),
                ("1659C2", ("PR", "SM")),
            )
            for uw in uws
        ],
    }

    targets = _finalize_equal_cv_tv_keys(factors, keys)

    assert targets == {"QuikCvs": {("1658C1", "19000101")}}
    assert {(r["PLAN"], r["UWCLASS"]) for r in factors["QuikCvs"]} == {
        ("1658C1", "00"),
        ("1659C2", "PR"),
        ("1659C2", "SM"),
    }
    assert {(r["PLAN"], r["UWCLASS"]) for r in keys["QuikPlCv"]} == {
        ("1658C1", "00"),
        ("1659C2", "PR"),
        ("1659C2", "SM"),
    }


def test_final_writer_boundary_uses_full_schema_and_preserves_control_plan():
    factors = {
        "QuikCvs": [
            _full_factor("1658C1", uw, (1, 2), "CV")
            for uw in ("00", "PR", "SM")
        ] + [
            _full_factor("1659C2", uw, values, "CV")
            for uw, values in (("PR", (1, 2)), ("SM", (1, 3)))
        ],
        "QuikTvs": [
            _full_factor("1658C1", uw, (3, 4), "TV")
            for uw in ("00", "PR", "SM")
        ],
    }
    keys = {
        "QuikPlCv": [
            _full_key("1658C1", uw, "QuikPlCv")
            for uw in ("00", "PR", "SM")
        ] + [
            _full_key("1659C2", uw, "QuikPlCv")
            for uw in ("PR", "SM")
        ],
        "QuikPlTv": [
            _full_key("1658C1", uw, "QuikPlTv")
            for uw in ("00", "PR", "SM")
        ],
    }

    targets = _finalize_equal_cv_tv_keys(factors, keys)

    assert targets == {
        "QuikCvs": {("1658C1", "19000101")},
        "QuikTvs": {("1658C1", "19000101")},
    }
    assert {(r["PLAN"], r["UWCLASS"]) for r in factors["QuikCvs"]} == {
        ("1658C1", "00"), ("1659C2", "PR"), ("1659C2", "SM"),
    }
    assert {(r["PLAN"], r["UWCLASS"]) for r in factors["QuikTvs"]} == {
        ("1658C1", "00"),
    }
    assert {(r["PLAN"], r["UWCLASS"]) for r in keys["QuikPlCv"]} == {
        ("1658C1", "00"), ("1659C2", "PR"), ("1659C2", "SM"),
    }
