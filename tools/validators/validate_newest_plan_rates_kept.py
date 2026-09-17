"""Fail-closed smoke: older policy cuts must keep the newest plan/rate package.

When QLA_VALUATION_DATE is older than package_valuation_date in
QLA_Migration/Reports/rates/newest_plan_rate_package.json, every pinned
quikplan / QuikIswl / rates/Quik*.csv file must be byte-identical to that
manifest. A 6/30 rebatch that rebuilds plan setup or rates is a drop.

Same-or-newer valuation: PASS (rebuild allowed). Force the hash check with
QLA_KEEP_NEWEST_PLAN_RATES=1. Disable auto-keep with =0 (Warren only).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.newest_plan_rate_package import (  # noqa: E402
    compare_output_to_manifest,
    keep_newest_required,
    load_manifest,
)
from qla_core.valuation_date import apply_valuation_date_env  # noqa: E402


def main() -> int:
    manifest = load_manifest(ROOT)
    pkg = str(manifest.get("package_valuation_date") or "")
    if not pkg:
        print("FAIL: newest_plan_rate_package.json missing package_valuation_date")
        return 1

    src = ROOT / "QLA_Migration" / "Source"
    try:
        vd, how = apply_valuation_date_env(src)
    except ValueError as exc:
        vd = "".join(c for c in os.environ.get("QLA_VALUATION_DATE", "") if c.isdigit())[:8]
        how = f"env-only ({exc})"
        if not vd:
            print(f"FAIL: cannot resolve valuation date: {exc}")
            return 1

    required = keep_newest_required(vd, pkg)
    print(f"validate_newest_plan_rates_kept: valuation={vd} ({how})")
    print(f"  package_valuation_date={pkg} keep_required={required}")

    if not required:
        print("PASS: same-or-newer cut — keep-newest hash check not required")
        return 0

    errors = compare_output_to_manifest(ROOT)
    if errors:
        print(f"FAIL: newest plan/rate package overwritten ({len(errors)})")
        for e in errors[:20]:
            print(f"  {e}")
        return 1

    n = len(manifest.get("files") or {})
    print(f"PASS: {n} pinned plan/rate files match the newest package ({pkg})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
