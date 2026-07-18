"""QLAdmin Data Governance framework.

Incremental, testable post-load governance checks for QLAdmin tables.
First governance item: DG-QUIKCOMP — QuikComp Company Code Integrity.
"""

from data_governance.execution.runner import run_data_governance
from data_governance.models.findings import (
    GovernanceFinding,
    GovernanceRunResult,
    RuleExecutionResult,
)

__all__ = [
    "run_data_governance",
    "GovernanceFinding",
    "GovernanceRunResult",
    "RuleExecutionResult",
]
