"""
Publish modified QLA output tables to Output/Test_Validation for partial UAT reload.

After an issue fix, copy only the quik*.csv tables that changed so the operator
can reload QLAdmin without running a full batch.

Usage:
  python tools/publish_test_validation.py quikmstr quikridr
  python tools/publish_test_validation.py --clean --issue Issue_80 quikplan
  python tools/publish_test_validation.py --clean --issue Issue_80 --rates QuikPlCv QuikPlTv quikplan
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"


def clean_dest(dest_dir: Path) -> None:
    """Remove all files under Test_Validation (partial UAT folder must stay minimal)."""
    if not dest_dir.is_dir():
        return
    for p in sorted(dest_dir.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            p.rmdir()


def publish_tables(
    table_names: list[str],
    *,
    output_dir: Path = DEFAULT_OUTPUT,
    dest_dir: Path = TEST_VALIDATION,
    issue_tag: str = "",
    rate_tables: list[str] | None = None,
    clean: bool = False,
) -> Path:
    if clean:
        clean_dest(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in table_names:
        stem = name.strip().lower().removesuffix(".csv")
        src = output_dir / f"{stem}.csv"
        if not src.is_file():
            raise FileNotFoundError(f"Missing output table: {src}")
        shutil.copy2(src, dest_dir / f"{stem}.csv")
        copied.append(stem)

    rate_copied: list[str] = []
    rates_src = output_dir / "rates"
    rates_dest = dest_dir / "rates"
    for name in rate_tables or []:
        stem = name.strip().removesuffix(".csv")
        src = rates_src / f"{stem}.csv"
        if not src.is_file():
            raise FileNotFoundError(f"Missing rate table: {src}")
        rates_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, rates_dest / f"{stem}.csv")
        rate_copied.append(f"rates/{stem}.csv")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    manifest = dest_dir / "manifest.txt"
    lines = [
        f"Published: {stamp}",
        f"Issue: {issue_tag or '(unspecified)'}",
        f"Source: {output_dir}",
        "Tables:",
    ]
    lines.extend(f"  - {t}.csv" for t in copied)
    lines.extend(f"  - {t}" for t in rate_copied)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish modified tables to Test_Validation")
    ap.add_argument("tables", nargs="*", help="Table stems, e.g. quikmstr quikridr")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--dest-dir", type=Path, default=TEST_VALIDATION)
    ap.add_argument("--issue", default="", help="Issue tag for manifest, e.g. Issue_49")
    ap.add_argument(
        "--manifest",
        type=Path,
        help="Text file with one table stem per line (comments with #)",
    )
    ap.add_argument(
        "--rates",
        nargs="*",
        default=None,
        metavar="TABLE",
        help="Rate key/factor stems copied from Output/rates/ into Test_Validation/rates/",
    )
    ap.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing Test_Validation contents before publish",
    )
    args = ap.parse_args()

    tables = list(args.tables)
    if args.manifest:
        for line in args.manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                tables.append(line.split()[0])

    if not tables and not args.rates:
        ap.error("Provide table names, --rates, or --manifest")

    dest = publish_tables(
        tables,
        output_dir=args.output_dir,
        dest_dir=args.dest_dir,
        issue_tag=args.issue,
        rate_tables=args.rates,
        clean=args.clean,
    )
    total = len(tables) + len(args.rates or [])
    print(f"Published {total} table(s) to {dest}")
    for t in tables:
        stem = t.strip().lower().removesuffix(".csv")
        print(f"  {stem}.csv")
    for t in args.rates or []:
        stem = t.strip().removesuffix(".csv")
        print(f"  rates/{stem}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
