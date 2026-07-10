"""
Publish modified QLA output tables to Output/Test_Validation for partial UAT reload.

After an issue fix, copy only the quik*.csv tables that changed so the operator
can reload QLAdmin without running a full batch.

Usage:
  python tools/publish_test_validation.py quikmstr quikridr
  python tools/publish_test_validation.py --manifest Issue_Log_Items/Issue_49/evidence/issue49_tables.txt
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"


def publish_tables(
    table_names: list[str],
    *,
    output_dir: Path = DEFAULT_OUTPUT,
    dest_dir: Path = TEST_VALIDATION,
    issue_tag: str = "",
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in table_names:
        stem = name.strip().lower().removesuffix(".csv")
        src = output_dir / f"{stem}.csv"
        if not src.is_file():
            raise FileNotFoundError(f"Missing output table: {src}")
        shutil.copy2(src, dest_dir / f"{stem}.csv")
        copied.append(stem)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    manifest = dest_dir / "manifest.txt"
    lines = [
        f"Published: {stamp}",
        f"Issue: {issue_tag or '(unspecified)'}",
        f"Source: {output_dir}",
        "Tables:",
    ]
    lines.extend(f"  - {t}.csv" for t in copied)
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
    args = ap.parse_args()

    tables = list(args.tables)
    if args.manifest:
        for line in args.manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                tables.append(line.split()[0])

    if not tables:
        ap.error("Provide table names or --manifest")

    dest = publish_tables(
        tables,
        output_dir=args.output_dir,
        dest_dir=args.dest_dir,
        issue_tag=args.issue,
    )
    print(f"Published {len(tables)} table(s) to {dest}")
    for t in tables:
        stem = t.strip().lower().removesuffix(".csv")
        print(f"  {stem}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
