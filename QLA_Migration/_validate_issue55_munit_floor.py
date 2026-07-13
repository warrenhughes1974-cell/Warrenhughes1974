"""Thin wrapper — Issue #55 MUNIT floor validation (see tools/validators/validate_issue55_munit_floor.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validators" / "validate_issue55_munit_floor.py"


def main() -> int:
    cmd = [sys.executable, str(VALIDATOR), *sys.argv[1:]]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
