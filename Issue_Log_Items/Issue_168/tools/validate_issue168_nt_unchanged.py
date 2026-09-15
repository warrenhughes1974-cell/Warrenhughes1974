"""Compare current 1L14SC NT rows to the pre-apply archive. Read-only."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "QLA_Migration" / "Archive" / "issue168_l14_20260915_010022"
CURRENT = ROOT / "QLA_Migration" / "Output" / "rates"
PLAN = "1L14SC"

TABLES = [
    "QuikTvs.csv",
    "QuikNps.csv",
    "QuikCvs.csv",
    "QuikNff.csv",
    "QuikPlTv.csv",
    "QuikPlCv.csv",
    "QuikPlDb.csv",
    "QuikPlDv.csv",
]


def nt_lines(path: Path) -> list[str]:
    out = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        header = fh.readline()
        cols = header.strip().split(",")
        try:
            plan_i = cols.index("PLAN")
            uw_i = cols.index("UWCLASS")
        except ValueError:
            return []
        for line in fh:
            parts = line.rstrip("\r\n").split(",")
            if len(parts) <= max(plan_i, uw_i):
                continue
            if parts[plan_i].strip() == PLAN and parts[uw_i].strip() == "NT":
                out.append(line.rstrip("\r\n"))
    return out


def main() -> int:
    if not ARCHIVE.is_dir():
        print(f"FAIL: archive missing {ARCHIVE}")
        return 1
    failed = 0
    for name in TABLES:
        before = nt_lines(ARCHIVE / name)
        after = nt_lines(CURRENT / name)
        if before != after:
            print(f"FAIL {name}: NT rows changed ({len(before)} -> {len(after)})")
            failed += 1
        else:
            print(f"OK   {name}: NT rows unchanged ({len(after)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
