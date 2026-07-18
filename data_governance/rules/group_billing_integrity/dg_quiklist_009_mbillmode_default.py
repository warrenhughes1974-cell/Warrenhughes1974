"""DG-QUIKLIST-009 — MBILLMODE Must Equal 0."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_009
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.group_billing_integrity.default_value_rule import (
    run_numeric_zero_default_rule,
)


def run_dg_quiklist_009(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_numeric_zero_default_rule(
        store,
        rule=RULE_DG_QUIKLIST_009,
        source_field="MBILLMODE",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
