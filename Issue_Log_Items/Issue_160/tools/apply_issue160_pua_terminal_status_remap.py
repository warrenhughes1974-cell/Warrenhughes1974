"""Issue #160 — scoped remap: PUA MPHSTAT inherits terminal base-phase status.

Reads QLA_Migration/Output/quikridr.csv, updates only PUA-row MPHSTAT when the
base phase is a terminal status (>= 50, not 44/45). Does not touch any other
table or any other column. Base 44/45 -> 54 and base < 50 -> 41 are
regression-guarded (WARNING only; not overwritten).
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RIDR = ROOT / "QLA_Migration" / "Output" / "quikridr.csv"


def _status_int(raw: object) -> int:
    try:
        return int("".join(c for c in str(raw).strip() if c.isdigit()) or "99")
    except ValueError:
        return 99


def _is_phase1(phase: object) -> bool:
    p = str(phase or "").strip()
    if p in ("1", "01", "1.0"):
        return True
    try:
        return int(float(p)) == 1
    except (TypeError, ValueError):
        return False


def _is_pua_row(row: dict) -> bool:
    if _is_phase1(row.get("MPHASE", "")):
        return False
    return str(row.get("MPLAN") or "").strip().upper().endswith("PA")


def main() -> int:
    if not RIDR.is_file():
        print(f"FAIL: missing {RIDR}")
        return 1

    with RIDR.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields:
            print("FAIL: quikridr.csv has no header")
            return 1
        rows = list(reader)

    by_policy: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        by_policy[str(row.get("MPOLICY") or "").strip()].append(i)

    changed = 0
    by_base = Counter()
    samples_by_base: dict[str, list[str]] = defaultdict(list)
    warnings = 0

    for _pol, idxs in by_policy.items():
        base_row = None
        for i in idxs:
            if _is_phase1(rows[i].get("MPHASE", "")):
                base_row = rows[i]
                break
        if base_row is None:
            continue
        base_raw = base_row.get("MPHSTAT", "")
        base_status = _status_int(base_raw)
        for i in idxs:
            row = rows[i]
            if not _is_pua_row(row):
                continue
            pua_raw = row.get("MPHSTAT", "")
            pol = str(row.get("MPOLICY") or "").strip()
            plan = str(row.get("MPLAN") or "").strip()
            if base_status in (44, 45):
                if str(pua_raw).strip() != "54":
                    warnings += 1
                    print(
                        f"WARNING: base 44/45 regression-guard (not overwritten) "
                        f"MPOLICY={pol} MPLAN={plan} base={base_raw!r} "
                        f"PUA_MPHSTAT={pua_raw!r} expected='54'"
                    )
                continue
            if base_status < 50:
                if str(pua_raw).strip() != "41":
                    warnings += 1
                    print(
                        f"WARNING: base <50 regression-guard (not overwritten) "
                        f"MPOLICY={pol} MPLAN={plan} base={base_raw!r} "
                        f"PUA_MPHSTAT={pua_raw!r} expected='41'"
                    )
                continue
            if pua_raw != base_raw:
                row["MPHSTAT"] = base_raw
                changed += 1
                status_key = str(base_status)
                by_base[status_key] += 1
                bucket = samples_by_base[status_key]
                if len(bucket) < 2:
                    bucket.append(
                        f"  MPOLICY={pol} MPLAN={plan} BASE={base_raw} "
                        f"BEFORE={pua_raw} AFTER={base_raw}"
                    )

    with RIDR.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("Issue #160 PUA terminal status remap")
    print(f"rows_read={len(rows)}")
    print(f"PUA rows changed={changed}")
    print("breakdown by base MPHSTAT:")
    for status in sorted(by_base, key=lambda s: int(s) if str(s).isdigit() else 999):
        print(f"  {status}: {by_base[status]}")
    print(f"warnings={warnings}")
    samples = []
    for status in sorted(samples_by_base, key=lambda s: int(s) if str(s).isdigit() else 999):
        samples.extend(samples_by_base[status])
    if samples:
        print("sample changes:")
        for line in samples:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
