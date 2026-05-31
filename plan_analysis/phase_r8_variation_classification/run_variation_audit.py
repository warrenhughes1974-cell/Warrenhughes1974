"""
Phase R8 — Variation Classification audit runner (read-only by default).

Usage:
  python plan_analysis/phase_r8_variation_classification/run_variation_audit.py

Outputs:
  variation_code_audit.csv
  variation_code_audit_summary.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from qla_core.variation_classification import (
    VariationClassificationConfig,
    run_classification,
)

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIT_CSV = os.path.join(HERE, "variation_code_audit.csv")


def main():
    cfg = VariationClassificationConfig.from_env_and_defaults(ROOT)
    rows, summary = run_classification(cfg, AUDIT_CSV)
    print(json.dumps({
        "audit_csv": os.path.relpath(AUDIT_CSV, ROOT),
        "auto_apply_enabled": cfg.auto_apply_variation_codes,
        **summary,
    }, indent=2))
    # Sample rows for key plans
    for plan in ("920ADB", "5L01MA", "7687J3"):
        match = [r for r in rows if r["PLAN"] == plan]
        if match:
            r = match[0]
            print(f"SAMPLE {plan}: VARGP={r['Recommended_VARGP']} VARDB={r['Recommended_VARDB']} "
                  f"structure={r['Detected_Structure']} confidence={r['Confidence']}")


if __name__ == "__main__":
    main()
