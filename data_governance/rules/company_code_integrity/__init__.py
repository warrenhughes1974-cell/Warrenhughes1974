"""Data Governance Item 1 — QuikComp Company Code Integrity."""

from data_governance.rules.company_code_integrity.dg_quikcomp_001_unique_company_code import (
    run_dg_quikcomp_001,
)
from data_governance.rules.company_code_integrity.dg_quikcomp_002_agent_company_code_must_exist import (
    run_dg_quikcomp_002,
)
from data_governance.rules.company_code_integrity.dg_quikcomp_003_policy_company_code_must_exist import (
    run_dg_quikcomp_003,
)

__all__ = [
    "run_dg_quikcomp_001",
    "run_dg_quikcomp_002",
    "run_dg_quikcomp_003",
]
