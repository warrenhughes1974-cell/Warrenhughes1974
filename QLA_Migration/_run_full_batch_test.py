"""Deprecated location — moved to `tools/batch_tests/run_full_batch_test.py`.

Run the new path directly, or invoke this stub for backward compatibility.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_TARGET = _REPO / 'tools/batch_tests/run_full_batch_test.py'


if __name__ == "__main__":
    cmd = [sys.executable, str(_TARGET), *sys.argv[1:]]
    raise SystemExit(subprocess.call(cmd))
