"""Issue #42 Validation Agent companion checks (read-only)."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\warren\Documents\GitHub\Warrenhughes1974")
sys.path.insert(0, str(ROOT))

from qla_core import plan_source_paths as PSP
from qla_core import rate_dbf_schema as S


def main():
    print("=== Path resolve ===")
    print("rate_table:", PSP.rate_table_extract())
    print("paagerat:", PSP.paagerat_extract())
    print("pdage:", PSP.pdage_extract())

    cfg = json.loads(
        (ROOT / "plan_analysis/phase_r5_rate_loader/rate_loader_config.json").read_text(
            encoding="utf-8"
        )
    )
    i42 = cfg.get("issue42_pdage_missfill") or {}
    print("config paagerat:", cfg.get("paagerat_pr_extract"))
    print("config i42 enabled:", i42.get("enabled"))
    print("config i42 pdage:", i42.get("pdage_extract"))

    app_txt = (ROOT / "app.py").read_text(encoding="utf-8", errors="replace")
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', app_txt)
    print("APP_VERSION:", m.group(1) if m else "?")

    pd = ROOT / "QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260713.csv"
    print("=== Sample L01 10Y NP mappable rows ===")
    n = 0
    with open(pd, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            r = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            if r.get("COVERAGE_ID") != "L01 10Y" or r.get("TYPE_CODE") != "NP":
                continue
            if S.map_sex(r.get("SEX")) and S.map_uwclass(r.get("UWCLS")) and S.map_band(
                r.get("BAND")
            ):
                print(
                    r.get("AGE"),
                    r.get("SEX"),
                    r.get("BAND"),
                    r.get("UWCLS"),
                    r.get("DURATION"),
                    r.get("VALUE1"),
                )
                n += 1
                if n >= 3:
                    break

    print("=== Residual CV still absent in PDAGE ===")
    for cov, typ in [("L17", "CV"), ("960 LP85-8", "CV")]:
        c = 0
        with open(pd, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if (row.get("COVERAGE_ID") or "").strip() == cov and (
                    row.get("TYPE_CODE") or ""
                ).strip() == typ:
                    c += 1
        print(f"{cov} {typ}={c}")

    # Sample cell: L01 10Y NP F/1/S age 51 dur 2 should be 16.42 from earlier scan
    print("=== Anchor L01 10Y NP F band1 S age51 dur2 ===")
    with open(pd, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            r = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            if (
                r.get("COVERAGE_ID") == "L01 10Y"
                and r.get("TYPE_CODE") == "NP"
                and r.get("SEX") == "F"
                and r.get("BAND") == "1"
                and r.get("UWCLS") == "S"
                and r.get("AGE") == "51"
                and r.get("DURATION") == "2"
            ):
                print("VALUE1=", r.get("VALUE1"))
                break

    # Pipeline evidence
    focus = ROOT / "Issue_Log_Items/Issue_42/evidence/issue42_focus_plan_counts.csv"
    print("=== Focus evidence ===")
    if focus.is_file():
        with open(focus, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                print(
                    row["coverage_id"],
                    row["type_code"],
                    "->",
                    row["expected_plan"],
                    row["table"],
                    "keys=",
                    row["grid_keys"],
                    row["status"],
                )

    st = ROOT / "QLA_Migration/Staging/rate_table_pdage_missfill_merged.csv"
    print("staging exists:", st.is_file(), "bytes:", st.stat().st_size if st.is_file() else 0)

    # Confirm policy tables untouched by this issue (no Output rates yet; note)
    rates = ROOT / "QLA_Migration/Output/rates"
    print("Output/rates exists:", rates.is_dir())
    if rates.is_dir():
        print("rate files:", sorted(p.name for p in rates.glob("Quik*.csv")))


if __name__ == "__main__":
    main()
