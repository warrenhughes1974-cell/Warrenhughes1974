"""DG-QUIKDATE-001 — PAC Bill Date Must Equal Prior Month End."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKDATE_001
from data_governance.config.settings import QUIKDATE_PAC_BILL_FIELD
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.rules.processing_date_integrity.bill_date_rule import (
    run_prior_month_end_bill_date_rule,
)


def run_dg_quikdate_001(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
):
    return run_prior_month_end_bill_date_rule(
        store,
        rule=RULE_DG_QUIKDATE_001,
        source_field=QUIKDATE_PAC_BILL_FIELD,
        business_label="PAC Bill",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
