"""DG-QUIKDATE-003 — Reinsurance Bill Date Must Equal Prior Month End."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKDATE_003
from data_governance.config.settings import QUIKDATE_REINSURANCE_BILL_FIELD
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.processing_date_integrity.bill_date_rule import (
    run_prior_month_end_bill_date_rule,
)


def run_dg_quikdate_003(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_prior_month_end_bill_date_rule(
        store,
        rule=RULE_DG_QUIKDATE_003,
        source_field=QUIKDATE_REINSURANCE_BILL_FIELD,
        business_label="Reinsurance Bill",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
