"""Thin wrapper — Issue #54 QuikBenh loan history validation."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validators" / "validate_issue54_quikbenh_loan_history.py"


def main() -> int:
    cmd = [sys.executable, str(VALIDATOR), *sys.argv[1:]]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
