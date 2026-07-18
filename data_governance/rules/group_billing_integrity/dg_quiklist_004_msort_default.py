"""DG-QUIKLIST-004 — MSORT Must Equal N."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_004
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.group_billing_integrity.default_value_rule import (
    run_character_default_rule,
)


def run_dg_quiklist_004(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_character_default_rule(
        store,
        rule=RULE_DG_QUIKLIST_004,
        source_field="MSORT",
        expected="N",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
