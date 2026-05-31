"""
R5 rate loader DRY RUN — exercises the full qla_core rate pipeline end-to-end and reports
what WOULD be emitted, WITHOUT writing any DBF. Read-only with respect to all inputs.

  transform (+ audited AGE>99 cap) -> pivot to factor grid -> materialize factor rows
  (CHAR(7) formatter) -> derive QuikPlxx rate keys (externalized assumptions) -> validate.

Outputs (this folder):
  dryrun_summary.json          counts, validation summary, AGE-cap audit, family/plan breakdown
  dryrun_validation_issues.csv all issues (BLOCKER/WARNING) with id + detail
  age_cap_audit.csv            PLAN, TYPE_CODE, ORIGINAL_AGE, EMITTED_AGE, ROW_COUNT

No production DBFs are emitted (per R5 direction). Run:
  python plan_analysis/phase_r5_rate_loader/rate_loader_dryrun.py
"""
import os, sys, json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from qla_core import rate_pipeline as P

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONFIG = os.path.join(HERE, "rate_loader_config.example.json")


def main():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    res = P.run(CONFIG, ROOT)
    summary = P.build_summary(res, "R5 rate loader DRY RUN (no DBFs emitted)",
                              cfg["source_rate_extract"],
                              extra={"emit_note": "DBFs intentionally NOT emitted in R5 dry run."})
    P.write_issue_reports(res, HERE)
    json.dump(summary, open(os.path.join(HERE, "dryrun_summary.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
