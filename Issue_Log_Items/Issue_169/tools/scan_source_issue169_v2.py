"""Issue #169 discovery v2: enumerate every distinct COVERAGE_ID variant in the
newest (8/31) LifePRO rate extracts whose text contains 960 / 619 / 667 / 1595 /
1596 / SAL ADB, with per-variant TYPE_CODE breakdown and nonzero VALUE1 counts.

This avoids guessing the exact PLAN_ID token shape (the first run showed
COVERAGE_ID can be a compound like "619 DT" or "667 ART 95" with no separate
sequence-number prefix, so exact single-token matching under-counted).

Read-only.
"""
from __future__ import annotations

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, "QLA_Migration", "Source")

FILES = {
    "PDAGE_20260831": ("PDAGE_AgeDuration_Rates_Extract_20260831.csv", {"type": 1, "uw": 5, "val1": 7}),
    "PAAGE_20260831": ("PAAGE_AttainedAge_Rates_Extract_20260831.csv", {"type": 1, "uw": 4, "val1": 7}),
    "PAAGERAT_20260831": ("PAAGERAT_AttainedAge_Rates_Extract_20260831.csv", {"type": 1, "uw": 4, "val1": 7}),
}

NEEDLES = re.compile(r"\b(960|619|667|1595|1596)\b|SAL\s*ADB", re.I)


def scan(label: str, path: str, cols: dict) -> dict:
    variants = collections.Counter()
    type_by_variant = collections.defaultdict(collections.Counter)
    nonzero_by_variant_type = collections.defaultdict(collections.Counter)
    total = 0
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        fh.readline()
        fh.readline()
        for line in fh:
            total += 1
            cov = line.split(",", 1)[0]
            covs = cov.strip()
            if not NEEDLES.search(covs):
                continue
            variants[covs] += 1
            parts = line.split(",")
            tcode = parts[cols["type"]].strip() if len(parts) > cols["type"] else "?"
            type_by_variant[covs][tcode] += 1
            try:
                v1 = float(parts[cols["val1"]].strip() or 0)
            except (ValueError, IndexError):
                v1 = 0.0
            if v1 != 0.0:
                nonzero_by_variant_type[covs][tcode] += 1

    print("=" * 90)
    print(f"{label}  ({total:,} rows scanned)")
    print("=" * 90)
    if not variants:
        print("  NO COVERAGE_ID VARIANTS MATCHED")
    for cov in sorted(variants):
        tb = type_by_variant[cov]
        nz = nonzero_by_variant_type[cov]
        detail = ", ".join(f"{t}:{n}(nz={nz.get(t,0)})" for t, n in sorted(tb.items()))
        print(f"  [{cov!r:<16}] rows={variants[cov]:>6}  {detail}")
    print()
    return variants


def main() -> int:
    for label, (fn, cols) in FILES.items():
        path = os.path.join(SRC, fn)
        if not os.path.isfile(path):
            print(f"MISSING: {path}")
            continue
        scan(label, path, cols)
    return 0


if __name__ == "__main__":
    sys.exit(main())
