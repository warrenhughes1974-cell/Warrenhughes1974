#!/usr/bin/env python3
"""Wrapper — canonical Issue 141 validator lives under QLA_Migration/."""
from __future__ import annotations

import runpy
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "QLA_Migration" / "_validate_issue141_resrvcat.py"

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
