"""
CLNT-RJ — client IDs must be trimmed, numeric→zero decimals, left-padded to 12.

Checks Output quikclnt / quikclid / quikbenf / quikmstr / quikridr client-ID fields.
Fails on left-justified (no leading space) non-blank IDs shorter than 12, or
values that do not match format_qladmin_mclientid().

Usage:
  python tools/validators/validate_client_id_width12.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import (  # noqa: E402
    CLIENT_ID_TARGET_FIELDS,
    QLADMIN_MCLIENTID_WIDTH,
    format_qladmin_mclientid,
)

OUT = ROOT / "QLA_Migration" / "Output"
TABLES = (
    "quikclnt.csv",
    "quikclid.csv",
    "quikbenf.csv",
    "quikmstr.csv",
    "quikridr.csv",
)


def main() -> int:
    if QLADMIN_MCLIENTID_WIDTH != 12:
        print(f"FAIL: QLADMIN_MCLIENTID_WIDTH={QLADMIN_MCLIENTID_WIDTH} expected 12")
        return 1

    errors: list[str] = []
    checked = 0
    for name in TABLES:
        path = OUT / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        # csv.reader — pandas read_csv dtype=str still strips leading spaces on
        # numeric-looking IDs (e.g. '      314894' becomes '  314894').
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            rd = csv.DictReader(f)
            if not rd.fieldnames:
                errors.append(f"{name}: empty header")
                continue
            cols = {c.strip().upper(): c for c in rd.fieldnames if c}
            field_map = {field: cols[field] for field in CLIENT_ID_TARGET_FIELDS if field in cols}
            for idx, row in enumerate(rd):
                for field, src in field_map.items():
                    raw = row.get(src) or ""
                    if not str(raw).strip():
                        continue
                    checked += 1
                    expected = format_qladmin_mclientid(raw)
                    if raw != expected:
                        if len(errors) < 12:
                            errors.append(
                                f"{name}.{field} row{idx}: got {raw!r} expected {expected!r}"
                            )
                        else:
                            errors.append("…")
                            print(
                                f"FAIL: client-ID width-12 — {len(errors)}+ mismatches "
                                f"(checked {checked})"
                            )
                            for e in errors[:12]:
                                print(" ", e)
                            return 1

    if errors:
        print(f"FAIL: client-ID width-12 — {len(errors)} issues (checked {checked})")
        for e in errors[:20]:
            print(" ", e)
        return 1

    print(
        f"PASS: client-ID width-12 — {checked} non-blank values match "
        f"format_qladmin_mclientid (width={QLADMIN_MCLIENTID_WIDTH}) on {', '.join(TABLES)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
