"""Issue #168 — fail-closed: 1L14SC reserve/value rows exist at NT/PQ/PR/ST.

LifePRO's L14 reserve does not vary by underwriting class. After the
output-apply, each reserve/value table must carry identical factor/option
rows at all four classes. Premium (QuikGps) must stay class-varying and
untouched.

Usage:
  python tools/validators/validate_issue168_l14_reserve_class_replication.py
  python tools/validators/validate_issue168_l14_reserve_class_replication.py --output-dir QLA_Migration/Output

Exit 1 on any failure.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "QLA_Migration" / "Output"

PLAN = "1L14SC"
CLASSES = ("NT", "PQ", "PR", "ST")
KEY_COLS = ("AGE", "CNTL", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")
FACTOR_RE = re.compile(r"^(TV|NP|CV|NFF|GP)\d+$")

TABLES = {
    "QuikTvs.csv": 332,
    "QuikNps.csv": 328,
    "QuikCvs.csv": 332,
    "QuikNff.csv": 324,
    "QuikPlTv.csv": 2,
    "QuikPlCv.csv": 2,
    "QuikPlDb.csv": 2,
    "QuikPlDv.csv": 2,
}

# QuikGps already carried all four classes before #168 and must not change.
QUIKGPS_FLOOR = 68
QUIKGPS_GOLDS = (
    # PLAN AGE CNTL GENDER UWCLASS field expected
    ("00", "04", "F", "NT", "GP5", "21.12"),
    ("00", "04", "F", "PQ", "GP5", "15.24"),
    ("00", "04", "F", "NT", "GP6", "22.08"),
    ("00", "04", "F", "PQ", "GP6", "15.96"),
)


def _zeroish(value: str) -> bool:
    s = (value or "").strip()
    if not s:
        return True
    try:
        return float(s) == 0.0
    except ValueError:
        return False


def _row_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple((row.get(c) or "").strip() for c in KEY_COLS)


def _value_fields(row: dict[str, str]) -> tuple[str, ...]:
    skip = {"PLAN", "UWCLASS", *KEY_COLS}
    items = []
    for col in row:
        if col in skip:
            continue
        items.append(f"{col}={(row.get(col) or '')}")
    return tuple(items)


def _factor_strip(row: dict[str, str]) -> list[str]:
    return [(row.get(c) or "") for c in row if FACTOR_RE.match(c)]


def _read_plan_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("PLAN") or "").strip() != PLAN:
                continue
            rows.append({(k or "").strip(): (v or "") for k, v in row.items()})
    return rows


def validate(output_dir: Path) -> int:
    rates = output_dir / "rates"
    errors: list[str] = []

    print("=" * 72)
    print("ISSUE #168 L14 1L14SC reserve class-key replication")
    print(f"Output: {output_dir}")
    print("=" * 72)

    for filename, expected in TABLES.items():
        path = rates / filename
        if not path.is_file():
            errors.append(f"missing {path}")
            continue
        rows = _read_plan_rows(path)
        by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_class[(row.get("UWCLASS") or "").strip()].append(row)

        counts = {cls: len(by_class.get(cls, [])) for cls in CLASSES}
        print(f"  {filename}: " + " ".join(f"{c}={counts[c]}" for c in CLASSES))
        if len(set(counts.values())) != 1 or counts["NT"] != expected:
            errors.append(
                f"{filename}: class counts {counts} expected {expected} each"
            )
            continue

        by_key: dict[tuple[str, ...], dict[str, dict[str, str]]] = defaultdict(dict)
        for cls in CLASSES:
            for row in by_class[cls]:
                by_key[_row_key(row)][cls] = row

        mismatch = 0
        blank_copy = 0
        for key, class_rows in by_key.items():
            missing = [c for c in CLASSES if c not in class_rows]
            if missing:
                mismatch += 1
                if mismatch <= 5:
                    errors.append(f"{filename}: key {key} missing {missing}")
                continue
            nt = class_rows["NT"]
            nt_vals = _value_fields(nt)
            for cls in ("PQ", "PR", "ST"):
                if _value_fields(class_rows[cls]) != nt_vals:
                    mismatch += 1
                    if mismatch <= 5:
                        errors.append(
                            f"{filename}: values differ NT vs {cls} at {key}"
                        )
            nt_factors = _factor_strip(nt)
            if nt_factors and not all(_zeroish(v) for v in nt_factors):
                for cls in ("PQ", "PR", "ST"):
                    copy_factors = _factor_strip(class_rows[cls])
                    if not copy_factors or all(_zeroish(v) for v in copy_factors):
                        blank_copy += 1
                        if blank_copy <= 5:
                            errors.append(
                                f"{filename}: {cls} factor strip blank/zero "
                                f"where NT has values at {key}"
                            )
        if mismatch > 5:
            errors.append(f"{filename}: {mismatch} class-key mismatches (first 5 shown)")
        if blank_copy > 5:
            errors.append(f"{filename}: {blank_copy} blank/zero copy strips (first 5 shown)")

    gps_path = rates / "QuikGps.csv"
    if not gps_path.is_file():
        errors.append(f"missing {gps_path}")
    else:
        gps = _read_plan_rows(gps_path)
        gps_n = len(gps)
        gps_classes = {((r.get("UWCLASS") or "").strip()) for r in gps}
        print(f"  QuikGps.csv: 1L14SC rows={gps_n} classes={sorted(gps_classes)}")
        if gps_n < QUIKGPS_FLOOR:
            errors.append(f"QuikGps 1L14SC count={gps_n} below floor {QUIKGPS_FLOOR}")
        if gps_classes != set(CLASSES):
            errors.append(f"QuikGps 1L14SC classes={sorted(gps_classes)} expected {list(CLASSES)}")
        for age, cntl, gender, uw, field, expected in QUIKGPS_GOLDS:
            hit = None
            for row in gps:
                if (
                    (row.get("AGE") or "").strip() == age
                    and (row.get("CNTL") or "").strip() == cntl
                    and (row.get("GENDER") or "").strip() == gender
                    and (row.get("UWCLASS") or "").strip() == uw
                ):
                    hit = (row.get(field) or "").strip()
                    break
            if hit != expected:
                errors.append(
                    f"QuikGps gold {gender}/{uw} AGE={age} CNTL={cntl} "
                    f"{field}={hit!r} expected {expected!r}"
                )
            else:
                print(f"  OK QuikGps {gender}/{uw} AGE={age} CNTL={cntl} {field}={hit}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  {e}")
        return 1

    print("PASS: 1L14SC reserve/value rows identical at NT/PQ/PR/ST; QuikGps unchanged.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #168 L14 class-key replication")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    return validate(args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
