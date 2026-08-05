"""Issue #120 — read-only QuikList spot/validator for cut-completeness registry.

Validates existing QLA_Migration/Output/quiklist.csv (does not re-emit).
Exit 0 = PASS / IN_DATA candidate; exit 1 = FAIL.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.quiklist_converter import (  # noqa: E402
    ACTIVE_QUIKLIST_GROUPS,
    QUIKLIST_DEFAULT_MBILLDAY,
    QUIKLIST_DEFAULT_MBILLMODE,
    QUIKLIST_DEFAULT_MLAPSEH,
    QUIKLIST_DEFAULT_MLAPSEL,
    QUIKLIST_DEFAULT_MSTATUS,
    QUIKLIST_DEFAULT_MSORT,
    QUIKLIST_MCOMP,
)
from qla_core.schema_constants import QUIKLIST_SCHEMA  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output" / "quiklist.csv"


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def main() -> int:
    errors: list[str] = []
    if not OUT.is_file():
        print("Issue #120 validation: FAIL")
        print("  - quiklist.csv missing in Output")
        return 1

    df = pd.read_csv(OUT, dtype=str).fillna("")
    if list(df.columns) != list(QUIKLIST_SCHEMA):
        errors.append("CSV column order mismatch vs QUIKLIST_SCHEMA")
    if len(df) != 6:
        errors.append(f"expected 6 rows, got {len(df)}")

    groups = sorted({_norm(v) for v in df.get("MGROUP", pd.Series(dtype=str)).tolist()})
    if groups != sorted(ACTIVE_QUIKLIST_GROUPS):
        errors.append(f"unexpected MGROUP keys: {groups}")

    for _, row in df.iterrows():
        group = _norm(row.get("MGROUP"))
        if _norm(row.get("MCOMP")) != QUIKLIST_MCOMP:
            errors.append(f"{group}: MCOMP mismatch")
        if not _norm(row.get("MBILLNAME")):
            errors.append(f"{group}: MBILLNAME blank")
        if _norm(row.get("MSORT")) != QUIKLIST_DEFAULT_MSORT:
            errors.append(f"{group}: MSORT mismatch")
        for field, expected in (
            ("MLAPSEL", str(QUIKLIST_DEFAULT_MLAPSEL)),
            ("MLAPSEH", str(QUIKLIST_DEFAULT_MLAPSEH)),
            ("MBILLDAY", str(QUIKLIST_DEFAULT_MBILLDAY)),
            ("MBILLMODE", str(QUIKLIST_DEFAULT_MBILLMODE)),
        ):
            if _norm(row.get(field)) != expected:
                errors.append(f"{group}: {field} mismatch")
        if _norm(row.get("MSTATUS")) != QUIKLIST_DEFAULT_MSTATUS:
            errors.append(f"{group}: MSTATUS mismatch")

    if errors:
        print("Issue #120 validation: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Issue #120 validation: PASS")
    print(f"  rows={len(df)} groups={groups}")
    print(f"  path={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
