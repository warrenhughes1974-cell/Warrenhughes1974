"""Emit QLAdmin rate CSVs — delegates to package_cfic_rates publisher."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CFIC_ROOT = Path(__file__).resolve().parents[3]
PACKAGE = CFIC_ROOT / "scripts" / "package_cfic_rates.py"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit CFIC reserve rates to Output/rates/ (use package_cfic_rates.py directly)"
    )
    parser.add_argument("--plans", default="P7MN")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    cmd = [sys.executable, str(PACKAGE), "--wave", "reserve", "--plans", args.plans, "--clean-legacy"]
    if args.extract:
        cmd.append("--extract")
    if args.validate:
        cmd.append("--validate")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
