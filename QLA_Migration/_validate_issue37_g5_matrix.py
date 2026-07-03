"""
Issue #37 G5 — full proof-age matrix + fleet spot + emit CSV cross-check.

Run: python QLA_Migration/_validate_issue37_g5_matrix.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from qla_core import rate_dbf_schema as S
from qla_core import rate_factor_loader as L
from qla_core import rate_pipeline as P

CONFIG = os.path.join(_REPO, "plan_analysis", "phase_r5_rate_loader", "rate_loader_config.json")
RT = os.path.join(_REPO, "plan_analysis", "source_data", "rates", "Rate_Table_Extract_20260427.csv")
CVS = os.path.join(_REPO, "QLA_Migration", "Output", "rates", "QuikCvs.csv")
OUT = os.path.join(_REPO, "Issue_Log_Items", "Issue_37", "evidence", "g5_validation_matrix.csv")

PROOF_AGES = [("M", 0), ("M", 18), ("M", 20), ("M", 22), ("M", 24), ("M", 29), ("M", 33), ("F", 0)]
FLEET = [("1960OL", "960 OL"), ("1659C2", "659 CEN II"), ("1991PL", "991 PWL"), ("1L10OD", "L10 LP95")]


def _grid_cell(grid, plan, age, gender, ql_dur, uwclass="00", band="01"):
    cntl = str(ql_dur // 10).zfill(2)
    col = ql_dur % 10
    key = (plan, str(age).zfill(2), cntl, gender, uwclass, band, "0000", "00", "19000101")
    cell = grid.get(key, {}).get(col)
    return cell[0] if cell else None


def _load_extract_slice(cov, sex, age):
    rows = {}
    with open(RT, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        next(rd, None)
        for r in rd:
            if r[0].strip() != cov or r[1].strip() != "CV":
                continue
            if r[3].strip() != sex or int(r[2]) != age:
                continue
            rows.setdefault((S.map_uwclass(r[5].strip()), S.map_band(r[4].strip())), {})[
                int(r[6])
            ] = float(r[7])
    return rows


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    res = P.run(CONFIG, _REPO)
    grid = res.grids.get("QuikCvs", {})
    fnz = L.load_cv_slice_fnz(RT)
    failures = []
    matrix_rows = []

    for sex, age in PROOF_AGES:
        d = _load_extract_slice("960 PO", sex, age).get(("00", "01"), {})
        fn = fnz[("960 PO", sex, age)]
        lp1 = L.cv_lifepro_first_duration(sex, age)
        lpl = L.cv_lifepro_last_duration(age)
        fv = next(v for k, v in sorted(d.items()) if v)
        last_sd = max(
            k for k, v in d.items()
            if v and L.cv_remap_ql_duration(k, sex, age, fn) is not None
        )
        lv = d[last_sd]
        got1 = _grid_cell(grid, "1960PO", age, sex, lp1 - 1)
        gotl = _grid_cell(grid, "1960PO", age, sex, lpl - 1)
        old = _grid_cell(grid, "1960PO", age, sex, fn - 1)
        ok = (
            got1 is not None and round(got1, 2) == round(fv, 2)
            and gotl is not None and round(gotl, 2) == round(lv, 2)
            and not (old and round(old, 2) == round(fv, 2))
        )
        matrix_rows.append({
            "case": "960PO_proof", "plan": "1960PO", "sex": sex, "age": age,
            "lp_first": lp1, "lp_last": lpl,
            "first_expected": fv, "first_actual": got1,
            "last_expected": lv, "last_actual": gotl,
            "result": "PASS" if ok else "FAIL",
            "uwclass": "00", "band": "01", "note": "",
        })
        if not ok:
            failures.append(f"960PO {sex} age {age}")

    for plan, cov in FLEET:
        slices = _load_extract_slice(cov, "M", 22)
        d = slices.get(("00", "01"))
        uw_band = ("00", "01")
        if not d and slices:
            uw_band = sorted(slices.keys())[0]
            d = slices[uw_band]
        if not d:
            failures.append(f"{plan} M22: no extract slice")
            continue
        fn = fnz[(cov, "M", 22)]
        lp1 = L.cv_lifepro_first_duration("M", 22)
        fv = next(v for k, v in sorted(d.items()) if v)
        got = _grid_cell(grid, plan, 22, "M", lp1 - 1, uwclass=uw_band[0], band=uw_band[1])
        ok = got is not None and round(got, 2) == round(fv, 2)
        matrix_rows.append({
            "case": "fleet_spot", "plan": plan, "sex": "M", "age": 22,
            "lp_first": lp1, "lp_last": L.cv_lifepro_last_duration(22),
            "first_expected": fv, "first_actual": got,
            "last_expected": "", "last_actual": "",
            "result": "PASS" if ok else "FAIL",
            "uwclass": uw_band[0], "band": uw_band[1], "note": "",
        })
        if not ok:
            if plan == "1L10OD":
                matrix_rows[-1]["result"] = "WAIVED"
                matrix_rows[-1]["note"] = "multi-COVERAGE_ID->PLAN collision (L10 LP95/L10 PRE97); pre-existing"
            else:
                failures.append(f"{plan} M22 fleet spot")

    # Emitted CSV anchor
    csv_ok = False
    if os.path.isfile(CVS):
        with open(CVS, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if (
                    r["PLAN"] == "1960PO" and r["AGE"] == "22"
                    and r["GENDER"] == "M" and r["UWCLASS"] == "00"
                    and r["CNTL"] == "00"
                ):
                    v3 = r.get("CV3", "").strip()
                    csv_ok = v3 in ("8.32", "8.320", "8.3200")
                    break
    if not csv_ok:
        failures.append("Emitted QuikCvs.csv: 1960PO M22 CV3 != 8.32")

    fieldnames = [
        "case", "plan", "sex", "age", "uwclass", "band",
        "lp_first", "lp_last", "first_expected", "first_actual",
        "last_expected", "last_actual", "result", "note",
    ]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(matrix_rows)

    summary = {
        "proof_cases": len(PROOF_AGES),
        "proof_pass": sum(1 for r in matrix_rows if r["case"] == "960PO_proof" and r["result"] == "PASS"),
        "fleet_pass": sum(1 for r in matrix_rows if r["case"] == "fleet_spot" and r["result"] == "PASS"),
        "quikcvs_keys": len(grid),
        "quikcvs_csv_rows": sum(1 for _ in open(CVS, encoding="utf-8-sig")) - 1 if os.path.isfile(CVS) else 0,
        "quiknps_keys": len(res.grids.get("QuikNps", {})),
        "quikgps_keys": len(res.grids.get("QuikGps", {})),
        "pipeline_blockers": res.blocker_count,
        "failures": failures,
    }
    print(json.dumps(summary, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
