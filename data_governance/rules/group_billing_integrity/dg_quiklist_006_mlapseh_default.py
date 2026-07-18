"""DG-QUIKLIST-006 — MLAPSEH Must Equal 0.

Uses field name MLAPSEH (not the misspelling MLASPEH).
"""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_006
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.group_billing_integrity.default_value_rule import (
    run_numeric_zero_default_rule,
)

# Explicit constant — do not use MLASPEH
MLAPSEH_FIELD = "MLAPSEH"


def run_dg_quiklist_006(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_numeric_zero_default_rule(
        store,
        rule=RULE_DG_QUIKLIST_006,
        source_field=MLAPSEH_FIELD,
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
