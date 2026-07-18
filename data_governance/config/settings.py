"""Configuration defaults for QLAdmin Data Governance."""

from __future__ import annotations

import os
from dataclasses import dataclass

# User-facing reports (run folder root)
WHAT_WAS_CHECKED_HTML = "1_What_Was_Checked.html"
ITEMS_NEEDING_ATTENTION_CSV = "2_Items_Needing_Attention.csv"

# Internal technical artifacts (under run folder / internal/)
INTERNAL_SUBDIR = "internal"
RESULTS_CSV_NAME = "data_governance_results.csv"
FINDINGS_CSV_NAME = "data_governance_findings.csv"
SUMMARY_CSV_NAME = "data_governance_summary.csv"
REPORT_MD_NAME = "data_governance_report.md"
VALIDATION_GUIDE_NAME = "data_governance_validation_guide.md"
VALIDATION_MANIFEST_NAME = "data_governance_validation_manifest.json"
RUN_SUMMARY_JSON_NAME = "data_governance_run.json"
RUN_LOG_NAME = "data_governance.log"

# Logical QLAdmin table names
TABLE_QUIKCOMP = "QuikComp"
TABLE_QUIKAGTS = "QuikAgts"
TABLE_QUIKMSTR = "QuikMstr"
TABLE_QUIKACTG = "QuikActg"
TABLE_QUIKCHRT = "QuikChrt"
TABLE_QUIKLIST = "QuikList"
TABLE_QUIKDATE = "QuikDate"
TABLE_QUIKPLCV = "QuikPlCv"
TABLE_QUIKPLTV = "QuikPlTv"
TABLE_QUIKPLGP = "QuikPlGp"
TABLE_QUIKPLDB = "QuikPlDb"
TABLE_QUIKPLDV = "QuikPlDv"
TABLE_QUIKQXS = "QuikQxs"
TABLE_QUIKPLAN = "QuikPlan"
TABLE_QUIKPLGD = "QuikPlGd"
TABLE_QUIKPLUW = "QuikPlUw"
TABLE_QUIKPLBD = "QuikPlBd"  # verified band table (QuikPlVd not present in CSO)

# File stem candidates (case-insensitive match in data region)
TABLE_FILE_STEMS = {
    TABLE_QUIKCOMP: ("quikcomp",),
    TABLE_QUIKAGTS: ("quikagts",),
    TABLE_QUIKMSTR: ("quikmstr",),
    TABLE_QUIKACTG: ("quikactg",),
    TABLE_QUIKCHRT: ("quikchrt",),
    TABLE_QUIKLIST: ("quiklist",),
    TABLE_QUIKDATE: ("quikdate",),
    TABLE_QUIKPLCV: ("quikplcv",),
    TABLE_QUIKPLTV: ("quikpltv",),
    TABLE_QUIKPLGP: ("quikplgp",),
    TABLE_QUIKPLDB: ("quikpldb",),
    TABLE_QUIKPLDV: ("quikpldv",),
    TABLE_QUIKQXS: ("quikqxs",),
    TABLE_QUIKPLAN: ("quikplan",),
    TABLE_QUIKPLGD: ("quikplgd",),
    TABLE_QUIKPLUW: ("quikpluw",),
    TABLE_QUIKPLBD: ("quikplbd",),
}

# Plan-value source tables evaluated by DG-PLANVALUES
PLANVALUE_SOURCE_TABLES = (
    TABLE_QUIKPLCV,
    TABLE_QUIKPLTV,
    TABLE_QUIKPLGP,
    TABLE_QUIKPLDB,
    TABLE_QUIKPLDV,
)

# Verified QuikDate physical fields (see docs/QuikDate_Schema_Verification.md)
QUIKDATE_PAC_BILL_FIELD = "PACBILL"
QUIKDATE_DIRECT_BILL_FIELD = "DIRBILL"
QUIKDATE_REINSURANCE_BILL_FIELD = "REINBILL"
QUIKDATE_ACHFILEID_FIELD = "ACHFILEID"
QUIKDATE_ACHFILEID2_FIELD = "ACHFILEID2"
# Business label ESCDATE → physical ESC_DATE
QUIKDATE_ESCDATE_FIELD = "ESC_DATE"

