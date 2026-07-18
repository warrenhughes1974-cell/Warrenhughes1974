"""
Apply Issue #80 quikplan overlay (CSO crosswalk then Valuation_Setup) to Output/quikplan.csv.

Headless helper when full batch is not run; mirrors app.py quikplan enrichment order.
Audit/backup artifacts go to QLA_Migration/Reports and Archive — never Output root.
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from qla_core.cso_mortality_crosswalk import (
    apply_quikplan_cv_assumptions,
    default_crosswalk_path,
    load_cso_mortality_crosswalk,
)
from qla_core.cso_valuation_setup import (
    apply_quikplan_valuation_setup,
    default_valuation_setup_path,
    load_valuation_setup,
)

OUT = ROOT / "QLA_Migration" / "Output"
QUIKPLAN = OUT / "quikplan.csv"
REPORTS = ROOT / "QLA_Migration" / "Reports"
ARCHIVE = ROOT / "QLA_Migration" / "Archive"


def main() -> int:
    if not QUIKPLAN.is_file():
        print(f"FAIL: {QUIKPLAN} not found")
        return 1

    df = pd.read_csv(QUIKPLAN, dtype=str).fillna("")
    repo = str(ROOT)

    cso = load_cso_mortality_crosswalk(default_crosswalk_path(repo))
    if cso.plans_loaded:
        cso_qa = apply_quikplan_cv_assumptions(df, cso, log=print)
    else:
        cso_qa = {"applied": False}

    vs = load_valuation_setup(default_valuation_setup_path(repo))
    if vs.plans_loaded:
        vs_qa = apply_quikplan_valuation_setup(df, vs, log=print)
    else:
        vs_qa = {"applied": False}
        print("WARN: Valuation_Setup not loaded")

    REPORTS.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = ARCHIVE / f"quikplan_pre_issue80_{stamp}.csv"
    shutil.copy2(QUIKPLAN, backup)
    df.to_csv(QUIKPLAN, index=False, quoting=csv.QUOTE_MINIMAL)

    qa_path = REPORTS / "issue80_quikplan_overlay_qa.csv"
    with qa_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage", "metric", "value"])
        for k, v in cso_qa.items():
            if k != "diffs":
                w.writerow(["cso_crosswalk", k, v])
        for k, v in vs_qa.items():
            if k != "diffs":
                w.writerow(["valuation_setup", k, v])

    print(f"OK: wrote {QUIKPLAN}")
    print(f"Backup: {backup}")
    print(f"QA: {qa_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
