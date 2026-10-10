"""Level renewal-period gross premium for 5L0110, 5L0510, and 5L075Y.

The converted QuikGps grid holds one rate for the whole renewal period and steps
only at the renewal date. quikplan VARGP for those plans is 2.

Checks, against QLA_Migration/Output by default:

  (a) quikplan VARGP is 2 for the three plans
  (b) each renewal block is level, and its value is the rate at the block's
      start age (the issue-age row for that age, policy-year index 0)
  (c) every issue age that has a source rate extends past the first renewal
  (d) the gold cells below, matched exactly
  (e) with --baseline DIR (a pre-change Output/rates folder): every other
      plan's QuikGps rows and every other rates file are byte-identical, and
      each new cell equals the baseline attained-age rate at
      a + R * (k // R)

Exits 1 on failure. Not part of the closed-issue smoke list.

Usage:
    python tools/validators/validate_tl10_level_premium.py
    python tools/validators/validate_tl10_level_premium.py --output-dir QLA_Migration/Output
    python tools/validators/validate_tl10_level_premium.py --baseline /path/to/Output/rates
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.level_period_premium import renewal_periods  # noqa: E402
from qla_core.rate_dbf_schema import N_DURATION_COLS, PREFIX  # noqa: E402

DEFAULT_OUTPUT = ROOT / "QLA_Migration" / "Output"
PLANS = ("5L0110", "5L0510", "5L075Y")
GP_PREFIX = PREFIX["QuikGps"]

# Policy year y is index y - 1. Text is the factor cell, exactly.
GOLD = (
    ("5L0110", "F", "PR", 45, 21, 30, "9.00"),
    ("5L0110", "F", "PR", 45, 31, 40, "27.04"),
    ("5L0110", "F", "PR", 45, 41, 41, "82.89"),
    ("5L0110", "M", "PR", 20, 21, 30, "2.38"),
    ("5L0110", "M", "PR", 20, 31, 40, "4.69"),
    ("5L0110", "M", "PR", 20, 41, 41, "10.08"),
    ("5L075Y", "M", "ST", 29, 26, 30, "8.51"),
    ("5L075Y", "M", "ST", 29, 31, 35, "11.86"),
    ("5L075Y", "M", "ST", 29, 36, 36, "17.41"),
)


def _n(value) -> str:
    return ("" if value is None else str(value)).strip()


def _find_csv(directory: Path, name: str) -> Path | None:
    direct = directory / name
    if direct.is_file():
        return direct
    if not directory.is_dir():
        return None
    for child in directory.iterdir():
        if child.is_file() and child.name.lower() == name.lower():
            return child
    return None


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def _sig(row: dict) -> tuple:
    return (
        _n(row.get("GENDER")),
        _n(row.get("UWCLASS")),
        _n(row.get("BAND")),
        _n(row.get("ISSCNTRY")),
        _n(row.get("ISSUEST")),
        _n(row.get("EFFDATE")),
    )


def _page(row: dict) -> int:
    raw = _n(row.get("CNTL")) or "0"
    return int(raw) if raw.isdigit() else 0


def _slices(rows: list[dict], plans: set[str]) -> dict[tuple, dict[int, str]]:
    """(plan, segmentation, issue age) -> {policy-year index: cell text}."""
    out: dict[tuple, dict[int, str]] = {}
    for row in rows:
        plan = _n(row.get("PLAN"))
        if plan not in plans:
            continue
        age_raw = _n(row.get("AGE"))
        if not age_raw.isdigit():
            continue
        cells = out.setdefault((plan, _sig(row), int(age_raw)), {})
        page = _page(row)
        for col in range(N_DURATION_COLS):
            text = _n(row.get(f"{GP_PREFIX}{col}"))
            if text:
                cells[page * N_DURATION_COLS + col] = text
    return out


def _same_rate(left: str, right: str) -> bool:
    if left.strip() == right.strip():
        return True
    try:
        return abs(float(left) - float(right)) < 1e-6
    except ValueError:
        return False


def _check_vargp(quikplan_rows: list[dict], failures: list[str]) -> None:
    by_plan: dict[str, list[str]] = {}
    for row in quikplan_rows:
        plan = _n(row.get("PLAN"))
        if plan in PLANS:
            by_plan.setdefault(plan, []).append(_n(row.get("VARGP")))
    for plan in PLANS:
        got = by_plan.get(plan)
        if not got:
            failures.append(f"(a) {plan} missing from quikplan")
            continue
        if any(value != "2" for value in got):
            failures.append(f"(a) {plan} VARGP={got!r}, expected '2'")


def _check_blocks(slices: dict, periods: dict[str, int], failures: list[str]) -> None:
    present = {key[0] for key in slices}
    for plan in PLANS:
        if plan not in present:
            failures.append(f"(b) {plan} has no QuikGps rows")
    for key, cells in sorted(slices.items(), key=lambda item: str(item[0])):
        plan, _seg, issue_age = key
        period = periods[plan]
        if not cells:
            continue
        max_index = max(cells)
        block = 0
        while block <= max_index:
            indexes = range(block, min(block + period, max_index + 1))
            values = [cells.get(index) for index in indexes]
            present_values = [value for value in values if value]
            if present_values:
                if any(value is None for value in values) or len(set(present_values)) != 1:
                    failures.append(
                        f"(b) {plan} issue age {issue_age} block starting at index {block} "
                        f"is not level: {values}"
                    )
                else:
                    start_age = issue_age + block
                    start_key = (plan, key[1], start_age)
                    if start_key in slices and slices[start_key].get(0) != present_values[0]:
                        failures.append(
                            f"(b) {plan} issue age {issue_age} index {block} is "
                            f"{present_values[0]!r}, rate at start age {start_age} is "
                            f"{slices[start_key].get(0)!r}"
                        )
            block += period
        if 0 in cells and max_index < period:
            failures.append(
                f"(c) {plan} issue age {issue_age} stops at index {max_index}, "
                f"before the renewal at index {period}"
            )


def _check_gold(slices: dict, failures: list[str]) -> None:
    for plan, gender, uwclass, issue_age, year_from, year_to, expected in GOLD:
        matches = [
            cells for (got_plan, seg, age), cells in slices.items()
            if got_plan == plan and age == issue_age and seg[0] == gender and seg[1] == uwclass
        ]
        if not matches:
            failures.append(
                f"(d) missing {plan} {gender} {uwclass} issue age {issue_age}"
            )
            continue
        for cells in matches:
            for year in range(year_from, year_to + 1):
                index = year - 1
                got = cells.get(index)
                if got != expected:
                    failures.append(
                        f"(d) {plan} {gender} {uwclass} issue {issue_age} "
                        f"year {year} (index {index}) is {got!r}, expected {expected!r}"
                    )


def _plan_of_line(line: bytes) -> str:
    body = line.rstrip(b"\r\n")
    if not body:
        return ""
    field = body.split(b",", 1)[0]
    return field.decode("utf-8-sig", errors="replace").strip().strip('"')


def _other_plan_bytes(path: Path, skip: set[str]) -> bytes:
    lines = path.read_bytes().splitlines(keepends=True)
    if not lines:
        return b""
    kept = [lines[0]]
    for line in lines[1:]:
        if _plan_of_line(line) not in skip:
            kept.append(line)
    return b"".join(kept)


def _baseline_slots(rows: list[dict], plans: set[str]) -> dict[tuple, dict[int, str]]:
    """Attained-age slot axis: AGE 00, slot = CNTL*10 + column."""
    slots: dict[tuple, dict[int, str]] = {}
    for row in rows:
        plan = _n(row.get("PLAN"))
        if plan not in plans:
            continue
        bucket = slots.setdefault((plan, _sig(row)), {})
        age = _n(row.get("AGE"))
        page = _page(row)
        for col in range(N_DURATION_COLS):
            text = _n(row.get(f"{GP_PREFIX}{col}"))
            if not text:
                continue
            if age in ("", "00"):
                attained = page * N_DURATION_COLS + col
            elif col == 0 and page == 0 and age.isdigit():
                attained = int(age)
            else:
                continue
            bucket[attained] = text
    return slots


def _check_baseline(rates_dir: Path, baseline_dir: Path, slices: dict, periods: dict, failures: list[str]) -> None:
    if not baseline_dir.is_dir():
        failures.append(f"(e) baseline rates folder not found: {baseline_dir}")
        return
    current_files = {path.name: path for path in rates_dir.iterdir() if path.is_file()}
    baseline_files = {path.name: path for path in baseline_dir.iterdir() if path.is_file()}
    if set(current_files) != set(baseline_files):
        failures.append(
            "(e) rates filenames differ: "
            f"only in output {sorted(set(current_files) - set(baseline_files))}, "
            f"only in baseline {sorted(set(baseline_files) - set(current_files))}"
        )
    skip = set(PLANS)
    for name in sorted(set(current_files) & set(baseline_files)):
        if name.lower() == "quikgps.csv":
            current = _other_plan_bytes(current_files[name], skip)
            previous = _other_plan_bytes(baseline_files[name], skip)
            if current != previous:
                failures.append("(e) QuikGps rows for plans other than the three differ from baseline")
            continue
        if current_files[name].read_bytes() != baseline_files[name].read_bytes():
            failures.append(f"(e) {name} is not byte-identical to baseline")

    base_gps = _find_csv(baseline_dir, "QuikGps.csv")
    if base_gps is None:
        failures.append("(e) baseline QuikGps.csv is missing")
        return
    slots = _baseline_slots(_read_csv(base_gps), skip)
    for (plan, seg, issue_age), cells in slices.items():
        period = periods[plan]
        base = slots.get((plan, seg))
        if base is None:
            failures.append(f"(e) {plan} {seg} has new QuikGps rows and no baseline attained-age grid")
            continue
        for index, text in sorted(cells.items()):
            lookup = issue_age + period * (index // period)
            expected = base.get(lookup)
            if expected is None or not _same_rate(text, expected):
                failures.append(
                    f"(e) {plan} issue {issue_age} index {index} is {text!r}, "
                    f"baseline attained age {lookup} is {expected!r}"
                )


def validate(output_dir: Path, baseline_dir: Path | None = None) -> list[str]:
    failures: list[str] = []
    output_dir = Path(output_dir)
    plan_path = output_dir / "quikplan.csv"
    rates_dir = output_dir / "rates"
    gps_path = _find_csv(rates_dir, "QuikGps.csv")
    if not plan_path.is_file():
        return [f"missing {plan_path}"]
    if gps_path is None:
        return [f"missing {rates_dir / 'QuikGps.csv'}"]

    periods = renewal_periods()
    for plan in PLANS:
        if plan not in periods:
            failures.append(f"{plan} is not in paagerat_pr_level_period")
    if failures:
        return failures

    _check_vargp(_read_csv(plan_path), failures)
    slices = _slices(_read_csv(gps_path), set(PLANS))
    _check_blocks(slices, periods, failures)
    _check_gold(slices, failures)
    if baseline_dir is not None:
        _check_baseline(rates_dir, Path(baseline_dir), slices, periods, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate level renewal-period gross premium")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--baseline", type=Path, default=None,
                        help="Pre-change Output/rates folder")
    args = parser.parse_args(argv)
    failures = validate(args.output_dir, args.baseline)
    print("Level renewal-period gross premium")
    print(f"  output: {args.output_dir}")
    if args.baseline is not None:
        print(f"  baseline: {args.baseline}")
    if failures:
        print("RESULT: FAIL")
        for failure in failures[:40]:
            print(f"  - {failure}")
        if len(failures) > 40:
            print(f"  ... {len(failures) - 40} more")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
