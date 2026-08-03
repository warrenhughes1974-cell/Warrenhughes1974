#!/usr/bin/env python3
"""A11h Validation helper — re-enrich quikplan against rates and gold-check 1658C1."""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

from qla_core.quikplan_rate_variation_flags import (
    VARY_FIELD_NAMES,
    RateVariationEnrichmentConfig,
    integrate_quikplan_file,
)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"


def main() -> int:
    src_rates = OUT / "rates"
    if not (src_rates / "QuikGps.csv").is_file():
        src_rates = TV / "rates"
    plan_path = OUT / "quikplan.csv"
    if not plan_path.is_file():
        plan_path = TV / "quikplan.csv"
    if not plan_path.is_file():
        print("FAIL: no quikplan.csv")
        return 2
    if not (src_rates / "QuikGps.csv").is_file():
        print("FAIL: no rates")
        return 3

    bak = plan_path.with_suffix(".csv.pre_a11h")
    shutil.copy2(plan_path, bak)
    print("backup", bak)
    print("plan", plan_path)
    print("rates", src_rates)

    cfg = RateVariationEnrichmentConfig.from_env_and_defaults(str(ROOT))
    cfg.emitted_csv_dir = str(src_rates)
    result = integrate_quikplan_file(
        str(plan_path),
        config=cfg,
        repo_root=str(ROOT),
        write_back=True,
        write_audit=True,
    )
    print("blockers", result.validation_blockers)
    fails = [c for c in result.validation_checks if c["STATUS"] != "PASS"]
    for c in fails[:20]:
        print("CHECK_FAIL", c["CHECK_NAME"], c["DETAILS"])

    # Publish / sync
    TV.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan_path, TV / "quikplan.csv")
    if plan_path != OUT / "quikplan.csv":
        (OUT).mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan_path, OUT / "quikplan.csv")

    gold = None
    with plan_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if (row.get("PLAN") or "").strip().upper() == "1658C1":
            gold = row
            break
    if not gold:
        print("FAIL: 1658C1 missing")
        return 4

    print("--- 1658C1 ---")
    for k in ["PLANVALOPT", "PAR"] + list(VARY_FIELD_NAMES):
        print(f"{k}={gold.get(k, '')}")

    errors = []
    for f in VARY_FIELD_NAMES:
        if f.startswith("BDVARY") and (gold.get(f) or "").strip().upper() == "Y":
            errors.append(f"Band still Y: {f}")
        if f.startswith("STVARY") and (gold.get(f) or "").strip().upper() == "Y":
            errors.append(f"State still Y: {f}")
        if f.endswith("DV") and (gold.get(f) or "").strip().upper() == "Y":
            errors.append(f"DV still Y: {f}")
        if f.endswith("DB") and (gold.get(f) or "").strip().upper() == "Y":
            errors.append(f"DB still Y: {f}")
    if (gold.get("GDVARYGP") or "").strip().upper() != "Y":
        errors.append("expected GDVARYGP=Y")
    if (gold.get("UWVARYGP") or "").strip().upper() != "Y":
        errors.append("expected UWVARYGP=Y")

    bd = st = dv = 0
    for row in rows:
        if any((row.get(f) or "").strip().upper() == "Y" for f in VARY_FIELD_NAMES if f.startswith("BDVARY")):
            bd += 1
        if any((row.get(f) or "").strip().upper() == "Y" for f in VARY_FIELD_NAMES if f.startswith("STVARY")):
            st += 1
        if any((row.get(f) or "").strip().upper() == "Y" for f in VARY_FIELD_NAMES if f.endswith("DV")):
            dv += 1
    print(f"fleet plans={len(rows)} with_BDVARY={bd} with_STVARY={st} with_DV_VARY={dv}")

    if errors or result.validation_blockers:
        print("A11H_VALIDATE FAIL", errors)
        return 5
    print("A11H_VALIDATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
