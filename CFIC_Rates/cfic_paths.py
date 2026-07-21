"""Canonical CFIC folder paths (standalone — not Warren QLA_Migration)."""
from __future__ import annotations

from pathlib import Path

CFIC_ROOT = Path(__file__).resolve().parent

# QLAdmin load package — table CSVs only (PascalCase Quik*.csv)
# Note: on Windows this may resolve to CFIC_Rates/output/rates (case-insensitive).
OUTPUT_RATES = CFIC_ROOT / "Output" / "rates"

# Non-load artifacts
REPORTS = CFIC_ROOT / "Reports"
VALIDATION = CFIC_ROOT / "Validation"
LOGS = CFIC_ROOT / "Logs"
ARCHIVE = CFIC_ROOT / "Archive"

# Pipeline staging (not handoff)
STAGING_RESERVE = CFIC_ROOT / "extracted_reserve" / "staging"
STAGING_PDF = CFIC_ROOT / "extracted_pdf_rates" / "staging"

# Deprecated draft emit location (pre-Output policy)
LEGACY_OUTPUT_RATES = CFIC_ROOT / "output" / "rates"

# Source DBFs
RESERVE_DBF = CFIC_ROOT / "docs" / "cifi0007.DBF"
PLANS_DBF = CFIC_ROOT / "docs" / "cifi0004.dbf"
CROSSWALK_XLSX = CFIC_ROOT / "Citizens_Plan_Crosswak.xlsx"

ASSUMPTIONS_CSV = (
    CFIC_ROOT / "Issue_Log" / "CFIC_Issue_03" / "business_inputs" / "cfic_rate_key_assumptions.csv"
)

# Tables allowed in Output/rates (CSV load package)
LOAD_PACKAGE_TABLES = frozenset({
    "QuikGps", "QuikCvs", "QuikDbs", "QuikDvs", "QuikNps", "QuikTvs",
    "QuikPlGp", "QuikPlCv", "QuikPlDb", "QuikPlDv", "QuikPlTv",
    "QuikPlGd", "QuikPlUw", "QuikPlBd", "QuikPlSt", "QuikPlNb",
})
