"""Extract Citizens Plans table (cifi0004.dbf) to staging CSV."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cfic_dbf_reader import load_dbf  # noqa: E402

ROOT = SCRIPT_DIR.parents[2]
PLANS_DBF = ROOT / "docs" / "cifi0004.dbf"
OUT_DIR = ROOT / "extracted_plans" / "staging"

FIELDS = [
    "pl_plan",
    "pl_desc",
    "pl_type",
    "pl_class",
    "pl_valunit",
    "pl_form",
    "adfee_amt",
    "payfee_amt",
    "ir1_date",
    "ir1_value",
    "ir2_date",
    "ir2_value",
    "ir3_date",
    "ir3_value",
    "ir4_date",
    "ir4_value",
    "ir5_date",
    "ir5_value",
    "ir6_date",
    "ir6_value",
    "ir7_date",
    "ir7_value",
    "ir8_date",
    "ir8_value",
    "source_file",
]

DBF_TO_STAGING = {
    "PL_PLAN": "pl_plan",
    "PL_DESC": "pl_desc",
    "PL_TYPE": "pl_type",
    "PL_CLASS": "pl_class",
    "PL_VALUNIT": "pl_valunit",
    "PL_FORM": "pl_form",
    "ADFEE_AMT": "adfee_amt",
    "PAYFEE_AMT": "payfee_amt",
    "IR1_DATE": "ir1_date",
    "IR1_VALUE": "ir1_value",
    "IR2_DATE": "ir2_date",
    "IR2_VALUE": "ir2_value",
    "IR3_DATE": "ir3_date",
    "IR3_VALUE": "ir3_value",
    "IR4_DATE": "ir4_date",
    "IR4_VALUE": "ir4_value",
    "IR5_DATE": "ir5_date",
    "IR5_VALUE": "ir5_value",
    "IR6_DATE": "ir6_date",
    "IR6_VALUE": "ir6_value",
    "IR7_DATE": "ir7_date",
    "IR7_VALUE": "ir7_value",
    "IR8_DATE": "ir8_date",
    "IR8_VALUE": "ir8_value",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbf", default=str(PLANS_DBF))
    args = parser.parse_args()
    path = Path(args.dbf)
    if not path.exists():
        raise SystemExit(f"Plans DBF not found: {path}")

    _, rows = load_dbf(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "plans_master.csv"
    staging_rows = []
    for row in rows:
        rec = {dst: row.get(src, "").strip() for src, dst in DBF_TO_STAGING.items()}
        rec["source_file"] = path.name
        staging_rows.append(rec)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(staging_rows)

    print(f"Wrote {len(staging_rows)} plan rows -> {out_path}")


if __name__ == "__main__":
    main()
