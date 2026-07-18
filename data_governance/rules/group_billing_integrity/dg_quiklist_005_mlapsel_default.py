"""DG-QUIKLIST-005 — MLAPSEL Must Equal 0."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_005
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.group_billing_integrity.default_value_rule import (
    run_numeric_zero_default_rule,
)


def run_dg_quiklist_005(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_numeric_zero_default_rule(
        store,
        rule=RULE_DG_QUIKLIST_005,
        source_field="MLAPSEL",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
