"""Issue #86 — validate full QuikDate rebuild emit."""
from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_governance.data_access.normalization import prior_month_end
from qla_core.quikdate_converter import (
    QUIKDATE_DEFAULT_ACHFILEID,
    QUIKDATE_DEFAULT_ACHFILEID2,
    QUIKDATE_DEFAULT_PDUEDAYS,
    QUIKDATE_DEFAULT_UPDATENUM,
    QUIKDATE_DEFAULT_VERSION,
    QUIKDATE_PME_DATE_FIELDS,
    QUIKDATE_SCHEMA,
    build_quikdate_governance_row,
    emit_quikdate_csv,
    format_qla_date,
)

OUT = ROOT / "QLA_Migration" / "Output"
TEST_VAL = OUT / "Test_Validation"
RUN_DATE = date(2026, 7, 19)


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def main() -> int:
    errors: list[str] = []
    expected_pme = format_qla_date(prior_month_end(RUN_DATE))
    row = build_quikdate_governance_row(RUN_DATE)

    if list(row.keys()) != QUIKDATE_SCHEMA:
        errors.append("schema field order mismatch")

    for field in QUIKDATE_PME_DATE_FIELDS:
        if _norm(row[field]) != expected_pme:
            errors.append(f"{field} expected {expected_pme}, got {row[field]!r}")

    if _norm(row["ESC_DATE"]) != "":
        errors.append("ESC_DATE must be blank")

    if int(row["PDUEDAYS"]) != QUIKDATE_DEFAULT_PDUEDAYS:
        errors.append(f"PDUEDAYS expected {QUIKDATE_DEFAULT_PDUEDAYS}")
    if _norm(row["VERSION"]) != QUIKDATE_DEFAULT_VERSION:
        errors.append(f"VERSION expected {QUIKDATE_DEFAULT_VERSION}")
    if int(row["UPDATENUM"]) != QUIKDATE_DEFAULT_UPDATENUM:
        errors.append(f"UPDATENUM expected {QUIKDATE_DEFAULT_UPDATENUM}")
    if int(row["ACHFILEID"]) != QUIKDATE_DEFAULT_ACHFILEID:
        errors.append(f"ACHFILEID expected {QUIKDATE_DEFAULT_ACHFILEID}")
    if _norm(row["ACHFILEID2"]) != QUIKDATE_DEFAULT_ACHFILEID2:
        errors.append(f"ACHFILEID2 expected {QUIKDATE_DEFAULT_ACHFILEID2}")

    info = emit_quikdate_csv(str(OUT), conversion_run_date=RUN_DATE)
    out_path = Path(info["path"])
    if not out_path.is_file():
        errors.append(f"missing emit file: {out_path}")

    df = pd.read_csv(out_path, dtype=str).fillna("")
    if len(df) != 1:
        errors.append(f"expected 1 row, got {len(df)}")
    if list(df.columns) != QUIKDATE_SCHEMA:
        errors.append("CSV column order mismatch")

    csv_row = df.iloc[0].to_dict()
    for field in QUIKDATE_SCHEMA:
        if _norm(csv_row.get(field)) != _norm(row[field]):
            errors.append(f"CSV {field} mismatch: {csv_row.get(field)!r} vs {row[field]!r}")

    if errors:
        print("Issue #86 validation: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    TEST_VAL.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, TEST_VAL / "quikdate.csv")
    print("Issue #86 validation: PASS")
    print(f"  run_date={RUN_DATE.isoformat()} prior_month_end={expected_pme}")
    print(f"  emit={out_path}")
    print(f"  test_validation={TEST_VAL / 'quikdate.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