# Verified QuikActg physical fields (from QUIKACTG.DBF schema inspection)
# Company code: MCOMP CHARACTER(1)
# Row / assignment key companion: MPLAN CHARACTER(6)
# Note: QuikActg has no single MACCOUNT column. Account numbers are stored as
# values in event-assignment columns (MACCTREC, MPREM1ST, …). QuikChrt uses
# MCOMP + MACCOUNT CHARACTER(10) for the chart of accounts.
QUIKACTG_COMPANY_FIELD = "MCOMP"
QUIKACTG_PLAN_FIELD = "MPLAN"
QUIKACTG_COMPANY_FIELD_TYPE = "C"
QUIKACTG_COMPANY_FIELD_LENGTH = 1
QUIKACTG_PLAN_FIELD_TYPE = "C"
QUIKACTG_PLAN_FIELD_LENGTH = 6

POLICY_NUMBER_MIN_LENGTH = 4
POLICY_NUMBER_MAX_LENGTH = 11


@dataclass(frozen=True)
class GovernancePaths:
    """Paths for one isolated governance run folder."""

    data_dir: str
    output_dir: str  # run-specific folder: <output_base>/<run_id>/

    @property
    def what_was_checked_html(self) -> str:
        return os.path.join(self.output_dir, WHAT_WAS_CHECKED_HTML)

    @property
    def items_needing_attention_csv(self) -> str:
        return os.path.join(self.output_dir, ITEMS_NEEDING_ATTENTION_CSV)

    @property
    def internal_dir(self) -> str:
        return os.path.join(self.output_dir, INTERNAL_SUBDIR)

    @property
    def results_csv(self) -> str:
        return os.path.join(self.internal_dir, RESULTS_CSV_NAME)

    @property
    def findings_csv(self) -> str:
        return os.path.join(self.internal_dir, FINDINGS_CSV_NAME)

    @property
    def summary_csv(self) -> str:
        return os.path.join(self.internal_dir, SUMMARY_CSV_NAME)

    @property
    def report_md(self) -> str:
        return os.path.join(self.internal_dir, REPORT_MD_NAME)

    @property
    def validation_guide(self) -> str:
        return os.path.join(self.internal_dir, VALIDATION_GUIDE_NAME)

    @property
    def validation_manifest(self) -> str:
        return os.path.join(self.internal_dir, VALIDATION_MANIFEST_NAME)

    @property
    def run_summary_json(self) -> str:
        return os.path.join(self.internal_dir, RUN_SUMMARY_JSON_NAME)

    @property
    def run_log(self) -> str:
        return os.path.join(self.internal_dir, RUN_LOG_NAME)


def default_output_base(repo_root: str | None = None) -> str:
    """Default output base under QLA_Migration/Reports/data_governance."""
    if repo_root is None:
        repo_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.normpath(
        os.path.join(repo_root, "QLA_Migration", "Reports", "data_governance")
    )


def resolve_output_base(explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return os.path.normpath(explicit.strip())
    env = os.environ.get("QLA_GOVERNANCE_OUTPUT_DIR", "").strip()
    if env:
        return os.path.normpath(env)
    return default_output_base()


def resolve_data_dir(explicit: str | None = None) -> str | None:
    """Resolve data-region path from argument or environment (may be None)."""
    if explicit and explicit.strip():
        return os.path.normpath(explicit.strip())
    env = os.environ.get("QLA_GOVERNANCE_DATA_DIR", "").strip()
    if env:
        return os.path.normpath(env)
    return None


# Backward-compatible aliases
default_output_dir = default_output_base
resolve_output_dir = resolve_output_base
